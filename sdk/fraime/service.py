from fraime.model import GenerateVideoRequest, GenerateVideoResponse, ModelsConfig, RulesConfig
from fraime.repository import GenerationRepository


class GenerationService:
    def __init__(self, repository: GenerationRepository):
        self._repository = repository

    def generate_video(self, request: GenerateVideoRequest) -> GenerateVideoResponse:
        payload = request.model_dump(mode="json", exclude_none=True, exclude={"fields"})
        payload["fields"] = request.fields.model_dump(mode="json", exclude_none=True)

        raw = self._repository.post_generate(payload)
        return GenerateVideoResponse.model_validate(raw)

    def get_models_config(self) -> ModelsConfig:
        raw = self._repository.get_models_config()
        return ModelsConfig.model_validate(raw)

    def get_rules_config(self) -> RulesConfig:
        raw = self._repository.get_rules_config()
        return RulesConfig.model_validate(raw)
