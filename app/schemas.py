from pydantic import BaseModel, ConfigDict, Field


class InferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(
        ...,
        min_length=1,
        description="Logical model name exposed by the gateway",
    )

    prompt: str = Field(
        ...,
        min_length=1,
        description="User prompt",
    )

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
    )

    max_tokens: int = Field(
        default=512,
        gt=0,
    )


class InferenceResponse(BaseModel):
    request_id: str
    model: str
    response: str


class ProviderRequest(BaseModel):
    model: str
    prompt: str
    temperature: float
    max_tokens: int


class ProviderResponse(BaseModel):
    text: str