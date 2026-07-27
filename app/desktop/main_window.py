from collections.abc import Callable

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFormLayout,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.desktop.data_provider import DesktopDataProvider
from app.services.application_factory import (
    get_category_service,
    get_processing_queue,
    get_storage_service,
)


class YkMediaMainWindow(QMainWindow):
    def __init__(self, data_provider: DesktopDataProvider | None = None) -> None:
        super().__init__()
        self.data_provider = data_provider or DesktopDataProvider(
            storage_service=get_storage_service(),
            processing_queue=get_processing_queue(),
            category_service=get_category_service(),
        )
        self.setWindowTitle("YkMedia")
        self.resize(1440, 880)
        self._animations: list[QPropertyAnimation] = []

        self.pages: dict[str, QWidget] = {}
        self.nav_buttons: dict[str, QPushButton] = {}
        self.module_descriptions = {
            "Dashboard": "Visao geral operacional em tempo real",
            "Fila": "Trabalhos pendentes, em processamento e finalizados",
            "Historico": "Midias processadas e arquivos organizados",
            "Conversas": "Sessoes ativas por remetente",
            "Categorias": "Organizacao das pastas de destino",
            "Configuracoes": "Parametros locais da aplicacao",
            "Logs": "Eventos recentes do sistema",
            "Sobre": "Informacoes do YkMedia",
        }

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_shell(), 1)
        self.setCentralWidget(root)

        self._apply_styles()
        self._select_page("Dashboard")
        self.refresh_all()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(3000)
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.refresh_timer.start()

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(248)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 22, 18, 18)
        layout.setSpacing(10)

        brand = QLabel("YkMedia")
        brand.setObjectName("brand")
        version = QLabel("Desktop Console")
        version.setObjectName("muted")
        layout.addWidget(brand)
        layout.addWidget(version)
        layout.addSpacing(18)

        items = [
            ("Dashboard", "▦"),
            ("Fila", "☷"),
            ("Historico", "◷"),
            ("Conversas", "◌"),
            ("Categorias", "◇"),
            ("Configuracoes", "⚙"),
            ("Logs", "≡"),
            ("Sobre", "ⓘ"),
        ]

        for name, icon in items:
            button = QPushButton(f"{icon}  {name}")
            button.setObjectName("nav_button")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, page=name: self._select_page(page))
            self.nav_buttons[name] = button
            layout.addWidget(button)

        layout.addStretch()
        footer = QLabel("SQLite local\nFila em memoria persistida")
        footer.setObjectName("sidebar_footer")
        layout.addWidget(footer)
        return sidebar

    def _build_shell(self) -> QWidget:
        shell = QWidget()
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(18)
        layout.addWidget(self._build_header())

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("content_stack")
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
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        title_block = QVBoxLayout()
        self.header_title = QLabel("Dashboard")
        self.header_title.setObjectName("header_title")
        self.header_description = QLabel(self.module_descriptions["Dashboard"])
        self.header_description.setObjectName("muted")
        title_block.addWidget(self.header_title)
        title_block.addWidget(self.header_description)
        layout.addLayout(title_block)
        layout.addStretch()

        self.header_indicators: dict[str, QLabel] = {}
        for key, text in {
            "system": "● Sistema Online",
            "worker": "Worker",
            "evolution": "Evolution",
            "sqlite": "SQLite",
        }.items():
            label = QLabel(text)
            label.setObjectName("status_pill")
            self.header_indicators[key] = label
            layout.addWidget(label)

        return header

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)
        self.metric_labels: dict[str, QLabel] = {}
        cards = QGridLayout()
        for index, (key, title) in enumerate(
            [
                ("system_status", "Sistema"),
                ("evolution_status", "Evolution"),
                ("worker_status", "Worker"),
                ("pending_jobs", "Fila"),
                ("completed_jobs", "Concluidos"),
                ("error_jobs", "Erros"),
            ]
        ):
            card, value = self._metric_card(title)
            self.metric_labels[key] = value
            cards.addWidget(card, index // 3, index % 3)
        layout.addLayout(cards)

        charts = QGridLayout()
        charts.addWidget(self._placeholder_panel("Grafico de atividade", "Atividade por hora"), 0, 0)
        charts.addWidget(self._placeholder_panel("Grafico de processamento", "Pendentes x concluidos"), 0, 1)
        charts.addWidget(self._placeholder_panel("Uso do disco", "Espaco usado pela pasta media"), 1, 0)
        charts.addWidget(self._placeholder_panel("Tempo medio", "Tempo medio por processamento"), 1, 1)
        layout.addLayout(charts, 1)
        return page

    def _build_queue_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        toolbar = self._toolbar()
        self.queue_search = QLineEdit()
        self.queue_search.setPlaceholderText("Pesquisar fila")
        self.queue_filter = QComboBox()
        self.queue_filter.addItems(["Todos", "PENDENTE", "PROCESSANDO", "CONCLUIDO", "ERRO"])
        refresh_button = QPushButton("Atualizar")
        refresh_button.clicked.connect(self.refresh_queue)
        clear_button = QPushButton("Limpar concluidos")
        clear_button.clicked.connect(self._clear_completed_jobs)
        toolbar.addWidget(self.queue_search)
        toolbar.addWidget(self.queue_filter)
        toolbar.addWidget(refresh_button)
        toolbar.addWidget(clear_button)
        layout.addLayout(toolbar)
        self.queue_table = self._create_table(["ID", "Remetente", "Origem", "Status", "Data/Hora"])
        layout.addWidget(self.queue_table)
        return page

    def _build_history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        toolbar = self._toolbar()
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("Pesquisar historico")
        self.history_search.textChanged.connect(self.refresh_history)
        self.history_filter = QComboBox()
        self.history_filter.addItems(["Todos", "Louvores", "Mensagens", "Jovens", "Criancas", "Outros"])
        self.pagination_label = QLabel("Pagina 1")
        toolbar.addWidget(self.history_search)
        toolbar.addWidget(self.history_filter)
        toolbar.addWidget(self.pagination_label)
        layout.addLayout(toolbar)
        self.history_table = self._create_table(["Data", "Remetente", "Categoria", "Nome final", "Caminho"])
        layout.addWidget(self.history_table)
        return page

    def _build_conversations_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        self.conversations_list = QListWidget()
        self.conversations_list.setFixedWidth(320)
        self.conversation_details = QTextEdit()
        self.conversation_details.setReadOnly(True)
        layout.addWidget(self.conversations_list)
        layout.addWidget(self.conversation_details, 1)
        return page

    def _build_categories_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.categories_list = QListWidget()
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Nova categoria")
        actions = self._toolbar()
        buttons: list[tuple[str, Callable[[], None]]] = [
            ("Adicionar", self._add_category),
            ("Editar", self._edit_selected_category),
            ("Excluir", self._remove_selected_category),
            ("Mover acima", self._move_category_up),
            ("Mover abaixo", self._move_category_down),
        ]
        actions.addWidget(self.category_input)
        for text, handler in buttons:
            button = QPushButton(text)
            button.clicked.connect(handler)
            actions.addWidget(button)
        layout.addWidget(self.categories_list)
        layout.addLayout(actions)
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page)
        self.downloads_root_input = QLineEdit()
        self.ffmpeg_path_input = QLineEdit()
        self.sqlite_database_input = QLineEdit()
        self.youtube_temp_input = QLineEdit()
        self.whatsapp_instance_input = QLineEdit("ykmedia")
        layout.addWidget(self._settings_group("Geral", [("Ambiente", QLineEdit("development"))]), 0, 0)
        layout.addWidget(self._settings_group("Downloads", [("Pasta raiz", self.downloads_root_input)]), 0, 1)
        layout.addWidget(self._settings_group("SQLite", [("Banco SQLite", self.sqlite_database_input)]), 1, 0)
        layout.addWidget(self._settings_group("FFmpeg", [("Caminho do FFmpeg", self.ffmpeg_path_input)]), 1, 1)
        layout.addWidget(self._settings_group("YouTube", [("Downloads temporarios", self.youtube_temp_input)]), 2, 0)
        layout.addWidget(self._settings_group("WhatsApp", [("Instancia Evolution", self.whatsapp_instance_input)]), 2, 1)
        return page

    def _build_logs_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        toolbar = self._toolbar()
        self.logs_search = QLineEdit()
        self.logs_search.setPlaceholderText("Pesquisar logs")
        self.logs_filter = QComboBox()
        self.logs_filter.addItems(["INFO", "WARNING", "ERROR"])
        export_button = QPushButton("Exportar")
        toolbar.addWidget(self.logs_search)
        toolbar.addWidget(self.logs_filter)
        toolbar.addWidget(export_button)
        self.logs_table = self._create_table(["Data/Hora", "Nivel", "Mensagem"])
        layout.addLayout(toolbar)
        layout.addWidget(self.logs_table)
        return page

    def _build_about_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        panel = self._placeholder_panel(
            "YkMedia",
            "Console desktop para monitoramento e configuracao do gerenciamento de midias via WhatsApp.",
        )
        layout.addWidget(panel)
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
        self.metric_labels["system_status"].setText(snapshot.system_status)
        self.metric_labels["evolution_status"].setText(snapshot.evolution_status)
        self.metric_labels["worker_status"].setText(snapshot.worker_status)
        self.metric_labels["pending_jobs"].setText(str(snapshot.pending_jobs))
        self.metric_labels["completed_jobs"].setText(str(snapshot.completed_jobs))
        self.metric_labels["error_jobs"].setText(str(snapshot.error_jobs))
        self.header_indicators["worker"].setText(f"Worker {snapshot.worker_status}")
        self.header_indicators["evolution"].setText(f"Evolution {snapshot.evolution_status}")

    def refresh_queue(self) -> None:
        rows = self.data_provider.list_jobs()
        query = self.queue_search.text().strip().lower()
        status = self.queue_filter.currentText()
        if query:
            rows = [row for row in rows if query in " ".join(row.values()).lower()]
        if status != "Todos":
            rows = [row for row in rows if row["status"] == status]
        self._fill_table(self.queue_table, rows, ["id", "sender", "origin", "status", "created_at"])

    def refresh_history(self) -> None:
        rows = self.data_provider.list_history(self.history_search.text())
        category = self.history_filter.currentText()
        if category != "Todos":
            rows = [row for row in rows if row["category"] == category]
        self._fill_table(self.history_table, rows, ["date", "sender", "category", "final_name", "file_path"])

    def refresh_conversations(self) -> None:
        self.conversations_list.clear()
        conversations = self.data_provider.list_conversations()
        for conversation in conversations:
            self.conversations_list.addItem(f"{conversation['sender']}  {conversation['state']}")
        details = conversations[0] if conversations else None
        self.conversation_details.setText(
            "\n".join(f"{key}: {value}" for key, value in details.items()) if details else "Nenhuma conversa ativa."
        )

    def refresh_categories(self) -> None:
        if self.categories_list.count() == 0:
            self.categories_list.addItems(self.data_provider.get_settings_snapshot().categories)

    def refresh_settings(self) -> None:
        snapshot = self.data_provider.get_settings_snapshot()
        if not self.downloads_root_input.text():
            self.downloads_root_input.setText(snapshot.downloads_root)
        if not self.sqlite_database_input.text():
            self.sqlite_database_input.setText(snapshot.sqlite_database)
        if not self.ffmpeg_path_input.text():
            self.ffmpeg_path_input.setText(snapshot.ffmpeg_path)

    def refresh_logs(self) -> None:
        self._fill_table(self.logs_table, self.data_provider.list_logs(), ["date", "level", "message"])

    def _select_page(self, name: str) -> None:
        for page_name, button in self.nav_buttons.items():
            button.setChecked(page_name == name)
        self.header_title.setText(name)
        self.header_description.setText(self.module_descriptions[name])
        self.content_stack.setCurrentWidget(self.pages[name])
        self._fade_current_page()

    def _fade_current_page(self) -> None:
        effect = QGraphicsOpacityEffect(self.content_stack.currentWidget())
        self.content_stack.currentWidget().setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(140)
        animation.setStartValue(0.72)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        self._animations.append(animation)

    def _clear_completed_jobs(self) -> None:
        self.data_provider.clear_completed_jobs()
        self.refresh_queue()
        self.refresh_dashboard()

    def _save_categories(self) -> None:
        categories = [self.categories_list.item(index).text() for index in range(self.categories_list.count())]
        snapshot = self.data_provider.get_settings_snapshot()
        self.data_provider.update_settings(
            downloads_root=snapshot.downloads_root,
            ffmpeg_path=snapshot.ffmpeg_path,
            sqlite_database=snapshot.sqlite_database,
            categories=categories,
        )

    def _add_category(self) -> None:
        category = self.category_input.text().strip()
        if category:
            self.categories_list.addItem(category)
            self.category_input.clear()
            self._save_categories()

    def _edit_selected_category(self) -> None:
        item = self.categories_list.currentItem()
        text = self.category_input.text().strip()
        if item is not None and text:
            item.setText(text)
            self.category_input.clear()
            self._save_categories()

    def _remove_selected_category(self) -> None:
        for item in self.categories_list.selectedItems():
            self.categories_list.takeItem(self.categories_list.row(item))
        self._save_categories()

    def _move_category_up(self) -> None:
        self._move_selected_category(-1)

    def _move_category_down(self) -> None:
        self._move_selected_category(1)

    def _move_selected_category(self, direction: int) -> None:
        row = self.categories_list.currentRow()
        target = row + direction
        if row < 0 or target < 0 or target >= self.categories_list.count():
            return
        item = self.categories_list.takeItem(row)
        self.categories_list.insertItem(target, item)
        self.categories_list.setCurrentRow(target)
        self._save_categories()

    def _metric_card(self, title: str) -> tuple[QWidget, QLabel]:
        card = QFrame()
        card.setObjectName("metric_card")
        layout = QVBoxLayout(card)
        label = QLabel(title)
        label.setObjectName("metric_title")
        value = QLabel("-")
        value.setObjectName("metric_value")
        layout.addWidget(label)
        layout.addWidget(value)
        return card, value

    def _placeholder_panel(self, title: str, body: str) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        title_label = QLabel(title)
        title_label.setObjectName("panel_title")
        body_label = QLabel(body)
        body_label.setObjectName("muted")
        layout.addWidget(title_label)
        layout.addWidget(body_label)
        layout.addStretch()
        return panel

    def _settings_group(self, title: str, fields: list[tuple[str, QLineEdit]]) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        label = QLabel(title)
        label.setObjectName("panel_title")
        form = QFormLayout()
        for field_label, widget in fields:
            form.addRow(field_label, widget)
        layout.addWidget(label)
        layout.addLayout(form)
        return panel

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
        return table

    def _fill_table(self, table: QTableWidget, rows: list[dict[str, str]], keys: list[str]) -> None:
        table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, key in enumerate(keys):
                table.setItem(row_index, column_index, QTableWidgetItem(row[key]))

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #071018;
                color: #edf5ff;
                font-family: Segoe UI;
                font-size: 14px;
            }
            QFrame#sidebar {
                background: #081722;
                border-right: 1px solid #19303d;
            }
            QLabel#brand {
                font-size: 26px;
                font-weight: 800;
                color: #ffffff;
            }
            QLabel#muted, QLabel#sidebar_footer {
                color: #90a4b4;
            }
            QPushButton#nav_button {
                text-align: left;
                background: transparent;
                border: 0;
                border-radius: 10px;
                padding: 12px 14px;
                color: #c8d5df;
                font-weight: 600;
            }
            QPushButton#nav_button:checked {
                background: #0b73ff;
                color: #ffffff;
            }
            QFrame#header {
                background: transparent;
            }
            QLabel#header_title {
                font-size: 30px;
                font-weight: 800;
            }
            QLabel#status_pill {
                background: #0d2230;
                border: 1px solid #1d3948;
                border-radius: 10px;
                padding: 8px 12px;
                color: #b9ccd8;
            }
            QFrame#metric_card, QFrame#panel {
                background: #0b1b26;
                border: 1px solid #1c3544;
                border-radius: 12px;
            }
            QLabel#metric_title {
                color: #a8bac7;
            }
            QLabel#metric_value {
                font-size: 26px;
                font-weight: 800;
                color: #36d779;
            }
            QLabel#panel_title {
                font-size: 18px;
                font-weight: 700;
            }
            QTableWidget, QLineEdit, QListWidget, QTextEdit, QComboBox {
                background: #0b1b26;
                border: 1px solid #1c3544;
                border-radius: 10px;
                padding: 8px;
                color: #edf5ff;
                selection-background-color: #0b73ff;
            }
            QHeaderView::section {
                background: #102736;
                color: #dceaf4;
                padding: 10px;
                border: 0;
                font-weight: 700;
            }
            QPushButton {
                background: #102736;
                border: 1px solid #244354;
                border-radius: 10px;
                padding: 10px 14px;
                color: #edf5ff;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #17364a;
            }
            """
        )


def run() -> int:
    application = QApplication([])
    window = YkMediaMainWindow()
    window.show()
    return application.exec()
