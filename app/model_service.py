from app.model_selector import (
    select_model,
    validate_model_request,
)
from app.models import ModelDefinition


def resolve_model(
    model_name: str,
    max_tokens: int,
) -> ModelDefinition:

    model = select_model(model_name)

    validate_model_request(
        model,
        max_tokens,
    )

    return model