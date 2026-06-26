from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ImageResult:
    image_url: str
    seed: int
    model: str
    latency_ms: int


class BaseImageService(ABC):
    @abstractmethod
    def text2img(self, prompt: str, negative_prompt: str = "",
                  width: int = 512, height: int = 768, **kwargs) -> ImageResult:
        ...

    @abstractmethod
    def img2img(self, init_image_url: str, prompt: str, **kwargs) -> ImageResult:
        ...
