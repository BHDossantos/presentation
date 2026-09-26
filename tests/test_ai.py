from types import SimpleNamespace

import pytest

from deckgen.ai import GenerationError, generate_deck
from deckgen.ai.prompts import system_prompt
from deckgen.models import Deck, Layout, Slide


class FakeMessages:
    def __init__(self, response):
        self.response = response
        self.kwargs = None

    def parse(self, **kwargs):
        self.kwargs = kwargs
        return self.response


def fake_client(response):
    messages = FakeMessages(response)
    return SimpleNamespace(beta=SimpleNamespace(messages=messages)), messages


def test_generate_deck_uses_structured_output():
    deck = Deck(title="Solar", slides=[Slide(title="Solar pays back in eight years", bullets=["x"])])
    client, messages = fake_client(SimpleNamespace(stop_reason="end_turn", parsed_output=deck))
    out = generate_deck("Solar", style="academic", client=client, slides=8)
    assert out.slides[0].layout == Layout.TITLE and out.style == "academic"
    assert messages.kwargs["output_format"] is Deck
    assert messages.kwargs["thinking"] == {"type": "adaptive"}
    assert "about 8 slides" in messages.kwargs["messages"][0]["content"]
    assert "Action Titles" in messages.kwargs["system"]  # academic guidelines embedded


def test_refusal_raises():
    client, _ = fake_client(SimpleNamespace(stop_reason="refusal", parsed_output=None))
    with pytest.raises(GenerationError):
        generate_deck("x", client=client)


def test_business_prompt_has_layout_guide():
    assert "two_column" in system_prompt("business") and "Action Titles" not in system_prompt("business")
