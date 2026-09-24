from fastapi import HTTPException, status


MODEL_PROVIDER_MAP = {
    "fast-model": [
        {
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
        }
    ],
    "quality-model": [
        {
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
        }
    ],
    "reasoning-model": [
        {
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
        }
    ],
}


def get_provider_candidates(
    model_name: str,
) -> list[dict]:

    providers = MODEL_PROVIDER_MAP.get(
        model_name
    )

    if not providers:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"No provider configured for "
                f"model '{model_name}'"
            ),
        )

    return providers