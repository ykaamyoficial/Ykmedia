from collections.abc import Callable
import base64
import subprocess
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QEasingCurve, QPropertyAnimation, QThread, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.desktop.components import (
    CompactButton,
    ContactListItem,
    ConversationBubble,
    ConversationInfoPanel,
    ConversationProfileHeader,
    EmptyStateWidget,
    MediaCard,
    MetricCard,
    SectionCard,
    StatusChip,
    YKButton,
    YKChip,
    YKConversationCard,
    YKIconButton,
    YKScrollArea,
    YKSearchField,
    YKStatusBadge,
    app_icon,
)
from app.desktop.data_provider import DesktopDataProvider
from app.desktop.styles import DESKTOP_STYLE
from app.services.application_factory import (
    get_automatic_setup_service,
    get_backend_runtime_manager,
    get_category_service,
    get_configuration_manager,
    get_contact_profile_service,
    get_diagnostic_service,
    get_environment_manager,
    get_evolution_client,
    get_processing_queue,
    get_storage_service,
    get_system_startup_coordinator,
)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
APP_ICON_PATH = ASSETS_DIR / "ykmedia.ico"


class SetupWorker(QObject):
    finished = Signal(object)

    def __init__(self, data_provider: DesktopDataProvider) -> None:
        super().__init__()
        self._data_provider = data_provider

    def run(self) -> None:
        self.finished.emit(self._data_provider.prepare_system_automatically())


class ContactPhotoWorker(QObject):
    finished = Signal(str, str)

    def __init__(self, data_provider: DesktopDataProvider, sender: str) -> None:
        super().__init__()
        self._data_provider = data_provider
        self._sender = sender

    def run(self) -> None:
        self.finished.emit(self._sender, self._data_provider.ensure_contact_photo_cached(self._sender))


class YkMediaMainWindow(QMainWindow):
    def __init__(self, data_provider: DesktopDataProvider | None = None) -> None:
        super().__init__()
        self.data_provider = data_provider or DesktopDataProvider(
            storage_service=get_storage_service(),
            processing_queue=get_processing_queue(),
            category_service=get_category_service(),
            evolution_client=get_evolution_client(),
            environment_manager=get_environment_manager(),
            backend_runtime_manager=get_backend_runtime_manager(),
            system_startup_coordinator=get_system_startup_coordinator(),
            diagnostic_service=get_diagnostic_service(),
            automatic_setup_service=get_automatic_setup_service(),
            configuration_manager=get_configuration_manager(),
            contact_profile_service=get_contact_profile_service(),
        )
        self.setWindowTitle("YkMedia")
        if APP_ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        self.resize(1366, 768)
        self.setMinimumSize(1180, 680)

        self._animations: list[QPropertyAnimation] = []
        self._conversation_rows: list[dict[str, object]] = []
        self._conversation_widgets: list[ContactListItem] = []
        self._conversation_filter = "Todos"
        self._conversation_details_visible = False
        self._conversation_history_visible = False
        self._setup_thread: QThread | None = None
        self._setup_worker: SetupWorker | None = None
        self._photo_threads: dict[str, QThread] = {}
        self._photo_workers: dict[str, ContactPhotoWorker] = {}
        self.pages: dict[str, QWidget] = {}
        self.nav_buttons: dict[str, QPushButton] = {}
        self.metric_cards: dict[str, MetricCard] = {}
        self.module_descriptions = {
            "Dashboard": "Visao geral do sistema",
            "Fila": "Midias aguardando processamento",
            "Historico": "Midias processadas e arquivos organizados",
            "Conversas": "Midias recebidas por pessoa",
            "Categorias": "Pastas e classificacoes de destino",
            "Configuracoes": "Preferencias e conexoes do sistema",
            "Logs": "Registros de atividades e eventos",
            "Sobre": "Informacoes do YkMedia",
        }

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_shell(), 1)
        self.setCentralWidget(root)

        self.setStyleSheet(DESKTOP_STYLE)
        self._select_page("Dashboard")
        self._startup_report_message = "Inicializacao ainda nao verificada."
        self._start_system_startup_background()
        self.refresh_all()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(1000)
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.refresh_timer.start()

    def closeEvent(self, event) -> None:
        self.refresh_timer.stop()
        self.data_provider.stop_backend_runtime()
        super().closeEvent(event)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(188)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(6)

        brand_row = QHBoxLayout()
        logo = QLabel()
        logo.setObjectName("brand_logo")
        logo.setFixedSize(40, 40)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_source = ASSETS_DIR / "ykmedia.png"
        if logo_source.exists():
            logo.setPixmap(QPixmap(str(logo_source)).scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            logo.setText("YK")
        brand_text = QVBoxLayout()
        brand = QLabel("YkMedia")
        brand.setObjectName("brand")
        subtitle = QLabel("Gerenciador de Midias")
        subtitle.setObjectName("app_subtitle")
        brand_text.addWidget(brand)
        brand_text.addWidget(subtitle)
        brand_row.addWidget(logo)
        brand_row.addLayout(brand_text)
        layout.addLayout(brand_row)
        layout.addSpacing(12)

        icon_map = {
            "Dashboard": "fa5s.th-large",
            "Fila": "fa5s.tasks",
            "Historico": "fa5s.history",
            "Conversas": "fa5s.comments",
            "Categorias": "fa5s.folder",
            "Configuracoes": "fa5s.sliders-h",
            "Logs": "fa5s.clipboard-list",
            "Sobre": "fa5s.info-circle",
        }
        for name, icon_name in icon_map.items():
            button = QPushButton(name)
            button.setIcon(app_icon(icon_name, "#aebfd1"))
            button.setObjectName("nav_button")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, page=name: self._select_page(page))
            self.nav_buttons[name] = button
            layout.addWidget(button)

        layout.addStretch()
        status_box = SectionCard("", "")
        status_box.layout.setContentsMargins(12, 10, 12, 10)
        self.sidebar_system = StatusChip("Sistema online", "success")
        self.sidebar_evolution = StatusChip("WhatsApp nao verificado", "neutral")
        self.sidebar_worker = StatusChip("Worker ativo", "success")
        self.sidebar_sqlite = StatusChip("SQLite local", "neutral")
        status_box.add_content(self.sidebar_system)
        status_box.add_content(self.sidebar_evolution)
        status_box.add_content(self.sidebar_worker)
        status_box.add_content(self.sidebar_sqlite)
        layout.addWidget(status_box)
        version = QLabel("v0.1.0")
        version.setObjectName("muted")
        layout.addWidget(version)
        return sidebar

    def _build_shell(self) -> QWidget:
        shell = QWidget()
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(10)
        layout.addWidget(self._build_header())

        self.content_stack = QStackedWidget()
        self.pages["Dashboard"] = self._build_dashboard_page()
        self.pages["Fila"] = self._build_queue_page()
        self.pages["Historico"] = self._build_history_page()
        self.pages["Conversas"] = self._build_conversations_page()
        self.pages["Categorias"] = self._build_categories_page()
        self.pages["Configuracoes"] = self._build_settings_page()
        self.pages["Logs"] = self._build_logs_page()
        self.pages["Sobre"] = self._build_about_page()
        for page in self.pages.values():
            self.content_stack.addWidget(page)
        layout.addWidget(self.content_stack, 1)
        return shell

    def _build_header(self) -> QWidget:
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        self.header_title = QLabel("Dashboard")
        self.header_title.setObjectName("header_title")
        self.header_description = QLabel(self.module_descriptions["Dashboard"])
        self.header_description.setObjectName("muted")
        title_block.addWidget(self.header_title)
        title_block.addWidget(self.header_description)
        layout.addLayout(title_block)
        layout.addStretch()

        refresh_button = CompactButton("Atualizar", icon_name="fa5s.sync-alt")
        refresh_button.clicked.connect(self.refresh_all)
        self.open_media_button = CompactButton("Abrir midias", icon_name="fa5s.folder-open")
        self.open_media_button.clicked.connect(self._open_media_root)
        layout.addWidget(refresh_button)
        layout.addWidget(self.open_media_button)

        self.header_indicators: dict[str, StatusChip] = {
            "system": StatusChip("Sistema online", "success"),
            "evolution": StatusChip("WhatsApp nao verificado", "neutral"),
            "worker": StatusChip("Worker ativo", "success"),
            "sqlite": StatusChip("SQLite local", "neutral"),
        }
        for chip in self.header_indicators.values():
            layout.addWidget(chip)
        return header

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        cards = QGridLayout()
        cards.setSpacing(12)
        definitions = [
            ("system_status", "Sistema", "fa5s.server", "success"),
            ("evolution_status", "WhatsApp", "fa5b.whatsapp", "success"),
            ("worker_status", "Worker", "fa5s.cogs", "primary"),
            ("pending_jobs", "Na fila", "fa5s.stream", "warning"),
            ("completed_jobs", "Concluidas", "fa5s.check-circle", "success"),
            ("error_jobs", "Erros", "fa5s.exclamation-triangle", "danger"),
        ]
        for index, (key, title, icon, tone) in enumerate(definitions):
            card = MetricCard(title, icon, tone)
            self.metric_cards[key] = card
            cards.addWidget(card, index // 3, index % 3)
        layout.addLayout(cards)

        body = QHBoxLayout()
        activity = SectionCard("Atividade nas ultimas 24 horas")
        self.dashboard_empty = EmptyStateWidget(
            "Nenhuma atividade registrada ainda.",
            "Quando novas midias chegarem pelo WhatsApp, o resumo aparecera aqui.",
        )
        activity.add_content(self.dashboard_empty)
        summary = SectionCard("Resumo operacional")
        self.dashboard_summary = QLabel("")
        self.dashboard_summary.setObjectName("muted")
        self.dashboard_summary.setWordWrap(True)
        summary.add_content(self.dashboard_summary)
        body.addWidget(activity, 2)
        body.addWidget(summary, 1)
        layout.addLayout(body, 1)
        return page

    def _build_queue_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        toolbar = self._toolbar()
        self.queue_search = QLineEdit()
        self.queue_search.setPlaceholderText("Buscar por remetente, arquivo ou tipo...")
        self.queue_search.textChanged.connect(self.refresh_queue)
        self.queue_filter = QComboBox()
        self.queue_filter.addItems(["Todos", "PENDENTE", "PROCESSANDO", "CONCLUIDO", "ERRO"])
        self.queue_filter.currentTextChanged.connect(self.refresh_queue)
        refresh = CompactButton("Atualizar", "primary", "fa5s.sync-alt")
        refresh.clicked.connect(self.refresh_queue)
        clear = CompactButton("Limpar concluidos", "danger", "fa5s.trash-alt")
        clear.clicked.connect(self._clear_completed_jobs)
        toolbar.addWidget(self.queue_search, 2)
        toolbar.addWidget(QLabel("Status"))
        toolbar.addWidget(self.queue_filter)
        toolbar.addStretch()
        toolbar.addWidget(refresh)
        toolbar.addWidget(clear)
        layout.addLayout(toolbar)
        self.queue_table = self._create_table(["Remetente", "Origem", "Arquivo", "Tipo", "Status", "Recebido em", "ID"])
        layout.addWidget(self.queue_table)
        self.queue_empty = EmptyStateWidget(
            "Fila vazia.",
            "Quando uma midia ou link entrar para processamento, o job aparecera aqui.",
            "fa5s.tasks",
        )
        layout.addWidget(self.queue_empty)
        layout.addStretch(1)
        return page

    def _build_history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        toolbar = self._toolbar()
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("Buscar por nome, remetente ou categoria...")
        self.history_search.textChanged.connect(self.refresh_history)
        self.history_filter = QComboBox()
        self.history_filter.addItems(["Todos", "Louvores", "Mensagens", "Jovens", "Criancas", "Outros"])
        self.history_filter.currentTextChanged.connect(self.refresh_history)
        self.history_origin_filter = QComboBox()
        self.history_origin_filter.addItems(["Todas", "WhatsApp", "YouTube"])
        self.history_origin_filter.currentTextChanged.connect(self.refresh_history)
        self.pagination_label = QLabel("0 registros")
        refresh = CompactButton("Atualizar", "primary", "fa5s.sync-alt")
        refresh.clicked.connect(self.refresh_history)
        toolbar.addWidget(self.history_search, 2)
        toolbar.addWidget(QLabel("Categoria"))
        toolbar.addWidget(self.history_filter)
        toolbar.addWidget(QLabel("Origem"))
        toolbar.addWidget(self.history_origin_filter)
        toolbar.addWidget(refresh)
        toolbar.addWidget(self.pagination_label)
        layout.addLayout(toolbar)
        self.history_table = self._create_table(["Data", "Remetente", "Origem", "Categoria", "Nome final", "Tipo", "Status"])
        layout.addWidget(self.history_table)
        self.history_empty = EmptyStateWidget(
            "Nenhuma midia processada ainda.",
            "Os arquivos organizados aparecerao aqui apos o primeiro fluxo concluido.",
        )
        layout.addWidget(self.history_empty)
        return page

    def _build_conversations_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setSpacing(8)
        left = SectionCard("Conversas", "Arquivos por remetente")
        left.layout.setContentsMargins(8, 8, 8, 8)
        self.conversation_search = YKSearchField("Pesquisar pessoas ou arquivos...")
        self.conversation_search.textChanged.connect(self.refresh_conversations)
        search_row = QHBoxLayout()
        search_row.setSpacing(4)
        search_row.addWidget(self.conversation_search, 1)
        filter_icon = YKIconButton("fa5s.filter", "Filtros")
        search_row.addWidget(filter_icon)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(4)
        self.conversation_filter_buttons: dict[str, QPushButton] = {}
        for label in ["Todos", "Imagens", "Videos"]:
            button = YKChip(label)
            button.clicked.connect(lambda checked=False, value=label: self._set_conversation_filter(value))
            self.conversation_filter_buttons[label] = button
            filter_row.addWidget(button)
        self.conversation_filter_buttons["Todos"].setChecked(True)

        filter_row_2 = QHBoxLayout()
        filter_row_2.setSpacing(4)
        for label in ["Audios", "Documentos", "YouTube"]:
            button = YKChip(label)
            button.clicked.connect(lambda checked=False, value=label: self._set_conversation_filter(value))
            self.conversation_filter_buttons[label] = button
            filter_row_2.addWidget(button)

        self.conversations_list = QListWidget()
        self.conversations_list.currentRowChanged.connect(self._show_conversation_details)
        search_widget = QWidget()
        search_widget.setLayout(search_row)
        filter_widget = QWidget()
        filter_widget.setLayout(filter_row)
        filter_widget_2 = QWidget()
        filter_widget_2.setLayout(filter_row_2)
        left.add_content(search_widget)
        left.add_content(filter_widget)
        left.add_content(filter_widget_2)
        left.add_content(self.conversations_list)
        left.setFixedWidth(300)

        right = SectionCard("", "")
        right.layout.setContentsMargins(0, 0, 0, 0)
        right.layout.setSpacing(0)
        self.conversation_header = QLabel("")
        self.conversation_header.hide()
        self.conversation_profile = ConversationProfileHeader()
        self.conversation_badges: dict[str, YKStatusBadge] = {
            "files": YKStatusBadge("Arquivos: 0", "neutral"),
            "last": YKStatusBadge("Ultimo: -", "primary"),
            "status": YKStatusBadge("Status: -", "success"),
        }
        badges_row = QHBoxLayout()
        badges_row.setContentsMargins(12, 6, 12, 6)
        badges_row.setSpacing(6)
        for badge in self.conversation_badges.values():
            badges_row.addWidget(badge)
        badges_row.addStretch()
        self.conversation_history_button = YKButton("Mostrar historico da conversa", icon_name="fa5s.comments")
        self.conversation_history_button.clicked.connect(self._toggle_conversation_history)
        self.conversation_details_button = YKButton("Mostrar detalhes", icon_name="fa5s.info-circle")
        self.conversation_details_button.clicked.connect(self._toggle_conversation_details)
        badges_row.addWidget(self.conversation_history_button)
        badges_row.addWidget(self.conversation_details_button)
        badges_widget = QWidget()
        badges_widget.setLayout(badges_row)

        conversation_body = QHBoxLayout()
        conversation_body.setContentsMargins(8, 0, 8, 8)
        conversation_body.setSpacing(8)
        self.media_scroll = YKScrollArea()
        self.media_container = QWidget()
        self.media_layout = QVBoxLayout(self.media_container)
        self.media_layout.setContentsMargins(0, 0, 4, 0)
        self.media_layout.setSpacing(8)
        self.media_scroll.setWidget(self.media_container)
        self.conversation_info = ConversationInfoPanel()
        self.conversation_info.setFixedWidth(220)
        self.conversation_info.hide()
        self.conversation_history_panel = SectionCard("Historico", "Mensagens ocultas da conversa")
        self.conversation_history_panel.setFixedWidth(280)
        self.conversation_history_panel.hide()
        self.conversation_history_scroll = YKScrollArea()
        self.conversation_history_container = QWidget()
        self.conversation_history_layout = QVBoxLayout(self.conversation_history_container)
        self.conversation_history_layout.setContentsMargins(0, 0, 0, 0)
        self.conversation_history_layout.setSpacing(6)
        self.conversation_history_scroll.setWidget(self.conversation_history_container)
        self.conversation_history_panel.add_content(self.conversation_history_scroll)
        conversation_body.addWidget(self.media_scroll, 1)
        conversation_body.addWidget(self.conversation_history_panel)
        conversation_body.addWidget(self.conversation_info)
        conversation_body_widget = QWidget()
        conversation_body_widget.setLayout(conversation_body)
        right.add_content(self.conversation_profile)
        right.add_content(badges_widget)
        right.add_content(conversation_body_widget)
        layout.addWidget(left)
        layout.addWidget(right, 1)
        return page

    def _build_categories_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        actions = self._toolbar()
        add = CompactButton("Nova categoria", "primary", "fa5s.plus")
        edit = CompactButton("Editar", icon_name="fa5s.pen")
        remove = CompactButton("Excluir", "danger", "fa5s.trash-alt")
        up = CompactButton("Mover acima", icon_name="fa5s.arrow-up")
        down = CompactButton("Mover abaixo", icon_name="fa5s.arrow-down")
        for button, handler in [
            (add, self._add_category),
            (edit, self._edit_selected_category),
            (remove, self._remove_selected_category),
            (up, self._move_category_up),
            (down, self._move_category_down),
        ]:
            button.clicked.connect(handler)
            actions.addWidget(button)
        actions.addStretch()
        self.category_input = QLineEdit()
        self.category_input.hide()
        layout.addLayout(actions)
        self.categories_table = self._create_table(["Posicao", "Categoria", "Pasta correspondente"])
        layout.addWidget(self.categories_table)
        self.categories_list = QListWidget()
        self.categories_list.hide()
        layout.addWidget(self.categories_list)
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setSpacing(14)
        self.settings_nav = QListWidget()
        self.settings_nav.setFixedWidth(220)
        settings_items = [
            ("Pastas", "fa5s.folder-open"),
            ("WhatsApp", "fa5b.whatsapp"),
            ("Downloads", "fa5s.download"),
            ("Atualizacoes", "fa5s.sync-alt"),
            ("Tema", "fa5s.moon"),
            ("Idioma", "fa5s.globe-americas"),
            ("Backup", "fa5s.archive"),
            ("Sistema", "fa5s.shield-alt"),
            ("Avancado", "fa5s.user-shield"),
        ]
        for label, icon_name in settings_items:
            item = QListWidgetItem(app_icon(icon_name, "#9fb7cf"), label)
            self.settings_nav.addItem(item)
        self.settings_stack = QStackedWidget()
        self.settings_nav.currentRowChanged.connect(self.settings_stack.setCurrentIndex)

        self.environment_input = QLineEdit("development")
        self.environment_status_label = QLabel("Nao verificado")
        self.downloads_root_input = QLineEdit()
        self.ffmpeg_path_input = QLineEdit()
        self.sqlite_database_input = QLineEdit()
        self.youtube_temp_input = QLineEdit()
        self.whatsapp_instance_input = QLineEdit("ykmedia")
        self.evolution_state_label = QLabel("Desconhecida")
        self.evolution_qrcode_label = QLabel("Clique em Gerar QR Code para conectar uma nova sessao.")
        self.evolution_qrcode_label.setObjectName("qr_placeholder")
        self.evolution_qrcode_label.setFixedSize(240, 240)
        self.evolution_qrcode_label.setWordWrap(True)
        self.evolution_qrcode_label.setScaledContents(True)

        self.settings_stack.addWidget(self._settings_form("Pastas", [("Pasta das midias", self.downloads_root_input)], [(CompactButton("Escolher pasta", "primary", "fa5s.folder"), self._choose_downloads_root), (CompactButton("Abrir pasta", icon_name="fa5s.folder-open"), self._open_media_root)]))
        self.settings_stack.addWidget(self._settings_form("WhatsApp", [("Status", self.evolution_state_label)], [(CompactButton("Verificar", icon_name="fa5s.search"), self._refresh_evolution_session), (CompactButton("Conectar WhatsApp", "primary", "fa5s.qrcode"), self._connect_evolution_session), (CompactButton("Desconectar", "danger", "fa5s.power-off"), self._disconnect_evolution_session)], self.evolution_qrcode_label))
        self.settings_stack.addWidget(self._simple_settings_page("Downloads", "Downloads automaticos de midias e links estao ativos. O YkMedia prepara os componentes necessarios pelo botao Sistema."))
        self.settings_stack.addWidget(self._simple_settings_page("Atualizacoes", "Estrutura reservada para atualizacoes automaticas futuras."))
        self.settings_stack.addWidget(self._simple_settings_page("Tema", "Tema escuro premium ativo. Outras opcoes serao adicionadas futuramente."))
        self.settings_stack.addWidget(self._simple_settings_page("Idioma", "Portugues do Brasil ativo. Estrutura preparada para idiomas futuros."))
        self.settings_stack.addWidget(self._simple_settings_page("Backup", "Estrutura preparada para backup e restauracao das configuracoes."))
        self.settings_stack.addWidget(self._build_system_settings_page())
        self.settings_stack.addWidget(self._build_advanced_settings_page())
        self.settings_nav.setCurrentRow(7)
        layout.addWidget(self.settings_nav)
        layout.addWidget(self.settings_stack, 1)
        return page

    def _simple_settings_page(self, title: str, description: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        card = SectionCard(title, description)
        card.add_content(StatusChip("Configuracao automatica", "success"))
        layout.addWidget(card)
        layout.addStretch()
        return page

    def _build_system_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        card = SectionCard("Sistema", "Tudo que o usuario precisa saber: funcionando ou corrigir.")
        actions = self._toolbar()
        prepare = CompactButton("Preparar Sistema Automaticamente", "primary", "fa5s.magic")
        wizard = CompactButton("Abrir assistente", icon_name="fa5s.route")
        verify = CompactButton("Executar Diagnostico", icon_name="fa5s.search")
        prepare.clicked.connect(self._prepare_system_automatically)
        wizard.clicked.connect(self._open_setup_wizard)
        verify.clicked.connect(self._run_diagnostics)
        for button in [prepare, wizard, verify]:
            actions.addWidget(button)
        actions.addStretch()
        card.layout.addLayout(actions)

        self.system_status_summary = QLabel("Clique em Preparar Sistema Automaticamente para verificar e corrigir tudo.")
        self.system_status_summary.setObjectName("muted")
        self.system_status_summary.setWordWrap(True)
        card.add_content(self.system_status_summary)

        self.system_status_table = self._create_table(["Item", "Status", "Mensagem"])
        card.add_content(self.system_status_table)
        layout.addWidget(card)
        layout.addStretch()
        self.diagnostics_summary = self.system_status_summary
        self.diagnostics_table = self.system_status_table
        return page

    def _build_advanced_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        warning = SectionCard("Avancado", "Area tecnica. Use apenas se souber exatamente o que esta fazendo.")
        masked_api_key = QLabel("Oculta por seguranca")
        masked_secret = QLabel("Oculto por seguranca")
        backend_port = QLabel("8010")
        webhook = QLabel("Configurado automaticamente")
        docker = QLabel("Gerenciado automaticamente")
        for label in [masked_api_key, masked_secret, backend_port, webhook, docker]:
            label.setObjectName("muted")
        form = QFormLayout()
        form.addRow("API Key", masked_api_key)
        form.addRow("Webhook Secret", masked_secret)
        form.addRow("Porta backend", backend_port)
        form.addRow("Webhook", webhook)
        form.addRow("Docker", docker)
        form.addRow("SQLite", self.sqlite_database_input)
        form.addRow("Instancia", self.whatsapp_instance_input)
        form.addRow("FFmpeg", self.ffmpeg_path_input)
        warning.layout.addLayout(form)
        layout.addWidget(warning)
        layout.addStretch()
        return page

    def _build_diagnostics_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        card = SectionCard("Central de Diagnostico", "Verificacao operacional do YkMedia.")
        actions = self._toolbar()
        verify = CompactButton("Verificar tudo", "primary", "fa5s.search")
        fix = CompactButton("Corrigir automaticamente", icon_name="fa5s.magic")
        restart = CompactButton("Reiniciar backend", icon_name="fa5s.redo")
        logs = CompactButton("Abrir logs", icon_name="fa5s.folder-open")
        verify.clicked.connect(self._run_diagnostics)
        fix.clicked.connect(self._auto_fix_diagnostics)
        restart.clicked.connect(self._restart_backend_diagnostics)
        logs.clicked.connect(self._open_logs_directory)
        for button in [verify, fix, restart, logs]:
            actions.addWidget(button)
        actions.addStretch()
        self.diagnostics_summary = QLabel("Diagnostico ainda nao executado.")
        self.diagnostics_summary.setObjectName("muted")
        self.diagnostics_summary.setWordWrap(True)
        self.diagnostics_table = self._create_table(["Componente", "Status", "Mensagem"])
        card.layout.addLayout(actions)
        card.add_content(self.diagnostics_summary)
        card.add_content(self.diagnostics_table)
        layout.addWidget(card)
        return page

    def _build_logs_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        toolbar = self._toolbar()
        self.logs_search = QLineEdit()
        self.logs_search.setPlaceholderText("Buscar nos logs...")
        self.logs_search.textChanged.connect(self.refresh_logs)
        self.logs_filter = QComboBox()
        self.logs_filter.addItems(["Todos", "INFO", "WARNING", "ERROR", "DEBUG"])
        self.logs_filter.currentTextChanged.connect(self.refresh_logs)
        refresh = CompactButton("Atualizar", "primary", "fa5s.sync-alt")
        refresh.clicked.connect(self.refresh_logs)
        export = CompactButton("Exportar", icon_name="fa5s.download")
        export.clicked.connect(self._export_logs)
        open_logs = CompactButton("Abrir pasta", icon_name="fa5s.folder-open")
        open_logs.clicked.connect(self._open_logs_directory)
        toolbar.addWidget(self.logs_search, 2)
        toolbar.addWidget(QLabel("Nivel"))
        toolbar.addWidget(self.logs_filter)
        toolbar.addWidget(refresh)
        toolbar.addWidget(export)
        toolbar.addWidget(open_logs)
        layout.addLayout(toolbar)
        self.logs_table = self._create_table(["Data e hora", "Nivel", "Origem", "Mensagem"])
        self.logs_table.itemDoubleClicked.connect(lambda item: self._show_info("Log", item.text()))
        layout.addWidget(self.logs_table)
        self.logs_empty = EmptyStateWidget(
            "Nenhum log encontrado.",
            "Os eventos do sistema aparecem aqui quando houver atividade registrada.",
            "fa5s.clipboard-list",
        )
        layout.addWidget(self.logs_empty)
        layout.addStretch(1)
        return page

    def _build_about_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addStretch()
        card = SectionCard("YkMedia", "Gerenciador de midias para sonoplastia via WhatsApp.")
        info = QLabel(
            "Versao: 0.1.0\n"
            f"Banco SQLite: {self.data_provider.sqlite_database_path()}\n"
            f"Pasta de midias: {self.data_provider.media_root_path()}\n"
            f"Instalacao: {Path.cwd()}"
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        actions = self._toolbar()
        open_folder = CompactButton("Abrir pasta", icon_name="fa5s.folder-open")
        open_folder.clicked.connect(lambda: self._open_path(Path.cwd()))
        copy_info = CompactButton("Copiar informacoes", icon_name="fa5s.copy")
        copy_info.clicked.connect(lambda: QApplication.clipboard().setText(info.text()))
        actions.addWidget(open_folder)
        actions.addWidget(copy_info)
        actions.addStretch()
        action_widget = QWidget()
        action_widget.setLayout(actions)
        card.add_content(info)
        card.add_content(StatusChip("Sistema online", "success"))
        card.add_content(action_widget)
        card.setMaximumWidth(680)
        layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        return page

    def refresh_all(self) -> None:
        self.refresh_dashboard()
        self.refresh_queue()
        self.refresh_history()
        self.refresh_conversations()
        self.refresh_categories()
        self.refresh_settings()
        self.refresh_logs()

    def refresh_dashboard(self) -> None:
        snapshot = self.data_provider.get_dashboard_snapshot()
        backend_status = self._friendly_backend_state(snapshot.system_status)
        values = {
            "system_status": (backend_status, "API local do YkMedia"),
            "evolution_status": (self._friendly_evolution_state(snapshot.evolution_status), "Conexao do WhatsApp"),
            "worker_status": (snapshot.worker_status, "Processamento local"),
            "pending_jobs": (str(snapshot.pending_jobs), "Aguardando processamento"),
            "completed_jobs": (str(snapshot.completed_jobs), "Total concluido"),
            "error_jobs": (str(snapshot.error_jobs), "Requer atencao"),
        }
        for key, (value, caption) in values.items():
            self.metric_cards[key].update_value(value, caption)
        self._update_status_chips(snapshot.evolution_status)
        self._update_system_status_chip(backend_status, snapshot.system_status)
        self.dashboard_summary.setText(
            f"Pendentes: {snapshot.pending_jobs}\n"
            f"Processando: {snapshot.processing_jobs}\n"
            f"Concluidos: {snapshot.completed_jobs}\n"
            f"Erros: {snapshot.error_jobs}\n"
            f"Backend: {backend_status}\n"
            f"Inicializacao: {self._startup_report_message}\n"
            f"Pasta de midias: {self.data_provider.media_root_path()}"
        )

    def _start_system_startup_background(self) -> None:
        thread = threading.Thread(
            target=self._prepare_system_startup,
            name="YkMediaSystemStartup",
            daemon=True,
        )
        thread.start()

    def _prepare_system_startup(self) -> None:
        report = self.data_provider.prepare_system_startup()
        if report is None:
            self.data_provider.start_backend_runtime()
            self._startup_report_message = "Backend verificado."
            return

        self._startup_report_message = report.message

    def refresh_queue(self) -> None:
        rows = self.data_provider.list_jobs()
        query = self.queue_search.text().strip().lower()
        status = self.queue_filter.currentText()
        if query:
            rows = [row for row in rows if query in " ".join(str(value) for value in row.values()).lower()]
        if status != "Todos":
            rows = [row for row in rows if row["status"] == status]
        self._fill_table(self.queue_table, rows, ["sender", "origin", "file", "kind", "status", "created_at", "id"])
        self.queue_empty.setVisible(len(rows) == 0)
        self.queue_table.setVisible(len(rows) > 0)

    def refresh_history(self) -> None:
        rows = self.data_provider.list_history(self.history_search.text())
        category = self.history_filter.currentText()
        origin = self.history_origin_filter.currentText()
        if category != "Todos":
            rows = [row for row in rows if row["category"] == category]
        if origin != "Todas":
            rows = [row for row in rows if row["origin"] == origin]
        self.pagination_label.setText(f"{len(rows)} registros")
        self._fill_table(self.history_table, rows, ["date_display", "sender", "origin", "category", "final_name", "kind", "status"])
        self.history_empty.setVisible(len(rows) == 0)
        self.history_table.setVisible(len(rows) > 0)

    def refresh_conversations(self) -> None:
        current_row = max(self.conversations_list.currentRow(), 0)
        rows = self.data_provider.list_media_conversations(self.conversation_search.text())
        if self._conversation_filter != "Todos":
            rows = [row for row in rows if self._conversation_has_kind(row, self._conversation_filter)]
        self._conversation_rows = rows
        self._conversation_widgets = []
        self.conversations_list.blockSignals(True)
        self.conversations_list.clear()
        for conversation in self._conversation_rows:
            self._request_contact_photo(conversation)
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 58))
            self.conversations_list.addItem(item)
            widget = YKConversationCard(conversation)
            self._conversation_widgets.append(widget)
            self.conversations_list.setItemWidget(item, widget)
        if self._conversation_rows:
            self.conversations_list.setCurrentRow(min(current_row, len(self._conversation_rows) - 1))
        self.conversations_list.blockSignals(False)
        self._show_conversation_details(self.conversations_list.currentRow())

    def _request_contact_photo(self, conversation: dict[str, object]) -> None:
        sender = str(conversation.get("sender_raw", ""))
        if (
            not sender
            or not self.data_provider.can_load_contact_photos()
            or conversation.get("profile_photo_path")
            or sender in self._photo_threads
        ):
            return
        thread = QThread(self)
        worker = ContactPhotoWorker(self.data_provider, sender)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._contact_photo_loaded)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda sender_key=sender: self._clear_contact_photo_worker(sender_key))
        self._photo_threads[sender] = thread
        self._photo_workers[sender] = worker
        thread.start()

    def _contact_photo_loaded(self, sender: str, path: str) -> None:
        if path:
            self.refresh_conversations()

    def _clear_contact_photo_worker(self, sender: str) -> None:
        self._photo_threads.pop(sender, None)
        self._photo_workers.pop(sender, None)

    def _set_conversation_filter(self, value: str) -> None:
        self._conversation_filter = value
        for label, button in self.conversation_filter_buttons.items():
            button.setChecked(label == value)
        self.refresh_conversations()

    def refresh_categories(self) -> None:
        categories = self.data_provider.get_settings_snapshot().categories
        self.categories_list.clear()
        self.categories_list.addItems(categories)
        self.categories_table.setRowCount(len(categories))
        for index, category in enumerate(categories):
            self.categories_table.setItem(index, 0, QTableWidgetItem(str(index + 1)))
            self.categories_table.setItem(index, 1, QTableWidgetItem(category))
            self.categories_table.setItem(index, 2, QTableWidgetItem(str(self.data_provider.media_root_path() / category)))
        self._refresh_history_categories_filter(categories)

    def refresh_settings(self) -> None:
        snapshot = self.data_provider.get_settings_snapshot()
        if not self.downloads_root_input.text():
            self.downloads_root_input.setText(snapshot.downloads_root)
        if not self.sqlite_database_input.text():
            self.sqlite_database_input.setText(snapshot.sqlite_database)
        if not self.ffmpeg_path_input.text():
            self.ffmpeg_path_input.setText(snapshot.ffmpeg_path)
        if not self.youtube_temp_input.text():
            self.youtube_temp_input.setText("downloads/youtube")
        self._refresh_evolution_session(show_message=False)

    def refresh_logs(self) -> None:
        rows = self.data_provider.list_logs(self.logs_search.text(), self.logs_filter.currentText())
        for row in rows:
            row.setdefault("source", self._source_from_log(row.get("message", "")))
        self._fill_table(self.logs_table, rows, ["date", "level", "source", "message"])
        self.logs_empty.setVisible(len(rows) == 0)
        self.logs_table.setVisible(len(rows) > 0)

    def _show_conversation_details(self, row: int) -> None:
        self._sync_conversation_selection(row)
        self._clear_layout(self.media_layout)
        self._clear_layout(self.conversation_history_layout)
        if row < 0 or row >= len(self._conversation_rows):
            self.conversation_header.setText("Selecione uma pessoa para visualizar os arquivos.")
            self.conversation_profile.update_contact(None)
            self._update_conversation_badges(None)
            self.conversation_info.update_info(None)
            self.media_layout.addSpacing(8)
            self.media_layout.addWidget(EmptyStateWidget("Nenhum remetente selecionado.", "Selecione uma pessoa para ver os arquivos recebidos.", "fa5s.folder-open"))
            self.media_layout.addStretch()
            return
        conversation = self._conversation_rows[row]
        self.conversation_header.setText(
            f"{conversation['sender']} - {conversation['media_count']} arquivo(s)"
        )
        self.conversation_profile.update_contact(conversation)
        self._update_conversation_badges(conversation)
        self.conversation_info.update_info(conversation)
        sender_raw = str(conversation["sender_raw"])
        items = [item for item in conversation.get("items", []) if isinstance(item, dict)]
        self._render_conversation_history(sender_raw)
        if not items:
            self.media_layout.addSpacing(8)
            self.media_layout.addWidget(EmptyStateWidget("Nenhum arquivo encontrado.", "As mensagens de texto ficam ocultas; esta area mostra apenas midias processadas.", "fa5s.folder-open"))
        else:
            grid_widget = QWidget()
            grid = QGridLayout(grid_widget)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setSpacing(8)
            columns = self._media_gallery_columns()
            for index, media in enumerate(items):
                file_path = self.data_provider.resolve_media_file_path(str(media.get("file_path", "")))
                card = MediaCard(media, file_path, self._open_file, self._open_containing_folder)
                grid.addWidget(card, index // columns, index % columns)
            self.media_layout.addWidget(grid_widget)
        self.media_layout.addStretch()

    def _render_conversation_history(self, sender_raw: str) -> None:
        messages = self.data_provider.list_conversation_timeline(sender_raw)
        for message in messages:
            if message.get("direction") == "EVENT":
                continue
            bubble = ConversationBubble(message)
            bubble.setMaximumWidth(240)
            self.conversation_history_layout.addWidget(bubble)
        self.conversation_history_layout.addStretch()

    def _toggle_conversation_details(self) -> None:
        self._conversation_details_visible = not self._conversation_details_visible
        self.conversation_info.setVisible(self._conversation_details_visible)
        self.conversation_details_button.setText(
            "Ocultar detalhes" if self._conversation_details_visible else "Mostrar detalhes"
        )

    def _toggle_conversation_history(self) -> None:
        self._conversation_history_visible = not self._conversation_history_visible
        self.conversation_history_panel.setVisible(self._conversation_history_visible)
        self.conversation_history_button.setText(
            "Ocultar historico" if self._conversation_history_visible else "Mostrar historico da conversa"
        )

    def _conversation_has_kind(self, conversation: dict[str, object], filter_name: str) -> bool:
        kind_map = {
            "Imagens": "imagem",
            "Videos": "video",
            "Audios": "audio",
            "Documentos": "documento",
            "YouTube": "youtube",
        }
        expected = kind_map.get(filter_name, "").lower()
        items = conversation.get("items", [])
        return isinstance(items, list) and any(expected in str(item.get("kind", "")).lower() for item in items if isinstance(item, dict))

    def _media_gallery_columns(self) -> int:
        width = max(1, self.media_scroll.viewport().width())
        return max(1, min(5, width // 290))

    def _sync_conversation_selection(self, selected_row: int) -> None:
        for index, widget in enumerate(self._conversation_widgets):
            widget.setProperty("selected", index == selected_row)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def _update_conversation_badges(self, conversation: dict[str, object] | None) -> None:
        if conversation is None:
            values = {
                "files": "Arquivos: 0",
                "last": "Ultimo: -",
                "status": "Status: -",
            }
        else:
            values = {
                "files": f"Arquivos: {conversation.get('media_count', '0')}",
                "last": f"Ultimo: {conversation.get('last_media', '-')}",
                "status": "Status: Processado",
            }
        for key, value in values.items():
            self.conversation_badges[key].set_text(value)

    def _settings_form(
        self,
        title: str,
        fields: list[tuple[str, QWidget]],
        actions: list[tuple[QPushButton, Callable[[], None]]],
        extra: QWidget | None = None,
    ) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        card = SectionCard(title)
        form = QFormLayout()
        for label, widget in fields:
            form.addRow(label, widget)
        card.layout.addLayout(form)
        if extra is not None:
            card.add_content(extra)
        action_row = self._toolbar()
        for button, handler in actions:
            button.clicked.connect(handler)
            action_row.addWidget(button)
        action_row.addStretch()
        card.layout.addLayout(action_row)
        layout.addWidget(card)
        layout.addStretch()
        return page

    def _select_page(self, name: str) -> None:
        for page_name, button in self.nav_buttons.items():
            button.setChecked(page_name == name)
        self.header_title.setText(name)
        self.header_description.setText(self.module_descriptions[name])
        self.open_media_button.setVisible(name in {"Dashboard", "Historico", "Conversas", "Configuracoes", "Sobre"})
        self.content_stack.setCurrentWidget(self.pages[name])
        self._fade_current_page()

    def _fade_current_page(self) -> None:
        effect = QGraphicsOpacityEffect(self.content_stack.currentWidget())
        self.content_stack.currentWidget().setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(120)
        animation.setStartValue(0.8)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        self._animations.append(animation)

    def _clear_completed_jobs(self) -> None:
        deleted = self.data_provider.clear_completed_jobs()
        self.refresh_queue()
        self.refresh_dashboard()
        self._show_info("Fila", f"{deleted} trabalho(s) concluido(s) removido(s).")

    def _add_category(self) -> None:
        preset = self.category_input.text().strip()
        if preset:
            category, ok = preset, True
            self.category_input.clear()
        else:
            category, ok = QInputDialog.getText(self, "Nova categoria", "Nome da categoria:")
        if ok and category.strip():
            self.categories_list.addItem(category.strip())
            self._save_categories_from_list()
            self.refresh_categories()

    def _edit_selected_category(self) -> None:
        row = self.categories_table.currentRow()
        if row < 0:
            return
        current = self.categories_table.item(row, 1).text()
        category, ok = QInputDialog.getText(self, "Editar categoria", "Nome da categoria:", text=current)
        if ok and category.strip():
            self.categories_list.item(row).setText(category.strip())
            self._save_categories_from_list()
            self.refresh_categories()

    def _remove_selected_category(self) -> None:
        row = self.categories_table.currentRow()
        if row < 0:
            return
        if QMessageBox.question(self, "Excluir categoria", "Deseja excluir esta categoria?") != QMessageBox.StandardButton.Yes:
            return
        self.categories_list.takeItem(row)
        self._save_categories_from_list()
        self.refresh_categories()

    def _move_category_up(self) -> None:
        self._move_selected_category(-1)

    def _move_category_down(self) -> None:
        self._move_selected_category(1)

    def _move_selected_category(self, direction: int) -> None:
        row = self.categories_table.currentRow()
        target = row + direction
        if row < 0 or target < 0 or target >= self.categories_list.count():
            return
        item = self.categories_list.takeItem(row)
        self.categories_list.insertItem(target, item)
        self._save_categories_from_list()
        self.refresh_categories()
        self.categories_table.selectRow(target)

    def _save_categories_from_list(self) -> None:
        categories = [self.categories_list.item(index).text() for index in range(self.categories_list.count())]
        snapshot = self.data_provider.get_settings_snapshot()
        self.data_provider.update_settings(snapshot.downloads_root, snapshot.ffmpeg_path, snapshot.sqlite_database, categories)

    def _refresh_history_categories_filter(self, categories: list[str]) -> None:
        current = self.history_filter.currentText()
        self.history_filter.blockSignals(True)
        self.history_filter.clear()
        self.history_filter.addItem("Todos")
        self.history_filter.addItems(categories)
        index = self.history_filter.findText(current)
        self.history_filter.setCurrentIndex(index if index >= 0 else 0)
        self.history_filter.blockSignals(False)

    def _choose_downloads_root(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Selecionar pasta de midias", self.downloads_root_input.text())
        if directory:
            self.downloads_root_input.setText(directory)
            self._save_settings()

    def _choose_sqlite_database(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "Selecionar banco SQLite", self.sqlite_database_input.text(), "SQLite (*.sqlite3 *.db)")
        if file_path:
            self.sqlite_database_input.setText(file_path)
            self._save_settings()

    def _choose_ffmpeg_path(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar FFmpeg", self.ffmpeg_path_input.text(), "Executavel (*.exe);;Todos (*.*)")
        if file_path:
            self.ffmpeg_path_input.setText(file_path)
            self._save_settings()

    def _save_settings(self) -> None:
        categories = [self.categories_list.item(index).text() for index in range(self.categories_list.count())]
        self.data_provider.update_settings(
            self.downloads_root_input.text().strip(),
            self.ffmpeg_path_input.text().strip(),
            self.sqlite_database_input.text().strip(),
            categories,
        )
        self.refresh_all()

    def _check_environment(self) -> None:
        check = self.data_provider.check_environment()
        if check is None:
            self.environment_status_label.setText("Indisponivel")
            return
        self.environment_status_label.setText(check.status.value)
        self._show_info("Ambiente", check.message)

    def _prepare_environment(self) -> None:
        check = self.data_provider.prepare_environment()
        if check is None:
            self.environment_status_label.setText("Indisponivel")
            return
        self.environment_status_label.setText(check.status.value)
        self._show_info("Ambiente", check.message)
        self.refresh_dashboard()

    def _prepare_system_automatically(self) -> None:
        if self._setup_thread is not None and self._setup_thread.isRunning():
            return

        self.system_status_summary.setText("Preparando ambiente...")
        self.system_status_table.setRowCount(0)
        self._setup_thread = QThread(self)
        self._setup_worker = SetupWorker(self.data_provider)
        self._setup_worker.moveToThread(self._setup_thread)
        self._setup_thread.started.connect(self._setup_worker.run)
        self._setup_worker.finished.connect(self._render_setup_report)
        self._setup_worker.finished.connect(self._setup_thread.quit)
        self._setup_worker.finished.connect(self._setup_worker.deleteLater)
        self._setup_thread.finished.connect(self._setup_thread.deleteLater)
        self._setup_thread.finished.connect(self._clear_setup_worker)
        self._setup_thread.start()

    def _clear_setup_worker(self) -> None:
        self._setup_thread = None
        self._setup_worker = None

    def _render_setup_report(self, report) -> None:
        if report is None:
            self.system_status_summary.setText("Preparacao automatica indisponivel.")
            return

        self.system_status_summary.setText(report.message)
        rows = [
            {
                "name": step.label,
                "status": self._friendly_setup_status(step.status.value),
                "message": step.message,
            }
            for step in report.steps
        ]
        self._fill_table(self.system_status_table, rows, ["name", "status", "message"])
        self.refresh_dashboard()
        if report.status.value == "OK":
            self._show_info("YkMedia", "Sistema pronto.")

    def _open_setup_wizard(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Assistente de Configuracao do YkMedia")
        dialog.setMinimumSize(560, 420)
        layout = QVBoxLayout(dialog)
        title = QLabel("Bem-vindo ao YkMedia")
        title.setObjectName("header_title")
        description = QLabel(
            "Siga estes passos: preparar sistema, conectar WhatsApp, escolher pasta das midias e usar."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)
        steps = QLabel(
            "1. Preparar Sistema\n"
            "2. Verificar servicos internos\n"
            "3. Configurar Evolution automaticamente\n"
            "4. Ler QR Code do WhatsApp\n"
            "5. Confirmar pasta das midias\n"
            "6. Teste final"
        )
        steps.setObjectName("muted")
        prepare = CompactButton("Preparar Sistema", "primary", "fa5s.magic")
        connect = CompactButton("Conectar WhatsApp", icon_name="fa5s.qrcode")
        folder = CompactButton("Escolher pasta das midias", icon_name="fa5s.folder")
        close = CompactButton("Fechar")
        prepare.clicked.connect(self._prepare_system_automatically)
        connect.clicked.connect(self._connect_evolution_session)
        folder.clicked.connect(self._choose_downloads_root)
        close.clicked.connect(dialog.accept)
        for widget in [title, description, steps]:
            layout.addWidget(widget)
        layout.addStretch()
        actions = self._toolbar()
        for button in [prepare, connect, folder, close]:
            actions.addWidget(button)
        layout.addLayout(actions)
        dialog.exec()

    def _run_diagnostics(self) -> None:
        report = self.data_provider.run_diagnostics()
        if report is None:
            self.diagnostics_summary.setText("Servico de diagnostico indisponivel.")
            return
        self._render_diagnostics_report(report)

    def _auto_fix_diagnostics(self) -> None:
        report = self.data_provider.auto_fix_diagnostics()
        if report is None:
            self.diagnostics_summary.setText("Servico de diagnostico indisponivel.")
            return
        self._render_diagnostics_report(report)
        self.refresh_dashboard()

    def _restart_backend_diagnostics(self) -> None:
        report = self.data_provider.restart_backend_from_diagnostics()
        if report is None:
            self.diagnostics_summary.setText("Servico de diagnostico indisponivel.")
            return
        self._render_diagnostics_report(report)
        self.refresh_dashboard()

    def _render_diagnostics_report(self, report) -> None:
        self.diagnostics_summary.setText(f"{report.status.value}: {report.message}")
        rows = [
            {
                "name": item.name,
                "status": item.status.value,
                "message": item.message,
            }
            for item in report.items
        ]
        self._fill_table(self.diagnostics_table, rows, ["name", "status", "message"])

    def _friendly_setup_status(self, status: str) -> str:
        labels = {
            "OK": "Funcionando",
            "WARNING": "Atencao",
            "ERROR": "Corrigir",
            "RUNNING": "Corrigindo",
            "PENDING": "Aguardando",
        }
        return labels.get(status, status)

    def _refresh_evolution_session(self, show_message: bool = True) -> None:
        snapshot = self.data_provider.get_evolution_session_snapshot()
        text = self._friendly_evolution_state(snapshot.state)
        self.evolution_state_label.setText(text)
        self._update_status_chips(snapshot.state)
        if show_message and snapshot.message:
            self._show_info("WhatsApp", snapshot.message)

    def _connect_evolution_session(self) -> None:
        snapshot = self.data_provider.connect_evolution_session()
        self.evolution_state_label.setText(self._friendly_evolution_state(snapshot.state))
        self._update_status_chips(snapshot.state)
        if snapshot.qrcode_base64:
            self._show_qrcode(snapshot.qrcode_base64)
        self._show_info("WhatsApp", snapshot.message or "Solicitacao de QR Code concluida.")

    def _disconnect_evolution_session(self) -> None:
        snapshot = self.data_provider.disconnect_evolution_session()
        self.evolution_state_label.setText(self._friendly_evolution_state(snapshot.state))
        self._update_status_chips(snapshot.state)
        self.evolution_qrcode_label.clear()
        self.evolution_qrcode_label.setText("Sessao desconectada. Gere um novo QR Code para conectar novamente.")
        self._show_info("WhatsApp", snapshot.message or "Sessao desconectada.")

    def _reconnect_evolution_session(self) -> None:
        snapshot = self.data_provider.reconnect_evolution_session()
        self.evolution_state_label.setText(self._friendly_evolution_state(snapshot.state))
        self._update_status_chips(snapshot.state)
        if snapshot.qrcode_base64:
            self._show_qrcode(snapshot.qrcode_base64)
        self._show_info("WhatsApp", snapshot.message or "Novo QR Code solicitado.")

    def _show_qrcode(self, qrcode_base64: str) -> None:
        encoded_content = qrcode_base64.split(",", 1)[1] if "," in qrcode_base64 else qrcode_base64
        try:
            image_content = base64.b64decode(encoded_content)
        except ValueError:
            self.evolution_qrcode_label.setText("QR Code recebido em formato invalido.")
            return
        pixmap = QPixmap()
        if pixmap.loadFromData(image_content):
            self.evolution_qrcode_label.setPixmap(pixmap)
        else:
            self.evolution_qrcode_label.setText("Nao foi possivel renderizar o QR Code.")

    def _update_status_chips(self, evolution_state: str) -> None:
        text = self._friendly_evolution_state(evolution_state)
        tone = self._status_tone(evolution_state)
        for chip in [self.header_indicators["evolution"], self.sidebar_evolution]:
            chip.setProperty("tone", tone)
            chip.set_text(text)
            chip.style().unpolish(chip)
            chip.style().polish(chip)

    def _update_system_status_chip(self, text: str, raw_state: str) -> None:
        tone = "success" if raw_state == "ONLINE" else "warning" if raw_state == "STARTING" else "danger"
        for chip in [self.header_indicators["system"], self.sidebar_system]:
            chip.setProperty("tone", tone)
            chip.set_text(text)
            chip.style().unpolish(chip)
            chip.style().polish(chip)

    def _friendly_backend_state(self, state: str) -> str:
        labels = {
            "ONLINE": "Backend online",
            "STARTING": "Backend iniciando",
            "OFFLINE": "Backend offline",
            "STOPPED": "Backend parado",
            "ERROR": "Backend com erro",
        }
        return labels.get(state, state or "Backend desconhecido")

    def _friendly_evolution_state(self, state: str) -> str:
        normalized = (state or "").lower()
        if normalized == "open":
            return "WhatsApp conectado"
        if normalized == "connecting":
            return "WhatsApp conectando"
        if normalized in {"close", "closed"}:
            return "WhatsApp desconectado"
        if normalized == "erro":
            return "WhatsApp com erro"
        return "WhatsApp nao verificado"

    def _status_tone(self, state: str) -> str:
        normalized = (state or "").lower()
        if normalized == "open":
            return "success"
        if normalized == "connecting":
            return "warning"
        if normalized in {"erro", "close", "closed"}:
            return "danger"
        return "neutral"

    def _open_media_root(self) -> None:
        self._open_path(self.data_provider.media_root_path())

    def _open_logs_directory(self) -> None:
        self._open_path(self.data_provider.logs_directory_path())

    def _open_file(self, path: Path) -> None:
        if path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        else:
            self._show_info("Arquivo", "Arquivo nao encontrado no disco.")

    def _open_containing_folder(self, path: Path) -> None:
        if path.exists():
            subprocess.Popen(["explorer", "/select,", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        self._open_path(path.parent)

    def _export_logs(self) -> None:
        target_path, _ = QFileDialog.getSaveFileName(self, "Exportar logs", "ykmedia-logs.txt", "Texto (*.txt)")
        if target_path:
            count = self.data_provider.export_logs(target_path)
            self._show_info("Logs", f"{count} linha(s) exportada(s).")

    def _open_path(self, path: Path) -> None:
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))
                return
        else:
            path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _toolbar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(10)
        return layout

    def _create_table(self, headers: list[str]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.verticalHeader().setDefaultSectionSize(40)
        return table

    def _fill_table(self, table: QTableWidget, rows: list[dict[str, str]], keys: list[str]) -> None:
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, key in enumerate(keys):
                text = str(row.get(key, ""))
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                table.setItem(row_index, column_index, item)
        table.setSortingEnabled(True)

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _source_from_log(self, message: str) -> str:
        upper = message.upper()
        if "WEBHOOK" in upper or "WHATSAPP" in upper:
            return "WhatsApp"
        if "DOWNLOAD" in upper:
            return "Worker"
        if "SQLITE" in upper or "BANCO" in upper:
            return "Banco"
        return "Sistema"

    def _show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)


def run() -> int:
    application = QApplication([])
    window = YkMediaMainWindow()
    window.showMaximized()
    return application.exec()
