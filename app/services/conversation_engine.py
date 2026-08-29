from dataclasses import dataclass, replace
from enum import StrEnum
import logging
import time
import unicodedata
from typing import TYPE_CHECKING

from app.core.config import settings
from app.models.interactive import IncomingInteraction, InteractivePrompt
from app.models.message import MessageType, ReceivedMessage
from app.services.category_service import CategoryService
from app.services.interactive_menu_builder import InteractiveMenuBuilder
from app.services.message_catalog import WhatsAppMessageCatalog

if TYPE_CHECKING:
    from app.services.session_store import SessionStore

KEEP_ORIGINAL_FILENAME = "__KEEP_ORIGINAL__"


def _session_timeout_seconds() -> float:
    return settings.CONVERSATION_FLOW_TIMEOUT_SECONDS


def _first_name(display_name: str | None) -> str | None:
    if not display_name:
        return None
    first = display_name.strip().split()
    return first[0] if first else None


def _strip_accents(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value.strip())
        if not unicodedata.combining(char)
    )


logger = logging.getLogger(__name__)


class ConversationState(StrEnum):
    IDLE = "IDLE"
    WAITING_MEDIA = "AGUARDANDO_MIDIA"
    MEDIA_RECEIVED = "MIDIA_RECEBIDA"
    WAITING_CATEGORY_SELECTION = "AGUARDANDO_CATEGORIA"
    WAITING_CONFIRMATION = "AGUARDANDO_CONFIRMACAO"
    SAVING = "SALVANDO"
    FINISHED = "FINALIZADO"
    WAITING_FILENAME_DECISION = "AGUARDANDO_RENOMEAR"
    WAITING_CUSTOM_FILENAME = "AGUARDANDO_NOME_ARQUIVO"
    PROCESSING = "SALVANDO"


@dataclass(frozen=True, slots=True)
class ConversationResult:
    current_state: ConversationState
    next_state: ConversationState
    suggested_response: str
    is_finished: bool
    interactive_prompt: InteractivePrompt | None = None


@dataclass(slots=True)
class ConversationSession:
    state: ConversationState = ConversationState.IDLE
    category: str | None = None
    filename: str | None = None
    pending_media_id: str | None = None
    pending_media_ids: tuple[str, ...] = ()
    allowed_option_ids: tuple[str, ...] = ()
    processed_interaction_ids: tuple[str, ...] = ()
    interactive_created_at: float | None = None
    created_at: float | None = None
    expires_at: float | None = None
    last_interaction_at: float | None = None
    origin: str | None = None
    contact_id: str | None = None
    contact_name: str | None = None
    greeting_sent: bool = False
    expiry_warning_sent: bool = False
    received_types: tuple[str, ...] = ()


class ConversationEngine:
    def __init__(
        self,
        session_store: "SessionStore",
        category_service: CategoryService | None = None,
        menu_builder: InteractiveMenuBuilder | None = None,
    ) -> None:
        self._session_store = session_store
        self._category_service = category_service or CategoryService()
        self._menu_builder = menu_builder or InteractiveMenuBuilder()

    def handle(self, message: ReceivedMessage) -> ConversationResult:
        sender_id = message.sender.remote_jid
        session = self._session_store.get(sender_id)
        if session is None:
            if message.sender.is_group:
                logger.info("Mensagem ignorada: origem = grupo.")
                return self._empty_result(ConversationState.IDLE)
            if not self._can_start_session(message):
                return self._empty_result(ConversationState.IDLE)
            session = self._session_store.create(sender_id)

        current_state = session.state
        text = self._normalize_text(message.text)

        if message.sender.is_group:
            logger.info("Mensagem ignorada: origem = grupo.")
            return self._empty_result(current_state)

        if self._is_expired(session):
            logger.info("Timeout da sessao: telefone=%s", sender_id)
            self.reset(sender_id)
            return ConversationResult(
                current_state=current_state,
                next_state=ConversationState.IDLE,
                suggested_response=WhatsAppMessageCatalog.conversation_timeout(),
                is_finished=True,
            )

        if current_state is ConversationState.IDLE:
            return self._start_flow(sender_id, session, current_state, message)

        if current_state is ConversationState.FINISHED:
            self.reset(sender_id)
            if not self._can_start_session(message):
                return self._empty_result(ConversationState.IDLE)
            session = self._session_store.create(sender_id)
            return self._start_flow(sender_id, session, ConversationState.IDLE, message)

        if self._is_valid_media(message):
            return self._append_media(sender_id, session, current_state, message)

        if current_state is ConversationState.WAITING_MEDIA:
            return self._handle_collecting(
                sender_id, session, current_state, text, message.interaction
            )

        if current_state is ConversationState.WAITING_CATEGORY_SELECTION:
            return self._handle_category(sender_id, session, current_state, text, message.interaction)

        if current_state is ConversationState.WAITING_FILENAME_DECISION:
            return self._handle_filename_decision(sender_id, session, current_state, text, message.interaction)

        if current_state is ConversationState.WAITING_CUSTOM_FILENAME:
            return self._handle_custom_filename(sender_id, session, current_state, text)

        if current_state is ConversationState.WAITING_CONFIRMATION:
            return self._handle_confirmation(
                sender_id, session, current_state, text, message.interaction
            )

        return ConversationResult(
            current_state=current_state,
            next_state=ConversationState.IDLE,
            suggested_response=WhatsAppMessageCatalog.conversation_finished(),
            is_finished=True,
        )

    def reset(self, remote_jid: str) -> None:
        self._session_store.remove(remote_jid)

    def attach_pending_media(self, remote_jid: str, media_id: str | None) -> None:
        session = self._session_store.get(remote_jid)
        if session is None:
            session = self._session_store.create(remote_jid)

        if media_id is None:
            session.pending_media_id = None
            session.pending_media_ids = ()
        elif media_id not in session.pending_media_ids:
            session.pending_media_id = media_id
            session.pending_media_ids = (*session.pending_media_ids, media_id)
        self._session_store.update(remote_jid, session)

    def get_session(self, remote_jid: str) -> ConversationSession | None:
        return self._session_store.get(remote_jid)

    def build_pending_category_response(
        self,
        remote_jid: str,
        current_state: ConversationState = ConversationState.IDLE,
    ) -> ConversationResult | None:
        session = self._session_store.get(remote_jid)
        if session is None or session.state is not ConversationState.WAITING_CATEGORY_SELECTION:
            return None

        prompt = self._menu_builder.build_category_menu(self._category_service)
        self._set_allowed_options(session, prompt)
        self._session_store.update(remote_jid, session)
        return self._category_prompt_result(current_state, session, prompt)

    def _get_session(self, message: ReceivedMessage) -> ConversationSession:
        sender_id = message.sender.remote_jid
        session = self._session_store.get(sender_id)
        if session is None:
            return self._session_store.create(sender_id)
        return session

    def _start_flow(
        self,
        sender_id: str,
        session: ConversationSession,
        current_state: ConversationState,
        message: ReceivedMessage,
    ) -> ConversationResult:
        now = self._now()
        session.state = ConversationState.WAITING_MEDIA
        session.created_at = now
        session.last_interaction_at = now
        session.expires_at = now + _session_timeout_seconds()
        session.contact_id = sender_id
        session.contact_name = _first_name(message.sender.display_name)
        session.origin = "YouTube" if message.raw_type == "youtubeMessage" else "WhatsApp"
        session.greeting_sent = True
        self._append_type(session, message)
        prompt = self._menu_builder.build_collecting_menu()
        self._set_allowed_options(session, prompt)
        self._session_store.update(sender_id, session)
        return self._collecting_result(current_state, session, prompt, greet=True)

    def _collecting_result(
        self,
        current_state: ConversationState,
        session: ConversationSession,
        prompt: InteractivePrompt,
        *,
        greet: bool = False,
        nudge: bool = False,
    ) -> ConversationResult:
        body = WhatsAppMessageCatalog.collecting_step(
            summary=self._session_summary(session),
            contact_name=session.contact_name if greet else None,
            nudge=nudge,
        )
        return ConversationResult(
            current_state=current_state,
            next_state=session.state,
            suggested_response=body,
            is_finished=False,
            interactive_prompt=replace(prompt, text=body),
        )

    def _handle_collecting(
        self,
        sender_id: str,
        session: ConversationSession,
        current_state: ConversationState,
        text: str,
        interaction: IncomingInteraction | None,
    ) -> ConversationResult:
        option_id = self._option_id(text=text, interaction=interaction).lower()
        normalized = _strip_accents(text.lower())
        if option_id == "collect:done" or normalized in {
            "concluir",
            "concluir envio",
            "pronto",
            "terminei",
            "finalizar",
            "ok",
        }:
            session.state = ConversationState.WAITING_CATEGORY_SELECTION
            prompt = self._menu_builder.build_category_menu(self._category_service)
            self._set_allowed_options(session, prompt)
            self._session_store.update(sender_id, session)
            return self._category_prompt_result(current_state, session, prompt)

        prompt = self._menu_builder.build_collecting_menu()
        self._set_allowed_options(session, prompt)
        self._session_store.update(sender_id, session)
        return self._collecting_result(current_state, session, prompt, nudge=True)

    def _append_media(
        self,
        sender_id: str,
        session: ConversationSession,
        current_state: ConversationState,
        message: ReceivedMessage,
    ) -> ConversationResult:
        self._append_type(session, message)
        session.last_interaction_at = self._now()
        session.expires_at = self._now() + _session_timeout_seconds()
        session.expiry_warning_sent = False
        self._session_store.update(sender_id, session)
        logger.info(
            "Midia adicionada a sessao: telefone=%s quantidade=%s",
            sender_id,
            len(session.pending_media_ids),
        )
        return ConversationResult(
            current_state=current_state,
            next_state=session.state,
            suggested_response="",
            is_finished=False,
        )

    def _handle_category(
        self,
        sender_id: str,
        session: ConversationSession,
        current_state: ConversationState,
        text: str,
        interaction: IncomingInteraction | None,
    ) -> ConversationResult:
        option_id = self._option_id(text=text, interaction=interaction)
        if option_id.startswith("action:next_page:") or option_id.startswith("action:previous_page:"):
            page = self._page_from_option(option_id)
            prompt = self._menu_builder.build_category_menu(self._category_service, page=page)
            self._set_allowed_options(session, prompt)
            self._session_store.update(sender_id, session)
            return ConversationResult(
                current_state=current_state,
                next_state=current_state,
                suggested_response=WhatsAppMessageCatalog.menu_text(prompt),
                is_finished=False,
                interactive_prompt=prompt,
            )

        category = self._category_from_option(option_id, text)
        if category is None:
            prompt = self._menu_builder.build_category_menu(self._category_service)
            self._set_allowed_options(session, prompt)
            self._session_store.update(sender_id, session)
            return self._category_prompt_result(
                current_state, session, prompt, invalid=True
            )

        session.category = category
        session.last_interaction_at = self._now()
        logger.info("Categoria escolhida: telefone=%s categoria=%s", sender_id, category)

        if self._pending_media_count(session) == 1:
            session.state = ConversationState.WAITING_FILENAME_DECISION
            self._clear_allowed_options(session)
            self._session_store.update(sender_id, session)
            return ConversationResult(
                current_state=current_state,
                next_state=session.state,
                suggested_response=WhatsAppMessageCatalog.filename_decision_text(),
                is_finished=False,
            )

        # Lote: sem passo de nome (numeracao automatica) -> vai direto confirmar.
        session.filename = KEEP_ORIGINAL_FILENAME
        return self._go_to_confirmation(sender_id, session, current_state)

    def _handle_filename_decision(
        self,
        sender_id: str,
        session: ConversationSession,
        current_state: ConversationState,
        text: str,
        interaction: IncomingInteraction | None,
    ) -> ConversationResult:
        option_id = self._option_id(text=text, interaction=interaction)
        normalized_option_id = option_id.lower()
        if normalized_option_id == "filename:keep_original" or text == "1":
            session.filename = KEEP_ORIGINAL_FILENAME
            return self._go_to_confirmation(sender_id, session, current_state)

        if normalized_option_id == "filename:custom" or text == "2":
            session.state = ConversationState.WAITING_CUSTOM_FILENAME
            self._clear_allowed_options(session)
            self._session_store.update(sender_id, session)
            return ConversationResult(
                current_state=current_state,
                next_state=session.state,
                suggested_response=WhatsAppMessageCatalog.custom_filename_request(),
                is_finished=False,
            )

        prompt = self._menu_builder.build_filename_menu()
        self._set_allowed_options(session, prompt)
        self._session_store.update(sender_id, session)
        return ConversationResult(
            current_state=current_state,
            next_state=current_state,
            suggested_response=WhatsAppMessageCatalog.invalid_filename_decision(prompt),
            is_finished=False,
            interactive_prompt=prompt,
        )

    def _handle_custom_filename(
        self,
        sender_id: str,
        session: ConversationSession,
        current_state: ConversationState,
        text: str,
    ) -> ConversationResult:
        return self._set_custom_filename(sender_id, session, current_state, text)

    def _set_custom_filename(
        self,
        sender_id: str,
        session: ConversationSession,
        current_state: ConversationState,
        text: str,
    ) -> ConversationResult:
        if not text:
            return ConversationResult(
                current_state=current_state,
                next_state=current_state,
                suggested_response=WhatsAppMessageCatalog.invalid_filename(),
                is_finished=False,
            )

        session.filename = text
        return self._go_to_confirmation(sender_id, session, current_state)

    def _go_to_confirmation(
        self,
        sender_id: str,
        session: ConversationSession,
        current_state: ConversationState,
    ) -> ConversationResult:
        session.state = ConversationState.WAITING_CONFIRMATION
        session.last_interaction_at = self._now()
        prompt = self._menu_builder.build_confirmation_menu()
        self._set_allowed_options(session, prompt)
        self._session_store.update(sender_id, session)
        body = WhatsAppMessageCatalog.confirmation_step(
            category=session.category,
            filename=session.filename,
            count=self._pending_media_count(session),
        )
        return ConversationResult(
            current_state=current_state,
            next_state=session.state,
            suggested_response=body,
            is_finished=False,
            interactive_prompt=replace(prompt, text=body),
        )

    def _handle_confirmation(
        self,
        sender_id: str,
        session: ConversationSession,
        current_state: ConversationState,
        text: str,
        interaction: IncomingInteraction | None,
    ) -> ConversationResult:
        option_id = self._option_id(text=text, interaction=interaction).lower()
        normalized = _strip_accents(text.lower())

        if option_id == "confirm:yes" or normalized in {"confirmar", "confirmar envio", "sim", "1"}:
            return self._finish(sender_id, session, current_state)

        if option_id == "confirm:edit" or normalized in {"corrigir", "2"}:
            session.state = ConversationState.WAITING_CATEGORY_SELECTION
            session.category = None
            session.filename = None
            prompt = self._menu_builder.build_category_menu(self._category_service)
            self._set_allowed_options(session, prompt)
            self._session_store.update(sender_id, session)
            return self._category_prompt_result(current_state, session, prompt)

        if option_id == "confirm:cancel" or normalized in {"cancelar", "3"}:
            self.reset(sender_id)
            return ConversationResult(
                current_state=current_state,
                next_state=ConversationState.IDLE,
                suggested_response=WhatsAppMessageCatalog.command_cancelled(),
                is_finished=True,
            )

        prompt = self._menu_builder.build_confirmation_menu()
        self._set_allowed_options(session, prompt)
        self._session_store.update(sender_id, session)
        return ConversationResult(
            current_state=current_state,
            next_state=current_state,
            suggested_response=WhatsAppMessageCatalog.invalid_confirmation(),
            is_finished=False,
            interactive_prompt=prompt,
        )

    def _finish(
        self,
        sender_id: str,
        session: ConversationSession,
        current_state: ConversationState,
    ) -> ConversationResult:
        session.state = ConversationState.FINISHED
        self._clear_allowed_options(session)
        self._session_store.update(sender_id, session)
        return ConversationResult(
            current_state=current_state,
            next_state=session.state,
            suggested_response=self._finished_message(session),
            is_finished=True,
        )

    def _option_id(self, text: str, interaction: IncomingInteraction | None) -> str:
        if interaction is not None:
            return interaction.option_id.strip()
        return text

    def _category_from_option(self, option_id: str, text: str) -> str | None:
        if option_id.startswith("category:"):
            try:
                option_number = int(option_id.split(":", 1)[1])
            except ValueError:
                return None
            return self._category_service.get_by_option(str(option_number))
        return self._category_service.get_by_option(text)

    def _page_from_option(self, option_id: str) -> int:
        try:
            return int(option_id.rsplit(":", 1)[1])
        except ValueError:
            return 1

    def _set_allowed_options(self, session: ConversationSession, prompt: InteractivePrompt) -> None:
        session.allowed_option_ids = tuple(option.id for option in prompt.options)

    def _clear_allowed_options(self, session: ConversationSession) -> None:
        session.allowed_option_ids = ()
        session.interactive_created_at = None

    def _normalize_text(self, text: str | None) -> str:
        return (text or "").strip()

    def _can_start_session(self, message: ReceivedMessage) -> bool:
        return self._is_valid_media(message) or message.message_type is MessageType.LINK

    def _is_valid_media(self, message: ReceivedMessage) -> bool:
        return message.message_type in {
            MessageType.IMAGE,
            MessageType.AUDIO,
            MessageType.VIDEO,
            MessageType.DOCUMENT,
        }

    def _append_type(self, session: ConversationSession, message: ReceivedMessage) -> None:
        value = message.message_type.value
        session.received_types = (*session.received_types, value)

    def _session_summary(self, session: ConversationSession) -> str:
        counts: dict[str, int] = {}
        for value in session.received_types:
            counts[value] = counts.get(value, 0) + 1
        return WhatsAppMessageCatalog.media_summary(
            total=max(1, len(session.received_types)),
            type_counts=counts,
        )

    def _category_prompt_result(
        self,
        current_state: ConversationState,
        session: ConversationSession,
        prompt: InteractivePrompt,
        *,
        greet: bool = False,
        invalid: bool = False,
    ) -> ConversationResult:
        menu_text = WhatsAppMessageCatalog.menu_text(prompt)
        body = WhatsAppMessageCatalog.category_step(
            summary=self._session_summary(session),
            menu_text=menu_text,
            contact_name=session.contact_name if greet else None,
            invalid=invalid,
        )
        rich_prompt = replace(prompt, text=body)
        return ConversationResult(
            current_state=current_state,
            next_state=session.state,
            suggested_response=body,
            is_finished=False,
            interactive_prompt=rich_prompt,
        )

    def _finished_message(self, session: ConversationSession) -> str:
        return WhatsAppMessageCatalog.media_finished(
            contact_name=session.contact_name,
            category=session.category,
            count=self._pending_media_count(session),
        )

    def _pending_media_count(self, session: ConversationSession) -> int:
        if session.pending_media_ids:
            return len(session.pending_media_ids)
        if session.pending_media_id:
            return 1
        return max(1, len(session.received_types))

    def _is_expired(self, session: ConversationSession) -> bool:
        return (
            session.state is not ConversationState.IDLE
            and session.expires_at is not None
            and self._now() >= session.expires_at
        )

    def _empty_result(self, state: ConversationState) -> ConversationResult:
        return ConversationResult(
            current_state=state,
            next_state=state,
            suggested_response="",
            is_finished=False,
        )

    def _now(self) -> float:
        return time.time()
