from dataclasses import dataclass
from enum import StrEnum


class InteractionSource(StrEnum):
    BUTTON_REPLY = "BUTTON_REPLY"
    LIST_REPLY = "LIST_REPLY"
    TEXT_FALLBACK = "TEXT_FALLBACK"


@dataclass(frozen=True, slots=True)
class InteractiveOption:
    id: str
    title: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class InteractivePrompt:
    text: str
    options: list[InteractiveOption]
    footer: str | None = None
    button_text: str | None = None


@dataclass(frozen=True, slots=True)
class IncomingInteraction:
    option_id: str
    option_title: str | None
    source_type: InteractionSource
