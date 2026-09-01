from enum import Enum


class MediaType(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    VOICE = "voice"
