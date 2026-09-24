from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
)

from app.authorization import require_user
from app.config import INFERENCE_TIMEOUT_SECONDS
from app.model_service import resolve_model
from app.provider_execution import (
    ProviderExecutionService,
)
from app.provider_selector import ProviderSelector
from app.provider_service import ProviderService
from app.providers.factory import (
    create_groq_provider,
)
from app.providers.registry import (
    ProviderRegistry,
)
from app.rate_limit import require_rate_limit
from app.retry import RetryPolicy
from app.schemas import (
    InferenceRequest,
    InferenceResponse,
    ProviderRequest,
)
from app.timeout import RequestDeadline


app = FastAPI(
    title="Production AI Inference Gateway",
    version="0.1.0",
)


# ---------------------------------------------------------
# Request ID Middleware
# ---------------------------------------------------------

@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next,
):

    import uuid

    request_id = request.headers.get(
        "X-Request-ID"
    )

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = (
        request_id
    )

    return response


# ---------------------------------------------------------
# Provider Initialization
# ---------------------------------------------------------

provider_registry = ProviderRegistry()

provider_registry.register(
    "groq",
    create_groq_provider(),
)

provider_selector = ProviderSelector(
    provider_registry
)

provider_service = ProviderService(
    provider_selector
)


# ---------------------------------------------------------
# Provider Execution
# ---------------------------------------------------------

provider_execution_service = (
    ProviderExecutionService(
        RetryPolicy(
            max_attempts=3,
            base_delay_seconds=1.0,
            max_delay_seconds=8.0,
            jitter_seconds=0.25,
        )
    )
)


# ---------------------------------------------------------
# Basic Endpoints
# ---------------------------------------------------------

@app.get("/")
async def root():

    return {
        "service": (
            "Production AI Inference Gateway"
        ),
        "status": "running",
    }


@app.get("/health")
async def health():

    return {
        "status": "healthy",
    }


# ---------------------------------------------------------
# Inference
# ---------------------------------------------------------

@app.post(
    "/v1/inference",
    response_model=InferenceResponse,
)
async def inference(
    request: InferenceRequest,
    client: Annotated[
        dict,
        Depends(require_rate_limit),
    ],
    http_request: Request,
):

    # ---------------------------------------------
    # Model Selection
    # ---------------------------------------------

    model = resolve_model(
        request.model,
        request.max_tokens,
    )

    # ---------------------------------------------
    # Provider Selection
    # ---------------------------------------------

    provider, provider_model = (
        provider_service.select_provider(
            model.name
        )
    )

    # ---------------------------------------------
    # Provider Request
    # ---------------------------------------------

    provider_request = ProviderRequest(
        model=provider_model,
        prompt=request.prompt,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    # ---------------------------------------------
    # Request Deadline
    # ---------------------------------------------

    deadline = RequestDeadline(
        INFERENCE_TIMEOUT_SECONDS
    )

    # ---------------------------------------------
    # Provider Execution
    #
    # Timeout
    # Retry
    # Backoff
    # Retry-After
    # Jitter
    # ---------------------------------------------

    try:

        provider_response = (
            await provider_execution_service.execute(
                provider=provider,
                request=provider_request,
                deadline=deadline,
            )
        )

    except TimeoutError:

        raise HTTPException(
            status_code=504,
            detail=(
                "LLM provider request timed out"
            ),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )

    # ---------------------------------------------
    # Response
    # ---------------------------------------------

    return InferenceResponse(
        request_id=(
            http_request.state.request_id
        ),
        model=model.name,
        response=provider_response.text,
    )