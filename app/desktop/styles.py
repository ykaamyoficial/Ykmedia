DESKTOP_STYLE = """
QMainWindow, QWidget {
    background: #050b12;
    color: #edf5ff;
    font-family: "Segoe UI", Arial;
    font-size: 12px;
}

QLabel {
    background: transparent;
}

QFrame#sidebar {
    background: #06131d;
    border-right: 1px solid #142536;
}

QLabel#brand_logo {
    background: #0d1f30;
    border: 1px solid #1e3b55;
    border-radius: 13px;
}

QLabel#brand {
    color: #ffffff;
    font-size: 18px;
    font-weight: 800;
}

QLabel#app_subtitle, QLabel#muted, QLabel.muted {
    color: #90a3b8;
}

QLabel#header_title {
    color: #ffffff;
    font-size: 20px;
    font-weight: 800;
}

QPushButton#nav_button {
    text-align: left;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 6px 8px;
    color: #d8e5f2;
    font-weight: 650;
    font-size: 12px;
}

QPushButton#nav_button:hover {
    background: #0d2030;
    border-color: #18354b;
}

QPushButton#nav_button:checked {
    background: #115ee8;
    border-color: #2d7dff;
    color: #ffffff;
}

QPushButton#nav_button:focus {
    outline: 0;
}

QFrame#section_card, QFrame#metric_card, QFrame#empty_state, QFrame#media_card, QFrame#contact_item, QFrame#conversation_profile, QFrame#conversation_stat, QFrame#conversation_info, QFrame#timeline_event, QFrame#yk_panel {
    background: #071520;
    border: 1px solid #172b3d;
    border-radius: 12px;
}

QFrame#metric_card:hover, QFrame#media_card:hover {
    border-color: #2b5574;
    background: #0a1c2b;
}

QFrame#conversation_profile {
    background: #0a1728;
    border-color: #203956;
}

QFrame#contact_item {
    background: #07131d;
    border: 1px solid transparent;
    border-left: 2px solid transparent;
    border-radius: 10px;
}

QFrame#contact_item:hover {
    background: #0d1b28;
    border-color: #20364a;
}

QFrame#contact_item[selected="true"] {
    background: #0f2540;
    border-color: #1f6feb;
}

QFrame#avatar_badge {
    background: #1d4ed8;
    border: 1px solid #3b82f6;
    border-radius: 27px;
}

QFrame#avatar_badge[tone="success"] {
    background: #047857;
    border-color: #10b981;
}

QFrame#avatar_badge[tone="warning"] {
    background: #b45309;
    border-color: #f59e0b;
}

QFrame#avatar_badge[tone="danger"] {
    background: #b91c1c;
    border-color: #ef4444;
}

QFrame#avatar_badge[tone="teal"] {
    background: #0e7490;
    border-color: #22d3ee;
}

QFrame#avatar_badge[tone="violet"] {
    background: #6d28d9;
    border-color: #8b5cf6;
}

QLabel#avatar_text {
    color: #ffffff;
    font-size: 14px;
    font-weight: 900;
}

QLabel#contact_name, QLabel#profile_title {
    color: #ffffff;
    font-size: 12px;
    font-weight: 850;
}

QLabel#profile_title {
    font-size: 15px;
}

QLabel#contact_phone, QLabel#profile_subtitle {
    color: #8fa3b8;
    font-size: 11px;
}

QLabel#contact_preview {
    color: #b9c9dc;
    font-size: 11px;
}

QLabel#contact_time {
    color: #9fb4cc;
    font-size: 11px;
}

QLabel#contact_category {
    color: #8fa4b9;
    font-size: 11px;
}

QLabel#contact_state {
    background: transparent;
    border: 0;
    border-radius: 0;
    color: #90a5ba;
    padding: 0;
    font-size: 10px;
    font-weight: 700;
}

QLabel#contact_state[active="true"] {
    background: #08371f;
    border-color: #146c43;
    color: #48e08a;
}

QLabel#contact_count {
    background: #1267f2;
    border-radius: 8px;
    color: #ffffff;
    padding: 2px 6px;
    font-size: 10px;
    font-weight: 900;
}

QFrame#conversation_stat {
    background: #0a1520;
    border-color: #1c3045;
}

QFrame#conversation_info {
    background: #07111b;
    border-color: #182a3c;
}

QLabel#stat_title {
    color: #93a7bc;
    font-size: 11px;
    font-weight: 800;
}

QLabel#stat_value {
    color: #ffffff;
    font-size: 14px;
    font-weight: 900;
}

QLabel#info_field {
    color: #b7c7d8;
    font-size: 12px;
}

QFrame#icon_badge {
    background: #123a66;
    border: 1px solid #2467a5;
    border-radius: 12px;
}

QFrame#icon_badge[tone="success"] {
    background: #0f3a2a;
    border-color: #1b8f57;
}

QFrame#icon_badge[tone="warning"] {
    background: #3e2e08;
    border-color: #aa7d19;
}

QFrame#icon_badge[tone="danger"] {
    background: #421721;
    border-color: #9e3748;
}

QFrame#icon_badge[tone="soft"] {
    background: #0d2639;
    border-color: #21455e;
    border-radius: 17px;
}

QFrame#status_chip, QFrame#yk_status_badge {
    background: #081927;
    border: 1px solid #1b344a;
    border-radius: 10px;
}

QLabel#status_dot {
    border-radius: 4px;
    background: #7d91a6;
}

QLabel#status_dot[tone="success"] {
    background: #20d973;
}

QLabel#status_dot[tone="warning"] {
    background: #f5b81f;
}

QLabel#status_dot[tone="danger"] {
    background: #ff4f64;
}

QLabel#status_chip_text {
    color: #f1f7ff;
    font-weight: 700;
    font-size: 10px;
}

QLabel#metric_title {
    color: #a9bdd0;
    font-weight: 650;
}

QLabel#metric_value {
    color: #ffffff;
    font-size: 20px;
    font-weight: 850;
}

QLabel#metric_caption {
    color: #8498ac;
}

QLabel#section_title {
    color: #f7fbff;
    font-size: 15px;
    font-weight: 800;
}

QLabel#yk_section_title {
    color: #f7fbff;
    font-size: 16px;
    font-weight: 800;
}

QLabel#empty_title {
    color: #f4f9ff;
    font-weight: 800;
}

QLabel#empty_description {
    color: #8fa4b7;
}

QFrame#media_preview {
    background: #0d2234;
    border: 1px solid #24435b;
    border-radius: 10px;
}

QLabel#media_title {
    color: #ffffff;
    font-size: 12px;
    font-weight: 800;
}

QFrame#conversation_bubble {
    border-radius: 12px;
    padding: 2px;
}

QFrame#conversation_bubble[direction="inbound"] {
    background: #0b1d2c;
    border: 1px solid #24425b;
}

QFrame#conversation_bubble[direction="outbound"] {
    background: #0c3a62;
    border: 1px solid #246ea8;
}

QLabel#bubble_header {
    color: #d8eaff;
    font-weight: 800;
}

QLabel#bubble_content {
    color: #ffffff;
    font-size: 13px;
}

QLabel#bubble_footer {
    color: #9bb1c8;
    font-size: 11px;
}

QLabel#bubble_error {
    color: #ff9fab;
    font-size: 12px;
}

QFrame#timeline_media_preview {
    background: #10233a;
    border: 1px solid #2b4b68;
    border-radius: 10px;
}

QFrame#timeline_event {
    background: #091522;
    border-color: #1c3147;
}

QLabel#event_content {
    color: #eaf3ff;
    font-weight: 800;
}

QLabel#timeline_badge {
    background: #153b72;
    border: 1px solid #2b66b1;
    color: #cfe6ff;
    border-radius: 10px;
    padding: 4px 9px;
    font-weight: 800;
}

QPushButton#conversation_filter {
    background: #0c1825;
    border: 1px solid #203a57;
    border-radius: 9px;
    color: #aebfd3;
    padding: 7px 10px;
    font-weight: 800;
    font-size: 12px;
}

QPushButton#yk_chip {
    background: #0b1824;
    border: 1px solid #1b344c;
    border-radius: 9px;
    color: #aebfd3;
    padding: 3px 7px;
    font-weight: 750;
    font-size: 10px;
}

QPushButton#yk_chip:hover {
    background: #102235;
    border-color: #29506d;
}

QPushButton#yk_chip:checked {
    background: #1267f2;
    border-color: #3b82f6;
    color: #ffffff;
}

QPushButton#conversation_filter:checked {
    background: #1267f2;
    border-color: #3b82f6;
    color: #ffffff;
}

QPushButton#compact_button, QPushButton#yk_button, QPushButton {
    background: #0d2435;
    border: 1px solid #24475f;
    border-radius: 9px;
    padding: 5px 9px;
    color: #edf6ff;
    font-weight: 750;
    font-size: 12px;
}

QPushButton#compact_button[variant="primary"], QPushButton#yk_button[variant="primary"] {
    background: #1267f2;
    border-color: #3282ff;
}

QPushButton#compact_button[variant="danger"], QPushButton#yk_button[variant="danger"] {
    background: #2a1018;
    border-color: #8a3342;
    color: #ff9fab;
}

QPushButton#yk_icon_button {
    background: #091a28;
    border: 1px solid #1c374f;
    border-radius: 9px;
    padding: 0;
}

QPushButton#yk_icon_button:hover {
    background: #102336;
    border-color: #2b5574;
}

QPushButton:hover {
    background: #14344b;
    border-color: #35627f;
}

QPushButton:pressed {
    background: #0c1d2c;
}

QPushButton:disabled {
    color: #667b8e;
    background: #081722;
    border-color: #172d3e;
}

QLineEdit, QComboBox, QTextEdit, QListWidget {
    background: #07141f;
    border: 1px solid #1d374c;
    border-radius: 10px;
    padding: 7px 10px;
    color: #eef7ff;
    selection-background-color: #1267f2;
}

QLineEdit#yk_search_field {
    background: #07131e;
    border: 1px solid #1b344a;
    border-radius: 10px;
    min-height: 24px;
    padding: 4px 8px;
    color: #eef7ff;
}

QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QListWidget:focus {
    border-color: #2f80ed;
}

QLineEdit {
    min-height: 24px;
}

QComboBox {
    min-height: 26px;
}

QListWidget::item {
    border-radius: 10px;
    padding: 2px;
    margin: 2px;
}

QListWidget::item:selected {
    background: #113f84;
    color: #ffffff;
}

QListWidget::item:hover {
    background: #0e2639;
}

QTableWidget {
    background: #07141f;
    alternate-background-color: #0a1926;
    gridline-color: #13283a;
    border: 1px solid #1d374c;
    border-radius: 12px;
    color: #edf7ff;
    selection-background-color: #123d70;
    selection-color: #ffffff;
}

QTableWidget::item {
    padding: 9px;
    border: 0;
}

QHeaderView::section {
    background: #10263a;
    color: #f2f8ff;
    padding: 10px;
    border: 0;
    border-right: 1px solid #1f394e;
    font-weight: 850;
}

QTableCornerButton::section {
    background: #10263a;
    border: 0;
}

QScrollArea {
    background: transparent;
    border: 0;
}

QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 2px 0 2px 0;
}

QScrollBar::handle:vertical {
    background: #294156;
    border-radius: 3px;
    min-height: 28px;
}

QScrollBar::handle:vertical:hover {
    background: #3e5f78;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    background: transparent;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

QFrame#yk_info_row {
    background: transparent;
    border: 0;
}

QLabel#info_label {
    color: #7f94aa;
    font-size: 11px;
    font-weight: 700;
}

QLabel#info_value {
    color: #d8e6f4;
    font-size: 12px;
}

QTabWidget::pane {
    border: 0;
}

QLabel#qr_placeholder {
    background: #07141f;
    border: 1px dashed #2b5674;
    border-radius: 12px;
    color: #95a9bd;
    padding: 14px;
}
"""
