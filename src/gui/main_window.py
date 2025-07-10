from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedWidget
)
from PySide6.QtCore import Qt
from .pages.buyer_search_page import BuyerSearchPage
from .pages.hs_code_page import HSCodePage


# Theme definitions
LIGHT_THEME = {
    'background': '#FFFFFF',
    'primary_accent': '#0078D4',
    'secondary_accent': '#4CAF50',
    'primary_text': '#2E3A59',
    'secondary_text': '#6B7C93',
    'divider': '#E0E4EA',
}

DARK_THEME = {
    'background': '#121A26',
    'surface': '#1E2A38',
    'primary_accent': '#4DA6FF',
    'secondary_accent': '#81C784',
    'primary_text': '#E0E4EA',
    'secondary_text': '#ABB2BC',
    'divider': '#2A3747',
}

PAGES = [
    ("Buyer Search", "🔍 Buyer Search Page"),
    ("Buyer List", "📋 Buyer List Page"),
    ("HS Code", "📦 HS Code Page"),
    ("Export", "⬇️ Export Page"),
    ("Settings", "⚙️ Settings Page"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Glove Buyer GUI')
        self.theme = 'light'
        self.setMinimumSize(800, 500)
        self.showMaximized()

        # Main layout: sidebar + main content
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Sidebar
        self.sidebar = QWidget()
        self.sidebar_layout = QVBoxLayout()
        self.sidebar.setLayout(self.sidebar_layout)
        self.sidebar.setFixedWidth(180)
        self.sidebar_layout.setSpacing(10)
        self.sidebar_layout.setContentsMargins(10, 20, 10, 10)

        # Navigation buttons
        self.nav_buttons = []
        for idx, (name, _) in enumerate(PAGES):
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, i=idx: self.switch_page(i))
            self.sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)
        self.sidebar_layout.addStretch(1)

        # Theme toggle button
        self.toggle_btn = QPushButton('Switch to Dark Theme')
        self.toggle_btn.setObjectName("themeToggle")
        self.toggle_btn.clicked.connect(self.toggle_theme)
        self.sidebar_layout.addWidget(self.toggle_btn)

        # Main content area (stacked pages)
        self.stack = QStackedWidget()
        # Page 0: Buyer Search
        self.buyer_search_page = BuyerSearchPage()
        self.stack.addWidget(self.buyer_search_page)
        # Page 1: Buyer List (placeholder)
        page = QWidget()
        vbox = QVBoxLayout()
        lbl = QLabel(PAGES[1][1])
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 28px;")
        vbox.addStretch(1)
        vbox.addWidget(lbl)
        vbox.addStretch(1)
        page.setLayout(vbox)
        self.stack.addWidget(page)
        # Page 2: HS Code
        self.hs_code_page = HSCodePage()
        self.stack.addWidget(self.hs_code_page)
        # Other pages: placeholders
        for _, label in PAGES[3:]:
            page = QWidget()
            vbox = QVBoxLayout()
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 28px;")
            vbox.addStretch(1)
            vbox.addWidget(lbl)
            vbox.addStretch(1)
            page.setLayout(vbox)
            self.stack.addWidget(page)

        # Add sidebar and main area to main layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack, 1)

        self.apply_theme()
        self.switch_page(0)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        # Update button highlighting
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                # Active button - highlighted
                btn.setEnabled(True)
                btn.setProperty("active", True)
            else:
                # Inactive button - normal
                btn.setEnabled(True)
                btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def toggle_theme(self):
        if self.theme == 'light':
            self.theme = 'dark'
            self.toggle_btn.setText('Switch to Light Theme')
        else:
            self.theme = 'light'
            self.toggle_btn.setText('Switch to Dark Theme')
        self.apply_theme()

    def apply_theme(self):
        if self.theme == 'light':
            theme = LIGHT_THEME
            self.sidebar.setStyleSheet(f"""
                QWidget {{
                    background: {theme['divider']};
                }}
                QPushButton {{
                    background: {theme['background']};
                    color: {theme['primary_text']};
                    border: none;
                    padding: 10px;
                    border-radius: 6px;
                    text-align: left;
                    font-size: 14px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background: {theme['primary_accent']};
                    color: white;
                }}
                QPushButton[active="true"] {{
                    background: {theme['primary_accent']};
                    color: white;
                    font-weight: 600;
                    border-left: 4px solid {theme['secondary_accent']};
                }}
            """)
            self.toggle_btn.setStyleSheet(f"""
                QPushButton#themeToggle {{
                    background: {theme['primary_accent']};
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: 500;
                }}
                QPushButton#themeToggle:hover {{
                    background: {theme['secondary_accent']};
                }}
            """)
            self.stack.setStyleSheet(f"background: {theme['background']}; color: {theme['primary_text']};")
            self.setStyleSheet(f"QMainWindow {{ background: {theme['background']}; }}")
        else:
            theme = DARK_THEME
            self.sidebar.setStyleSheet(f"""
                QWidget {{
                    background: {theme['surface']};
                }}
                QPushButton {{
                    background: {theme['surface']};
                    color: {theme['primary_text']};
                    border: none;
                    padding: 10px;
                    border-radius: 6px;
                    text-align: left;
                    font-size: 14px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background: {theme['primary_accent']};
                    color: {theme['background']};
                }}
                QPushButton[active="true"] {{
                    background: {theme['primary_accent']};
                    color: {theme['background']};
                    font-weight: 600;
                    border-left: 4px solid {theme['secondary_accent']};
                }}
            """)
            self.toggle_btn.setStyleSheet(f"""
                QPushButton#themeToggle {{
                    background: {theme['primary_accent']};
                    color: {theme['background']};
                    border: none;
                    padding: 10px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: 500;
                }}
                QPushButton#themeToggle:hover {{
                    background: {theme['secondary_accent']};
                }}
            """)
            self.stack.setStyleSheet(f"background: {theme['background']}; color: {theme['primary_text']};")
            self.setStyleSheet(f"QMainWindow {{ background: {theme['background']}; }}")
        # Update HSCodePage theme if it exists
        if hasattr(self, 'hs_code_page'):
            self.hs_code_page.apply_theme(self.theme) 