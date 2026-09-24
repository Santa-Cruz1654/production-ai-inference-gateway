from fastapi import HTTPException, status

from app.models import MODEL_REGISTRY, ModelDefinition


def select_model(model_name: str) -> ModelDefinition:
    model = MODEL_REGISTRY.get(model_name)

    if model is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown model: {model_name}",
        )

    return model


def validate_model_request(
    model: ModelDefinition,
    max_tokens: int,
) -> None:

    if max_tokens > model.max_tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"max_tokens exceeds the limit for "
                f"model '{model.name}'"
            ),
        )