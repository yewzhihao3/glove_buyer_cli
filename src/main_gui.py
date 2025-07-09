import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedWidget, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QCheckBox, QMessageBox, QToolButton
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
import os
import sqlite3
# --- Import real logic ---
from db import get_country_hs_codes
from deepseek_agent import query_deepseek_for_hs_codes, parse_hs_codes_from_deepseek
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QDialogButtonBox, QWidget, QHBoxLayout
from PySide6.QtGui import QIcon

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

def load_asia_countries():
    countries = set()
    fname = "prompts/asia_countries.txt"
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            for line in f:
                country = line.strip()
                if country:
                    countries.add(country)
    return countries

def load_global_countries():
    countries = set()
    fname = "prompts/global_countries.txt"
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            for line in f:
                country = line.strip()
                if country:
                    countries.add(country)
    return countries

class BuyerSearchPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        # Search bar
        search_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter buyer name...")
        self.country_combo = QComboBox()
        self.country_combo.setEditable(True)
        self.country_combo.setInsertPolicy(QComboBox.NoInsert)
        self.country_combo.setPlaceholderText("Country")
        # Placeholder country list
        self.country_combo.addItems(["", "USA", "UK", "China", "Malaysia", "Germany"])
        self.hs_code_combo = QComboBox()
        self.hs_code_combo.setEditable(True)
        self.hs_code_combo.setInsertPolicy(QComboBox.NoInsert)
        self.hs_code_combo.setPlaceholderText("HS Code")
        # Placeholder HS code list
        self.hs_code_combo.addItems(["", "4015.19", "4015.11", "3926.20"])
        self.deepseek_checkbox = QCheckBox("Use DeepSeek AI for enhanced search")
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.do_search)
        search_layout.addWidget(self.name_input)
        search_layout.addWidget(self.country_combo)
        search_layout.addWidget(self.hs_code_combo)
        search_layout.addWidget(self.deepseek_checkbox)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)
        # Results table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Name", "Country", "Email", "HS Code"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.setLayout(layout)
        # Initial placeholder data
        self.populate_table([
            ("Acme Gloves", "USA", "acme@example.com", "4015.19"),
            ("Best Gloves Ltd", "UK", "info@bestgloves.co.uk", "4015.11"),
        ])
    def do_search(self):
        # Placeholder: just repopulate with the same data
        self.populate_table([
            ("Acme Gloves", "USA", "acme@example.com", "4015.19"),
            ("Best Gloves Ltd", "UK", "info@bestgloves.co.uk", "4015.11"),
        ])
    def populate_table(self, data):
        self.table.setRowCount(len(data))
        for row, (name, country, email, hs_code) in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(country))
            self.table.setItem(row, 2, QTableWidgetItem(email))
            self.table.setItem(row, 3, QTableWidgetItem(hs_code))

class DeepSeekWorker(QThread):
    result_ready = Signal(list)
    error = Signal(str)
    def __init__(self, country, query):
        super().__init__()
        self.country = country
        self.query = query
    def run(self):
        try:
            from deepseek_agent import query_deepseek_for_hs_codes, parse_hs_codes_from_deepseek
            output = query_deepseek_for_hs_codes(self.country)
            parsed = parse_hs_codes_from_deepseek(output)
            # Optionally, filter DeepSeek results by query
            filtered_parsed = [row for row in parsed if self.query in row['hs_code'].lower() or self.query in row['description'].lower()]
            self.result_ready.emit(filtered_parsed)
        except Exception as e:
            self.error.emit(str(e))

class AddHSCodeDialog(QMessageBox):
    def __init__(self, parent, country):
        super().__init__(parent)
        self.setWindowTitle("Add HS Code")
        self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        self.setDefaultButton(QMessageBox.Ok)
        self.country = country
        # Custom layout
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QDialogButtonBox, QWidget
        self.dialog = QDialog(parent)
        self.dialog.setWindowTitle("Add HS Code")
        layout = QVBoxLayout()
        self.hs_code_input = QLineEdit()
        self.hs_code_input.setPlaceholderText("HS Code")
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description")
        layout.addWidget(QLabel(f"Country: {country}"))
        layout.addWidget(self.hs_code_input)
        layout.addWidget(self.desc_input)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.dialog.accept)
        buttons.rejected.connect(self.dialog.reject)
        layout.addWidget(buttons)
        self.dialog.setLayout(layout)
    def get_data(self):
        if self.dialog.exec() == QMessageBox.Accepted:
            return self.hs_code_input.text().strip(), self.desc_input.text().strip()
        return None, None

class EditHSCodeDialog(QDialog):
    def __init__(self, parent, country, hs_code, desc):
        super().__init__(parent)
        self.setWindowTitle("Edit HS Code")
        layout = QVBoxLayout()
        self.hs_code_input = QLineEdit(hs_code)
        self.desc_input = QLineEdit(desc)
        layout.addWidget(QLabel(f"Country: {country}"))
        layout.addWidget(QLabel("HS Code:"))
        layout.addWidget(self.hs_code_input)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.desc_input)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
    def get_data(self):
        if self.exec() == QDialog.Accepted:
            return self.hs_code_input.text().strip(), self.desc_input.text().strip()
        return None, None

class HSCodePage(QWidget):
    def __init__(self):
        super().__init__()
        # Outer layout for zen padding
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(32, 32, 32, 32)
        outer_layout.setSpacing(24)
        # Card-like container
        card = QWidget()
        card.setObjectName("card")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(20)
        # Add HS Code button
        self.add_btn = QPushButton("Add HS Code")
        self.add_btn.clicked.connect(self.add_hs_code)
        self.add_btn.setObjectName("primaryBtn")
        card_layout.addWidget(self.add_btn, alignment=Qt.AlignLeft)
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)
        self.country_combo = QComboBox()
        self.country_combo.setEditable(True)
        self.country_combo.setInsertPolicy(QComboBox.NoInsert)
        self.country_combo.setPlaceholderText("Country")
        self.country_combo.addItem("All")
        self.country_combo.addItem("")
        self.asia_countries = load_asia_countries()
        self.global_countries = load_global_countries()
        for country in sorted(self.asia_countries | self.global_countries):
            self.country_combo.addItem(country)
        self.hs_input = QLineEdit()
        self.hs_input.setPlaceholderText("Enter HS code or description...")
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.do_search)
        self.search_btn.setObjectName("primaryBtn")
        search_layout.addWidget(self.country_combo)
        search_layout.addWidget(self.hs_input)
        search_layout.addWidget(self.search_btn)
        card_layout.addLayout(search_layout)
        # Results table (add Actions column)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["HS Code", "Country", "Description", ""])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 60)
        self.table.setObjectName("zenTable")
        card_layout.addWidget(self.table)
        card.setLayout(card_layout)
        outer_layout.addWidget(card)
        self.setLayout(outer_layout)
        self.populate_table([])
        self.loading_dialog = None
        self.deepseek_thread = None
        self.theme = 'light'  # Track current theme
        self.setStyleSheet(self.zen_stylesheet(self.theme))
    def zen_stylesheet(self, theme):
        if theme == 'dark':
            return """
            QWidget#card {
                background: #1E2A38;
                border-radius: 18px;
                border: 1px solid #2A3747;
            }
            QPushButton#primaryBtn {
                background: #4DA6FF;
                color: #121A26;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton#primaryBtn:hover {
                background: #0078D4;
            }
            QPushButton {
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 15px;
                color: #E0E4EA;
                background: transparent;
            }
            QPushButton:hover {
                background: #2A3747;
            }
            QLineEdit, QComboBox {
                border: 1px solid #2A3747;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 15px;
                background: #121A26;
                color: #E0E4EA;
            }
            QTableWidget#zenTable {
                background: #1E2A38;
                border-radius: 12px;
                font-size: 15px;
                color: #E0E4EA;
            }
            QHeaderView::section {
                background: #2A3747;
                font-weight: 600;
                font-size: 15px;
                border: none;
                border-radius: 8px;
                padding: 8px;
                color: #E0E4EA;
            }
            """
        else:
            return """
            QWidget#card {
                background: #f8fafc;
                border-radius: 18px;
                border: 1px solid #e0e4ea;
            }
            QPushButton#primaryBtn {
                background: #0078D4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton#primaryBtn:hover {
                background: #005fa3;
            }
            QPushButton {
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 15px;
            }
            QPushButton:hover {
                background: #e0e4ea;
            }
            QLineEdit, QComboBox {
                border: 1px solid #e0e4ea;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 15px;
                background: #fff;
            }
            QTableWidget#zenTable {
                background: #fff;
                border-radius: 12px;
                font-size: 15px;
            }
            QHeaderView::section {
                background: #f0f2f5;
                font-weight: 600;
                font-size: 15px;
                border: none;
                border-radius: 8px;
                padding: 8px;
            }
            """
    def showEvent(self, event):
        idx = self.country_combo.findText("All")
        if idx != -1:
            self.country_combo.setCurrentIndex(idx)
            self.do_search()
        super().showEvent(event)
    def add_hs_code(self):
        country = self.country_combo.currentText().strip()
        if not country:
            QMessageBox.warning(self, "Missing Country", "Please select a country before adding an HS code.")
            return
        dialog = AddHSCodeDialog(self, country)
        hs_code, desc = dialog.get_data()
        if hs_code and desc:
            try:
                conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'data', 'results.db'))
                c = conn.cursor()
                if country in self.asia_countries:
                    c.execute('INSERT OR IGNORE INTO asia_hs_codes (hs_code, description, country) VALUES (?, ?, ?)', (hs_code, desc, country))
                elif country in self.global_countries:
                    c.execute('INSERT OR IGNORE INTO global_hs_codes (hs_code, description, country) VALUES (?, ?, ?)', (hs_code, desc, country))
                else:
                    QMessageBox.warning(self, "Unknown Country", "Selected country is not in Asia or Global lists.")
                    conn.close()
                    return
                conn.commit()
                conn.close()
                self.do_search()  # Refresh table
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Error adding HS code: {e}")
    def do_search(self):
        country = self.country_combo.currentText().strip()
        query = self.hs_input.text().strip().lower()
        if not country:
            QMessageBox.warning(self, "Missing Country", "Please select a country.")
            return
        # 1. Search in asia_hs_codes/global_hs_codes
        results = []
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'data', 'results.db'))
            c = conn.cursor()
            if country == "All":
                # All countries: show all HS codes from both tables
                c.execute('SELECT hs_code, description, country FROM asia_hs_codes ORDER BY created_at DESC')
                rows = c.fetchall()
                results.extend({'hs_code': row[0], 'description': row[1], 'country': row[2]} for row in rows)
                c.execute('SELECT hs_code, description, country FROM global_hs_codes ORDER BY created_at DESC')
                rows = c.fetchall()
                results.extend({'hs_code': row[0], 'description': row[1], 'country': row[2]} for row in rows)
            else:
                if country in self.asia_countries:
                    c.execute('SELECT hs_code, description, country FROM asia_hs_codes WHERE country = ? ORDER BY created_at DESC', (country,))
                    rows = c.fetchall()
                    results.extend({'hs_code': row[0], 'description': row[1], 'country': row[2]} for row in rows)
                if country in self.global_countries:
                    c.execute('SELECT hs_code, description, country FROM global_hs_codes WHERE country = ? ORDER BY created_at DESC', (country,))
                    rows = c.fetchall()
                    results.extend({'hs_code': row[0], 'description': row[1], 'country': row[2]} for row in rows)
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error fetching HS codes: {e}")
            return
        # 2. Filter by code/description
        filtered = [row for row in results if query in row['hs_code'].lower() or query in row['description'].lower()]
        self.populate_table(filtered)
        # 3. If no results, offer DeepSeek
        if not filtered and country != "All":
            reply = QMessageBox.question(self, "No Results", "No results found. Would you like to use DeepSeek AI to search for the HS Code?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.run_deepseek(country, query)
    def run_deepseek(self, country, query):
        # Show loading dialog
        self.loading_dialog = QMessageBox(self)
        self.loading_dialog.setWindowTitle("Loading...")
        self.loading_dialog.setText("Searching DeepSeek. Please wait...")
        self.loading_dialog.setStandardButtons(QMessageBox.NoButton)
        self.loading_dialog.setModal(True)
        self.loading_dialog.show()
        # Start worker thread
        self.deepseek_thread = DeepSeekWorker(country, query)
        self.deepseek_thread.result_ready.connect(self.on_deepseek_result)
        self.deepseek_thread.error.connect(self.on_deepseek_error)
        self.deepseek_thread.start()
    def on_deepseek_result(self, results):
        if self.loading_dialog:
            self.loading_dialog.hide()
        self.populate_table(results)
        self.deepseek_thread = None
    def on_deepseek_error(self, error_msg):
        if self.loading_dialog:
            self.loading_dialog.hide()
        QMessageBox.critical(self, "DeepSeek Error", f"Error calling DeepSeek: {error_msg}")
        self.deepseek_thread = None
    def populate_table(self, data):
        self.table.setRowCount(len(data))
        for row, rowdata in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(rowdata['hs_code']))
            self.table.setItem(row, 1, QTableWidgetItem(rowdata.get('country', '')))
            self.table.setItem(row, 2, QTableWidgetItem(rowdata['description']))
            # Actions: QToolButton with emoji and spacing
            action_widget = QWidget()
            hbox = QHBoxLayout()
            hbox.setContentsMargins(8, 0, 8, 0)
            hbox.setSpacing(8)
            hbox.setAlignment(Qt.AlignLeft)
            edit_btn = QToolButton()
            delete_btn = QToolButton()
            edit_btn.setText('✏️')
            delete_btn.setText('🗑️')
            edit_btn.setToolTip('Edit')
            delete_btn.setToolTip('Delete')
            edit_btn.setFixedSize(32, 32)
            delete_btn.setFixedSize(32, 32)
            edit_btn.setStyleSheet('QToolButton { border: none; background: transparent; font-size: 18px; } QToolButton:hover { background: #e0e4ea; }')
            delete_btn.setStyleSheet('QToolButton { border: none; background: transparent; font-size: 18px; } QToolButton:hover { background: #ffeaea; }')
            edit_btn.clicked.connect(lambda checked, r=row: self.edit_hs_code(r))
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_hs_code(r))
            hbox.addWidget(edit_btn)
            hbox.addWidget(delete_btn)
            action_widget.setLayout(hbox)
            action_widget.setStyleSheet("background: transparent;")
            self.table.setCellWidget(row, 3, action_widget)
    def edit_hs_code(self, row):
        country = self.country_combo.currentText().strip()
        hs_code = self.table.item(row, 0).text()
        desc = self.table.item(row, 2).text() # Changed from 1 to 2
        dialog = EditHSCodeDialog(self, country, hs_code, desc)
        new_code, new_desc = dialog.get_data()
        if new_code and new_desc and (new_code != hs_code or new_desc != desc):
            try:
                conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'data', 'results.db'))
                c = conn.cursor()
                if country in self.asia_countries:
                    c.execute('UPDATE asia_hs_codes SET hs_code = ?, description = ? WHERE hs_code = ? AND country = ?', (new_code, new_desc, hs_code, country))
                elif country in self.global_countries:
                    c.execute('UPDATE global_hs_codes SET hs_code = ?, description = ? WHERE hs_code = ? AND country = ?', (new_code, new_desc, hs_code, country))
                conn.commit()
                conn.close()
                self.do_search()
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Error editing HS code: {e}")
    def delete_hs_code(self, row):
        country = self.country_combo.currentText().strip()
        hs_code = self.table.item(row, 0).text()
        desc = self.table.item(row, 2).text() # Changed from 1 to 2
        confirm = QMessageBox.question(self, "Delete HS Code", f"Delete HS code {hs_code} for {country}?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'data', 'results.db'))
                c = conn.cursor()
                if country in self.asia_countries:
                    c.execute('DELETE FROM asia_hs_codes WHERE hs_code = ? AND country = ?', (hs_code, country))
                elif country in self.global_countries:
                    c.execute('DELETE FROM global_hs_codes WHERE hs_code = ? AND country = ?', (hs_code, country))
                conn.commit()
                conn.close()
                self.do_search()
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Error deleting HS code: {e}")

    def apply_theme(self, theme):
        self.theme = theme
        self.setStyleSheet(self.zen_stylesheet(theme))

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
        lbl.setAlignment(Qt.AlignCenter)
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
            lbl.setAlignment(Qt.AlignCenter)
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
        for i, btn in enumerate(self.nav_buttons):
            btn.setEnabled(i != index)

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
            self.sidebar.setStyleSheet(f"background: {theme['divider']};")
            for btn in self.nav_buttons:
                btn.setStyleSheet(f"background: {theme['background']}; color: {theme['primary_text']}; border: none; padding: 10px; border-radius: 6px; text-align: left;")
            self.toggle_btn.setStyleSheet(f"background: {theme['primary_accent']}; color: white; border: none; padding: 10px; border-radius: 6px;")
            self.stack.setStyleSheet(f"background: {theme['background']}; color: {theme['primary_text']};")
            self.setStyleSheet(f"QMainWindow {{ background: {theme['background']}; }}")
        else:
            theme = DARK_THEME
            self.sidebar.setStyleSheet(f"background: {theme['surface']};")
            for btn in self.nav_buttons:
                btn.setStyleSheet(f"background: {theme['surface']}; color: {theme['primary_text']}; border: none; padding: 10px; border-radius: 6px; text-align: left;")
            self.toggle_btn.setStyleSheet(f"background: {theme['primary_accent']}; color: {theme['primary_text']}; border: none; padding: 10px; border-radius: 6px;")
            self.stack.setStyleSheet(f"background: {theme['background']}; color: {theme['primary_text']};")
            self.setStyleSheet(f"QMainWindow {{ background: {theme['background']}; }}")
        # Update HSCodePage theme if it exists
        if hasattr(self, 'hs_code_page'):
            self.hs_code_page.apply_theme(self.theme)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 