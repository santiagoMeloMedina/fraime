from api.generation.media_type import MediaType
from api.generation.prompt.image.handler import ImagePromptHandler
from api.generation.prompt.video.handler import VideoPromptHandler


class PromptHandler:
    @staticmethod
    def compile(media_type: MediaType, fields: dict, video_type: str | None = None) -> str:
        if media_type == MediaType.IMAGE:
            return ImagePromptHandler.compile(fields)

        if video_type is None:
            raise ValueError("video_type is required when media_type is MediaType.VIDEO")
        return VideoPromptHandler.compile(video_type, fields)
