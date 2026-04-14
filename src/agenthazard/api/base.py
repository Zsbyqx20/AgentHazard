import asyncio
import base64
import io
import os
from abc import ABC
from collections.abc import Callable
from typing import Literal, TypeVar, cast

import aiohttp
import structlog
from dotenv import load_dotenv
from PIL import Image

from .models import Message, Usage

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
    ADDITIONAL_HEADERS = None

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
        self.BASE_URL = self.BASE_URL.removesuffix("/")

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
                        raise RuntimeError(
                            f"API Request Failed: {response.status} - {error_text}"
                        )

                except (TimeoutError, aiohttp.ClientError) as e:
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
                        raise RuntimeError(
                            f"API Request Failed after {max_retries + 1} attempts: {e}"
                        ) from e

    def payload(
        self,
        model: str | None = None,
        messages: list[Message] | None = None,
        **kwargs,
    ):
        return PayloadWrapper(
            self,
            model=model,
            messages=messages,
            **kwargs,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class PayloadWrapper:
    def __init__(
        self,
        client: AsyncClient,
        model: str | None = None,
        messages: list[Message] | list[dict] | None = None,
        **kwargs,
    ):
        self._client = client
        self._model = model
        self._messages = cast(list[Message], [])
        if isinstance(messages, list):
            for m in messages:
                if isinstance(m, dict):
                    self._messages.append(Message.model_validate(m))
                elif isinstance(m, Message):
                    self._messages.append(m)
                else:
                    raise TypeError(f"Invalid message: {m}")
        else:
            self._messages = cast(list[Message], [])
        self._kwargs = kwargs

    async def post(
        self,
        timeout: int = 60,
        max_retries: int = 10,
        retry_delay: float = 1.0,
        callback: Callable[[tuple[str, Usage]], T] = post_callback,
        **kwargs,
    ) -> T:
        messages = [m.model_dump(by_alias=True) for m in self._messages]
        logger.debug(
            "Posting payload",
            model=self._model,
            messages=[m.as_str() for m in self._messages],
            **kwargs,
        )
        return await self._client.post(
            payload={
                "model": self._model,
                "messages": messages,
                **self._kwargs,
            },
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            callback=callback,
            **kwargs,
        )

    def text(
        self,
        text: list[str] | str,
        role: Literal["user", "assistant", "system"] = "user",
    ):
        if isinstance(text, str):
            text = [text]

        if self._messages and self._messages[-1].role == role:
            # If last message has same role, append to its content
            for t in text:
                self._messages[-1].add_text(t)
        else:
            # Create new message
            msg = Message(role=role, content=[])
            for t in text:
                msg.add_text(t)
            self._messages.append(msg)

        return self

    def image(
        self,
        image_url: str | Image.Image,
        detail: Literal["low", "high", "auto"] = "auto",
        role: Literal["user", "assistant", "system"] = "user",
    ):
        if isinstance(image_url, Image.Image):
            buffered = io.BytesIO()
            image_url.save(buffered, format="PNG")
            image_data = buffered.getvalue()
            url = f"data:image/png;base64,{base64.b64encode(image_data).decode()}"
        else:
            url = image_url

        if self._messages and self._messages[-1].role == role:
            # If last message has same role, append to its content
            self._messages[-1].add_image(url, detail)
        else:
            # Create new message
            msg = Message(role=role, content=[])
            msg.add_image(url, detail)
            self._messages.append(msg)
        return self

    def model(self, model: str):
        self._model = model
        return self

    def update(self, **kwargs):
        self._kwargs.update(kwargs)
        return self
