from api.generation.prompt.image.model import ImagePromptComponents


class ImagePromptHandler:
    @staticmethod
    def compile(fields: dict) -> str:
        prompt = ImagePromptComponents(**fields)
        return ImagePromptHandler._compile(prompt)

    @staticmethod
    def _compile(prompt: ImagePromptComponents) -> str:
        subject_clause = f"A {prompt.subject}"
        if prompt.action:
            subject_clause += f", {prompt.action}"

        sentences = [
            f"{subject_clause}, in {prompt.scene}.",
            f"{prompt.camera}.",
            f"{prompt.lighting}.",
            f"{prompt.style}.",
        ]
        if prompt.color_palette:
            sentences.append(f"{prompt.color_palette}.")
        return " ".join(sentences)
