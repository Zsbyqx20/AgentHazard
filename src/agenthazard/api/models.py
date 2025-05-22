from typing import Literal

from pydantic import BaseModel, Field


class TextMessage(BaseModel):
    type_: Literal["text"] = Field(alias="type")
    text: str


class ImageUrl(BaseModel):
    url: str
    detail: Literal["low", "high", "auto"]


class ImageMessage(BaseModel):
    type_: Literal["image_url"] = Field(alias="type")
    image_url: ImageUrl


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: list[TextMessage | ImageMessage]

    def add_text(self, text: str):
        self.content.append(TextMessage(text=text, type="text"))

    def add_image(
        self,
        image_url: str,
        detail: Literal["low", "high", "auto"] = "auto",
    ):
        self.content.append(
            ImageMessage(
                image_url=ImageUrl(url=image_url, detail=detail),
                type="image_url",
            )
        )

    def as_str(self) -> str:
        content_parts = []
        for item in self.content:
            if isinstance(item, TextMessage):
                content_parts.append(f"Text({item.text})")
            elif isinstance(item, ImageMessage):
                url = item.image_url.url
                truncated_url = url[:15] + "..." + url[-5:] if len(url) > 30 else url
                content_parts.append(
                    f"Image({truncated_url}, detail={item.image_url.detail})"
                )

        content_str = ", ".join(content_parts)
        return f"Message(role: {self.role}, content: [{content_str}])"


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
