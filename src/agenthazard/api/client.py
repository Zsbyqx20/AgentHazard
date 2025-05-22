import os

from .base import AsyncClient


class OpenAIAsyncClient(AsyncClient):
    NAME = "OpenAI"
    BASE_URL = "https://api.openai.com/v1"


class ArkAsyncClient(AsyncClient):
    NAME = "ARK"
    BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"


class QwenVLAsyncClient(AsyncClient):
    NAME = "Qwen"
    BASE_URL = "http://localhost:8000/v1"


class AzureOpenAIAsyncClient(AsyncClient):
    NAME = "Azure"
    BASE_URL = "https://api.openai.com/v1"
    ENDPOINT = ""

    def _before_init(self):
        self.ADDITIONAL_HEADERS = {"api-key": os.getenv("AZURE_API_KEY")}

    def _get_endpoint_url(self, endpoint: str) -> str:
        return self.BASE_URL
