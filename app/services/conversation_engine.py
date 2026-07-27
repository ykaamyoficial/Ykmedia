from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from app.models.message import ReceivedMessage
from app.services.category_service import CategoryService

if TYPE_CHECKING:
    from app.services.session_store import SessionStore


class ConversationState(StrEnum):
    IDLE = "IDLE"
    WAITING_CATEGORY = "WAITING_CATEGORY"
    WAITING_FILENAME = "WAITING_FILENAME"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    FINISHED = "FINISHED"


@dataclass(frozen=True, slots=True)
class ConversationResult:
    current_state: ConversationState
    next_state: ConversationState
    suggested_response: str
    is_finished: bool


@dataclass(slots=True)
class ConversationSession:
    state: ConversationState = ConversationState.IDLE
    category: str | None = None
    filename: str | None = None


class ConversationEngine:
    def __init__(
        self,
        session_store: "SessionStore",
        category_service: CategoryService | None = None,
    ) -> None:
        self._session_store = session_store
        self._category_service = category_service or CategoryService()

    def handle(self, message: ReceivedMessage) -> ConversationResult:
        session = self._get_session(message)
        current_state = session.state
        text = self._normalize_text(message.text)

        if current_state is ConversationState.IDLE:
            return self._start_flow(session, current_state)

        if current_state is ConversationState.WAITING_CATEGORY:
            return self._handle_category(session, current_state, text)

        if current_state is ConversationState.WAITING_FILENAME:
            return self._handle_filename(session, current_state, text)

        return ConversationResult(
            current_state=current_state,
            next_state=ConversationState.FINISHED,
            suggested_response="Fluxo ja concluido.",
            is_finished=True,
        )

    def reset(self, remote_jid: str) -> None:
        self._session_store.remove(remote_jid)

    def _get_session(self, message: ReceivedMessage) -> ConversationSession:
        sender_id = message.sender.remote_jid
        session = self._session_store.get(sender_id)
        if session is None:
            return self._session_store.create(sender_id)

        return session

    def _start_flow(
        self,
        session: ConversationSession,
        current_state: ConversationState,
    ) -> ConversationResult:
        session.state = ConversationState.WAITING_CATEGORY
        return ConversationResult(
            current_state=current_state,
            next_state=session.state,
            suggested_response=(
                "Recebi seu arquivo. Como deseja classifica-lo? "
                f"{self._category_service.format_options()}."
            ),
            is_finished=False,
        )

    def _handle_category(
        self,
        session: ConversationSession,
        current_state: ConversationState,
        text: str,
    ) -> ConversationResult:
        category = self._category_service.get_by_option(text)
        if category is None:
            return ConversationResult(
                current_state=current_state,
                next_state=current_state,
                suggested_response=(
                    "Opcao invalida. Responda "
                    f"{self._category_service.format_options()}."
                ),
                is_finished=False,
            )

        session.category = category
        session.state = ConversationState.WAITING_FILENAME
        return ConversationResult(
            current_state=current_state,
            next_state=session.state,
            suggested_response="Qual nome deseja dar ao arquivo?",
            is_finished=False,
        )

    def _handle_filename(
        self,
        session: ConversationSession,
        current_state: ConversationState,
        text: str,
    ) -> ConversationResult:
        if not text:
            return ConversationResult(
                current_state=current_state,
                next_state=current_state,
                suggested_response="Nome invalido. Informe um nome para o arquivo.",
                is_finished=False,
            )

        session.filename = text
        session.state = ConversationState.FINISHED
        return ConversationResult(
            current_state=current_state,
            next_state=session.state,
            suggested_response="Arquivo organizado e conversa finalizada.",
            is_finished=True,
        )

    def get_session(self, remote_jid: str) -> ConversationSession | None:
        return self._session_store.get(remote_jid)

    def _normalize_text(self, text: str | None) -> str:
        return (text or "").strip().lower()
