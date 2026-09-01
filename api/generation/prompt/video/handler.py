from api.generation.prompt.video.model import (
    MotionGraphicsPromptComponents,
    MusicVideoPromptComponents,
    PromptComponents,
    UGCPromptComponents,
    VideoType,
)


class VideoPromptHandler:
    @staticmethod
    def compile(video_type: str, fields: dict) -> str:
        prompt = PromptComponents.create(VideoType(video_type), **fields)
        if isinstance(prompt, MusicVideoPromptComponents):
            return VideoPromptHandler._compile_music_video(prompt)
        if isinstance(prompt, MotionGraphicsPromptComponents):
            return VideoPromptHandler._compile_motion_graphics(prompt)
        if isinstance(prompt, UGCPromptComponents):
            return VideoPromptHandler._compile_dialogue_driven(prompt)
        return VideoPromptHandler._compile_cinematic(prompt)

    @staticmethod
    def _compile_cinematic(prompt: PromptComponents) -> str:
        return (
            f"A {prompt.subject}, {prompt.action}, in {prompt.scene}. "
            f"{prompt.camera}. {prompt.lighting}. {prompt.style}."
        )

    @staticmethod
    def _compile_dialogue_driven(prompt: UGCPromptComponents) -> str:
        sentences = [
            f"A {prompt.subject}, {prompt.action}, in {prompt.scene}.",
            f"{prompt.camera}.",
            f"{prompt.lighting}.",
            f"{prompt.style}.",
        ]
        if prompt.dialogue:
            sentences.append(f'Saying: "{prompt.dialogue}"')
        return " ".join(sentences)

    @staticmethod
    def _compile_music_video(prompt: MusicVideoPromptComponents) -> str:
        sentences = [
            f"A {prompt.subject}, {prompt.action}, in {prompt.scene}.",
            f"{prompt.camera}.",
            f"{prompt.lighting}.",
            f"{prompt.style}.",
            "Synced to the rhythm of the reference track.",
        ]
        if prompt.tempo_bpm:
            sentences.append(f"{prompt.tempo_bpm} BPM.")
        return " ".join(sentences)

    @staticmethod
    def _compile_motion_graphics(prompt: MotionGraphicsPromptComponents) -> str:
        sentences = [f"{prompt.style} motion graphics showing {prompt.subject}, {prompt.action}."]
        if prompt.text_content:
            sentences.append(f'On-screen text: "{prompt.text_content}".')
        if prompt.transitions:
            sentences.append(f"{prompt.transitions} transitions.")
        return " ".join(sentences)
