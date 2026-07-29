from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
import qtawesome as qta

ICON_COLOR = "#e8f2ff"
MUTED_ICON_COLOR = "#8da3b8"
ACCENT_COLOR = "#3b82f6"


def app_icon(name: str, color: str = ICON_COLOR) -> QIcon:
    return qta.icon(name, color=color)


class YKPanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("yk_panel")


class YKScrollArea(QScrollArea):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("yk_scroll_area")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)


class YKSectionTitle(QLabel):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("yk_section_title")


class YKPageHeader(QFrame):
    def __init__(self, title: str, description: str = "") -> None:
        super().__init__()
        self.setObjectName("yk_page_header")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setObjectName("header_title")
        description_label = QLabel(description)
        description_label.setObjectName("muted")
        layout.addWidget(title_label)
        if description:
            layout.addWidget(description_label)


class YKSearchField(QLineEdit):
    def __init__(self, placeholder: str = "") -> None:
        super().__init__()
        self.setObjectName("yk_search_field")
        self.setPlaceholderText(placeholder)
        self.addAction(app_icon("fa5s.search", MUTED_ICON_COLOR), QLineEdit.ActionPosition.LeadingPosition)


class IconBadge(QFrame):
    def __init__(self, icon_name: str, tone: str = "primary", size: int = 44) -> None:
        super().__init__()
        self.setObjectName("icon_badge")
        self.setProperty("tone", tone)
        self.setFixedSize(size, size)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setPixmap(app_icon(icon_name).pixmap(max(18, size // 2), max(18, size // 2)))
        layout.addWidget(self.icon_label)


class StatusChip(QFrame):
    def __init__(self, text: str, tone: str = "neutral") -> None:
        super().__init__()
        self.setObjectName("status_chip")
        self.setProperty("tone", tone)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(7)
        dot = QLabel()
        dot.setObjectName("status_dot")
        dot.setProperty("tone", tone)
        dot.setFixedSize(8, 8)
        self.label = QLabel(text)
        self.label.setObjectName("status_chip_text")
        layout.addWidget(dot)
        layout.addWidget(self.label)

    def set_text(self, text: str) -> None:
        self.label.setText(text)


class YKStatusBadge(StatusChip):
    def __init__(self, text: str, tone: str = "neutral") -> None:
        super().__init__(text, tone)
        self.setObjectName("yk_status_badge")


class CompactButton(QPushButton):
    def __init__(self, text: str, variant: str = "secondary", icon_name: str | None = None) -> None:
        super().__init__(text)
        self.setObjectName("compact_button")
        self.setProperty("variant", variant)
        self.setMinimumHeight(32)
        if icon_name:
            self.setIcon(app_icon(icon_name))


class YKButton(CompactButton):
    def __init__(self, text: str, variant: str = "secondary", icon_name: str | None = None) -> None:
        super().__init__(text, variant, icon_name)
        self.setObjectName("yk_button")
        self.setMinimumHeight(32)


class YKIconButton(QPushButton):
    def __init__(self, icon_name: str, tooltip: str = "") -> None:
        super().__init__("")
        self.setObjectName("yk_icon_button")
        self.setIcon(app_icon(icon_name, MUTED_ICON_COLOR))
        self.setFixedSize(32, 32)
        if tooltip:
            self.setToolTip(tooltip)


class YKChip(QPushButton):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("yk_chip")
        self.setCheckable(True)
        self.setMinimumHeight(26)


class AvatarBadge(QFrame):
    def __init__(self, initials: str, tone: str = "primary", size: int = 54, image_path: str = "") -> None:
        super().__init__()
        self.setObjectName("avatar_badge")
        self.setProperty("tone", tone)
        self.setFixedSize(size, size)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(initials[:2].upper())
        label.setObjectName("avatar_text")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if image_path:
            pixmap = _rounded_pixmap(image_path, size)
            if not pixmap.isNull():
                label.setText("")
                label.setPixmap(pixmap)
        layout.addWidget(label)


class YKAvatar(AvatarBadge):
    pass


class YKInfoRow(QFrame):
    def __init__(self, label: str, value: str = "-") -> None:
        super().__init__()
        self.setObjectName("yk_info_row")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        label_widget = QLabel(label)
        label_widget.setObjectName("info_label")
        self.value_widget = QLabel(value)
        self.value_widget.setObjectName("info_value")
        self.value_widget.setWordWrap(True)
        layout.addWidget(label_widget)
        layout.addWidget(self.value_widget)

    def set_value(self, value: str) -> None:
        self.value_widget.setText(value)


class ContactListItem(QFrame):
    def __init__(self, conversation: dict[str, object]) -> None:
        super().__init__()
        self.setObjectName("contact_item")
        self.setProperty("active", bool(conversation.get("active")))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        initials = str(conversation.get("initials", "YK"))
        layout.addWidget(YKAvatar(initials, tone=_avatar_tone(initials), size=38, image_path=str(conversation.get("profile_photo_path", ""))))

        body = QVBoxLayout()
        body.setSpacing(0)
        top = QHBoxLayout()
        name = QLabel(str(conversation.get("display_name") or conversation.get("sender", "Contato")))
        name.setObjectName("contact_name")
        time = QLabel(str(conversation.get("last_activity", "")))
        time.setObjectName("contact_time")
        top.addWidget(name, 1)
        top.addWidget(time)

        phone = QLabel(str(conversation.get("sender", "")))
        phone.setObjectName("contact_phone")

        bottom = QHBoxLayout()
        files = QLabel(f"{conversation.get('media_count', 0)} arquivo(s) - {conversation.get('last_media', 'Arquivo')}")
        files.setObjectName("contact_state")
        files.setProperty("active", True)
        count = QLabel(str(conversation.get("message_count", "0")))
        if "media_count" in conversation:
            count.setText(str(conversation.get("media_count", "0")))
        count.setObjectName("contact_count")
        bottom.addWidget(files)
        bottom.addStretch(1)
        bottom.addWidget(count)

        body.addLayout(top)
        body.addWidget(phone)
        body.addLayout(bottom)
        layout.addLayout(body, 1)


class YKConversationCard(ContactListItem):
    pass


class ConversationProfileHeader(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("conversation_profile")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        self.avatar_slot = QHBoxLayout()
        layout.addLayout(self.avatar_slot)

        body = QVBoxLayout()
        body.setSpacing(4)
        self.title = QLabel("Selecione uma conversa")
        self.title.setObjectName("profile_title")
        self.subtitle = QLabel("Escolha um contato para visualizar a timeline.")
        self.subtitle.setObjectName("profile_subtitle")
        body.addWidget(self.title)
        body.addWidget(self.subtitle)
        layout.addLayout(body, 1)

        self.status = StatusChip("Sem conversa", "neutral")
        menu = CompactButton("", icon_name="fa5s.ellipsis-v")
        menu.setFixedWidth(36)
        layout.addWidget(self.status)
        layout.addWidget(menu)

    def update_contact(self, conversation: dict[str, object] | None) -> None:
        _clear_layout(self.avatar_slot)
        if conversation is None:
            self.avatar_slot.addWidget(YKAvatar("YK", tone="primary", size=56))
            self.title.setText("Selecione um remetente")
            self.subtitle.setText("Escolha um contato para visualizar os arquivos.")
            self.status.set_text("Sem conversa")
            return

        initials = str(conversation.get("initials", "YK"))
        self.avatar_slot.addWidget(YKAvatar(initials, tone=_avatar_tone(initials), size=58, image_path=str(conversation.get("profile_photo_path", ""))))
        self.title.setText(str(conversation.get("display_name") or conversation.get("sender", "Contato")))
        self.subtitle.setText(str(conversation.get("sender", "")))
        self.status.set_text(
            f"{conversation.get('media_count', 0)} arquivo(s) - Ultima midia {conversation.get('last_activity', '-')}"
        )


class ConversationStatCard(QFrame):
    def __init__(self, title: str, value: str, icon_name: str, tone: str = "primary") -> None:
        super().__init__()
        self.setObjectName("conversation_stat")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        layout.addWidget(IconBadge(icon_name, tone=tone, size=34))
        text = QVBoxLayout()
        text.setSpacing(1)
        title_label = QLabel(title)
        title_label.setObjectName("stat_title")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("stat_value")
        text.addWidget(title_label)
        text.addWidget(self.value_label)
        layout.addLayout(text, 1)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class ConversationInfoPanel(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("conversation_info")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(8)
        title = YKSectionTitle("Detalhes")
        self.layout.addWidget(title)
        self.fields: dict[str, YKInfoRow] = {}
        for key in [
            "Telefone",
            "Categoria",
            "Primeira mensagem",
            "Ultima atividade",
            "Midias",
            "Arquivos",
            "Pasta",
            "Status",
        ]:
            row = YKInfoRow(key)
            self.fields[key] = row
            self.layout.addWidget(row)
        self.layout.addStretch()

    def update_info(self, conversation: dict[str, object] | None) -> None:
        if conversation is None:
            for row in self.fields.values():
                row.set_value("-")
            return
        values = {
            "Telefone": conversation.get("sender", "-"),
            "Categoria": conversation.get("category", "-"),
            "Primeira mensagem": conversation.get("first_message", "-"),
            "Ultima atividade": conversation.get("last_activity", "-"),
            "Midias": conversation.get("media_count", "0"),
            "Arquivos": ", ".join(str(item) for item in conversation.get("generated_files", [])) or "-",
            "Pasta": conversation.get("folder", "-"),
            "Status": conversation.get("state", "-"),
        }
        for key, row in self.fields.items():
            row.set_value(str(values[key]))


class TimelineEventCard(QFrame):
    def __init__(self, event: dict[str, str]) -> None:
        super().__init__()
        self.setObjectName("timeline_event")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        layout.addWidget(IconBadge(_event_icon(event), tone=_event_tone(event), size=30))
        body = QVBoxLayout()
        body.setSpacing(2)
        content = QLabel(event.get("content", "Evento da conversa"))
        content.setObjectName("event_content")
        meta = QLabel(f"{event.get('created_at', '-')} - {event.get('status', '-')}")
        meta.setObjectName("bubble_footer")
        body.addWidget(content)
        body.addWidget(meta)
        layout.addLayout(body, 1)


class MetricCard(QFrame):
    def __init__(self, title: str, icon_name: str = "fa5s.circle", tone: str = "primary") -> None:
        super().__init__()
        self.setObjectName("metric_card")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        icon = IconBadge(icon_name, tone=tone, size=44)

        text_block = QVBoxLayout()
        text_block.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("metric_title")
        self.value_label = QLabel("-")
        self.value_label.setObjectName("metric_value")
        self.caption_label = QLabel("")
        self.caption_label.setObjectName("metric_caption")
        text_block.addWidget(title_label)
        text_block.addWidget(self.value_label)
        text_block.addWidget(self.caption_label)

        layout.addWidget(icon)
        layout.addLayout(text_block, 1)

    def update_value(self, value: str, caption: str = "") -> None:
        self.value_label.setText(value)
        self.caption_label.setText(caption)


class EmptyStateWidget(QFrame):
    def __init__(self, title: str, description: str, icon_name: str = "fa5s.info-circle") -> None:
        super().__init__()
        self.setObjectName("empty_state")
        self.setMaximumHeight(150)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(6)
        icon = IconBadge(icon_name, tone="soft", size=34)
        title_label = QLabel(title)
        title_label.setObjectName("empty_title")
        description_label = QLabel(description)
        description_label.setObjectName("empty_description")
        description_label.setWordWrap(True)
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(description_label, alignment=Qt.AlignmentFlag.AlignHCenter)


class SectionCard(QFrame):
    def __init__(self, title: str, description: str = "") -> None:
        super().__init__()
        self.setObjectName("section_card")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 14, 16, 14)
        self.layout.setSpacing(12)
        if title:
            title_label = QLabel(title)
            title_label.setObjectName("section_title")
            self.layout.addWidget(title_label)
        if description:
            description_label = QLabel(description)
            description_label.setObjectName("muted")
            description_label.setWordWrap(True)
            self.layout.addWidget(description_label)

    def add_content(self, widget: QWidget) -> None:
        self.layout.addWidget(widget)


class MediaCard(QFrame):
    def __init__(
        self,
        media: dict[str, str],
        file_path: Path | None = None,
        on_open: Callable[[Path], None] | None = None,
        on_open_folder: Callable[[Path], None] | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("media_card")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        kind = media.get("kind", "Arquivo")
        icon_name = _media_icon_name(kind)
        preview = QFrame()
        preview.setObjectName("media_preview")
        preview_layout = QHBoxLayout(preview)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_label = QLabel()
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = self._preview_pixmap(icon_name, kind, file_path)
        preview_label.setPixmap(pixmap)
        preview_layout.addWidget(preview_label)
        preview.setFixedSize(58, 42)

        body = QVBoxLayout()
        body.setSpacing(2)
        title = QLabel(media.get("final_name") or media.get("file_path") or "Arquivo")
        title.setObjectName("media_title")
        meta = QLabel(f"{media.get('date_display', media.get('date', '-'))} - {media.get('kind', 'Arquivo')}")
        meta.setObjectName("muted")
        size = QLabel(self._file_size(file_path))
        size.setObjectName("bubble_footer")
        body.addWidget(title)
        body.addWidget(meta)
        body.addWidget(size)

        status = StatusChip(media.get("status", "-"), "success")
        open_button = CompactButton("Abrir", icon_name="fa5s.play")
        folder_button = CompactButton("Abrir pasta", icon_name="fa5s.folder-open")
        can_open = file_path is not None and file_path.exists()
        open_button.setEnabled(can_open)
        folder_button.setEnabled(file_path is not None)
        if file_path is not None and on_open is not None:
            open_button.clicked.connect(lambda checked=False, path=file_path: on_open(path))
        if file_path is not None and on_open_folder is not None:
            folder_button.clicked.connect(lambda checked=False, path=file_path: on_open_folder(path))

        layout.addWidget(preview)
        layout.addLayout(body, 1)
        layout.addWidget(status)
        layout.addWidget(open_button)
        layout.addWidget(folder_button)

    def _preview_pixmap(self, icon_name: str, kind: str, file_path: Path | None) -> QPixmap:
        if file_path is not None and file_path.exists() and "imagem" in kind.lower():
            image = QPixmap(str(file_path))
            if not image.isNull():
                return image.scaled(58, 42, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        return app_icon(icon_name, "#8fd3ff").pixmap(22, 22)

    def _file_size(self, file_path: Path | None) -> str:
        if file_path is None or not file_path.exists():
            return "Tamanho indisponivel"
        size = file_path.stat().st_size
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        if size >= 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size} B"


class ConversationBubble(QFrame):
    def __init__(self, message: dict[str, str]) -> None:
        super().__init__()
        self.setObjectName("conversation_bubble")
        direction = message.get("direction", "")
        is_outbound = direction == "OUTBOUND"
        self.setProperty("direction", "outbound" if is_outbound else "inbound")

        is_media = message.get("message_type", "").lower() not in {"texto", "text"} and not is_outbound
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        header = QLabel(
            "YkMedia"
            if is_outbound
            else message.get("sender", "Contato")
        )
        header.setObjectName("bubble_header")
        content = QLabel(message.get("content", ""))
        content.setObjectName("bubble_content")
        content.setWordWrap(True)
        footer = QLabel(
            f"{message.get('created_at', '-')} - {message.get('status', '-')}"
        )
        footer.setObjectName("bubble_footer")

        show_header = str(message.get("show_header", "true")).lower() == "true"
        if is_media:
            media_row = QHBoxLayout()
            media_row.setSpacing(12)
            preview = QFrame()
            preview.setObjectName("timeline_media_preview")
            preview_layout = QHBoxLayout(preview)
            preview_layout.setContentsMargins(0, 0, 0, 0)
            icon = QLabel()
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setPixmap(app_icon(_media_icon_name(message.get("message_type", "")), "#9ed8ff").pixmap(32, 32))
            preview_layout.addWidget(icon)
            preview.setFixedSize(110, 68)

            meta = QVBoxLayout()
            title = QLabel(message.get("content", "Arquivo recebido"))
            title.setObjectName("media_title")
            details = QLabel(f"{message.get('message_type', 'Arquivo')}  -  {message.get('state', '-')}")
            details.setObjectName("muted")
            category = QLabel(message.get("status", "-"))
            category.setObjectName("timeline_badge")
            meta.addWidget(title)
            meta.addWidget(details)
            meta.addWidget(category, alignment=Qt.AlignmentFlag.AlignLeft)

            actions = QHBoxLayout()
            open_button = CompactButton("Abrir", icon_name="fa5s.play")
            folder_button = CompactButton("Abrir pasta", icon_name="fa5s.folder-open")
            open_button.setEnabled(False)
            folder_button.setEnabled(False)
            actions.addWidget(open_button)
            actions.addWidget(folder_button)
            meta.addLayout(actions)

            media_row.addWidget(preview)
            media_row.addLayout(meta, 1)
            layout.addLayout(media_row)
        else:
            if show_header:
                layout.addWidget(header)
            layout.addWidget(content)

        if message.get("error"):
            error = QLabel(message.get("error", ""))
            error.setObjectName("bubble_error")
            error.setWordWrap(True)
        else:
            error = None

        layout.addWidget(footer)
        if error is not None:
            layout.addWidget(error)


def _avatar_tone(value: str) -> str:
    tones = ("primary", "success", "warning", "danger", "teal", "violet")
    return tones[sum(ord(character) for character in value) % len(tones)]


def _rounded_pixmap(image_path: str, size: int) -> QPixmap:
    source = QPixmap(image_path)
    if source.isNull():
        return QPixmap()
    scaled = source.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, scaled)
    painter.end()
    return result


def _event_icon(event: dict[str, str]) -> str:
    content = event.get("content", "").lower()
    if "salvo" in content:
        return "fa5s.save"
    if "download" in content:
        return "fa5s.download"
    if "categoria" in content:
        return "fa5s.folder"
    return "fa5s.check-circle"


def _event_tone(event: dict[str, str]) -> str:
    status = event.get("status", "").lower()
    if "erro" in status:
        return "danger"
    if "pendente" in status:
        return "warning"
    return "success"


def _clear_layout(layout: QHBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()


def _media_icon_name(kind: str) -> str:
    normalized = kind.lower()
    if "youtube" in normalized:
        return "fa5b.youtube"
    if "video" in normalized:
        return "fa5s.video"
    if "audio" in normalized or "musica" in normalized:
        return "fa5s.music"
    if "imagem" in normalized:
        return "fa5s.image"
    if "documento" in normalized or "pdf" in normalized:
        return "fa5s.file-alt"
    return "fa5s.file"
