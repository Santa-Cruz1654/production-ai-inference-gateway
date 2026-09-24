from dataclasses import dataclass


@dataclass(frozen=True)
class ModelDefinition:
    name: str
    capability: str
    default_temperature: float
    max_tokens: int


MODEL_REGISTRY: dict[str, ModelDefinition] = {
    "fast-model": ModelDefinition(
        name="fast-model",
        capability="fast",
        default_temperature=0.7,
        max_tokens=4096,
    ),
    "quality-model": ModelDefinition(
        name="quality-model",
        capability="quality",
        default_temperature=0.7,
        max_tokens=8192,
    ),
    "reasoning-model": ModelDefinition(
        name="reasoning-model",
        capability="reasoning",
        default_temperature=0.2,
        max_tokens=16384,
    ),
}