"""Topic -> Deck using the Claude API with structured outputs (the reply is validated against ``Deck``)."""

from __future__ import annotations

import os

import anthropic

from deckgen.ai.prompts import system_prompt, user_prompt
from deckgen.models import Deck, Layout, Slide

DEFAULT_MODEL = os.environ.get("DECKGEN_MODEL", "claude-opus-5")
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class GenerationError(RuntimeError):
    pass


def has_credentials() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def generate_deck(
    topic: str,
    *,
    slides: int = 10,
    style: str = "business",
    audience: str | None = None,
    tone: str | None = None,
    context: str | None = None,
    language: str | None = None,
    model: str | None = None,
    effort: str = "high",
    client: anthropic.Anthropic | None = None,
) -> Deck:
    client = client or anthropic.Anthropic()
    try:
        response = client.beta.messages.parse(
            model=model or DEFAULT_MODEL,
            max_tokens=16000,
            system=system_prompt(style),
            messages=[{"role": "user", "content": user_prompt(topic, slides, audience, tone, context, language)}],
            thinking={"type": "adaptive"},
            output_config={"effort": effort},
            output_format=Deck,
            # If a safety classifier declines, the API retries on a fallback model inside the same call.
            betas=[FALLBACK_BETA],
            fallbacks="default",
        )
    except anthropic.AuthenticationError as exc:
        raise GenerationError("Anthropic API authentication failed: check ANTHROPIC_API_KEY") from exc
    except anthropic.RateLimitError as exc:
        raise GenerationError("Rate limited by the Anthropic API; retry later") from exc
    except anthropic.APIStatusError as exc:
        raise GenerationError(f"Anthropic API error {exc.status_code}: {exc.message}") from exc
    except anthropic.APIConnectionError as exc:
        raise GenerationError("Could not reach the Anthropic API") from exc

    if response.stop_reason == "refusal":
        raise GenerationError("The model declined to generate this deck")
    if response.stop_reason == "max_tokens":
        raise GenerationError("Response was cut off (max_tokens); request fewer slides")
    deck = response.parsed_output
    if deck is None:
        raise GenerationError("Model returned no parsable deck")
    deck.style = style  # type: ignore[assignment]
    if not deck.slides or deck.slides[0].layout != Layout.TITLE:
        deck.slides.insert(0, Slide(layout=Layout.TITLE, title=deck.title, subtitle=deck.subtitle))
    return deck
