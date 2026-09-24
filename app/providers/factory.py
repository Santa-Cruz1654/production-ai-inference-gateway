import os

from dotenv import load_dotenv
from fastapi import HTTPException

from app.providers.groq_provider import GroqProvider


load_dotenv()


def create_groq_provider() -> GroqProvider:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not configured",
        )

    return GroqProvider(api_key=api_key)