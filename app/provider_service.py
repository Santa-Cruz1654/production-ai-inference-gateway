from app.provider_selector import ProviderSelector
from app.routing import get_provider_candidates


class ProviderService:

    def __init__(
        self,
        selector: ProviderSelector,
    ):
        self.selector = selector

    def select_provider(
        self,
        model_name: str,
    ):
        candidates = get_provider_candidates(
            model_name
        )

        primary = candidates[0]

        return (
            self.selector.select(
                primary["provider"]
            ),
            primary["model"],
        )