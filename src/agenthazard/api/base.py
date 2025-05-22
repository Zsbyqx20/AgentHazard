import asyncio
import os
from abc import ABC
from typing import Callable, TypeVar

import aiohttp
import structlog
from dotenv import load_dotenv

from .models import Usage

logger = structlog.get_logger(__name__)
T = TypeVar("T")


def post_callback(x: tuple[str, Usage], **kwargs) -> tuple[str, dict]:
    return (x[0], kwargs)


class AsyncClient(ABC):
    NAME = ""
    BASE_URL = ""
    AUTH_HEADER_NAME = "Authorization"
    AUTH_HEADER_PREFIX = "Bearer"
    ENDPOINT = "/chat/completions"
    ADDITIONAL_HEADERS = {}

    def __init__(self, base_url: str | None = None, max_concurrent: int = 10):
        load_dotenv()
        self._before_init()
        self.api_key = os.environ.get(f"{self.NAME.upper()}_API_KEY")
        if not self.api_key:
            raise ValueError("API_KEY is not set")

        if base_url:
            self.BASE_URL = base_url
        else:
            base_url_env = os.getenv(f"{self.NAME.upper()}_BASE_URL")
            if base_url_env:
                self.BASE_URL = base_url_env
        if self.BASE_URL.endswith("/"):
            self.BASE_URL = self.BASE_URL[:-1]

        self.headers = self._get_header(self.ADDITIONAL_HEADERS)
        self.session = None
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._post_init()

    def _before_init(self):
        pass

    def _post_init(self):
        pass

    def _get_header(self, additional_headers: dict | None = None):
        headers = {
            self.AUTH_HEADER_NAME: f"{self.AUTH_HEADER_PREFIX} {self.api_key}",
            "Content-Type": "application/json",
        }
        if additional_headers:
            headers.update(additional_headers)
        return headers

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session

    async def close(self) -> None:
        if self.session:
            await self.session.close()

    def _get_endpoint_url(self, endpoint: str) -> str:
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint

        return f"{self.BASE_URL}{endpoint}"

    def _default_callback(self, x: dict):
        message = str(x["choices"][0]["message"]["content"])
        usage = Usage.model_validate(x["usage"])
        return message, usage

    async def post(
        self,
        payload: dict,
        timeout: int = 60,
        max_retries: int = 10,
        retry_delay: float = 1.0,
        callback: Callable[[tuple[str, Usage]], T] = post_callback,
        **kwargs,
    ) -> T:
        session = await self._get_session()

        async with self._semaphore:
            retries = 0
            while True:
                try:
                    async with session.post(
                        self._get_endpoint_url(self.ENDPOINT),
                        headers=self.headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=timeout),
                    ) as response:
                        if response.status == 200:
                            logger.debug(
                                "Request successful",
                                status=response.status,
                                response=await response.json(),
                                **kwargs,
                            )
                            return callback(
                                self._default_callback(await response.json()),
                                **kwargs,
                            )

                        if (
                            response.status in (429, 500, 502, 503, 504)
                            and retries < max_retries
                        ):
                            error_text = await response.text()
                            logger.warning(
                                "Request failed, retrying",
                                status=response.status,
                                error=error_text,
                                attempt=retries + 1,
                                max_attempts=max_retries + 1,
                                **kwargs,
                            )
                            retries += 1
                            current_delay = retry_delay * (2 ** (retries - 1))
                            await asyncio.sleep(current_delay)
                            continue

                        error_text = await response.text()
                        raise Exception(
                            f"API Request Failed: {response.status} - {error_text}"
                        )

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if retries < max_retries:
                        logger.warning(
                            "Network error, retrying",
                            error=str(e),
                            attempt=retries + 1,
                            max_attempts=max_retries + 1,
                            **kwargs,
                        )
                        retries += 1
                        current_delay = retry_delay * (2 ** (retries - 1))
                        await asyncio.sleep(current_delay)
                        continue
                    else:
                        logger.error(
                            "Request failed, reached max retries",
                            error=str(e),
                            **kwargs,
                        )
                        return callback(
                            self._default_callback({
                                "choices": [
                                    {
                                        "message": {
                                            "content": "Request failed, reached max retries"
                                        }
                                    }
                                ]
                            }),
                            **kwargs,
                        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
