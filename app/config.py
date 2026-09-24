import os


INFERENCE_TIMEOUT_SECONDS = float(
    os.getenv(
        "INFERENCE_TIMEOUT_SECONDS",
        "30",
    )
)