from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt
from GUI_db import (
    save_hs_code, update_hs_code, delete_hs_code, get_all_hs_codes, 
    get_hs_codes_by_country, init_db, get_all_available_countries
)
from ..components.hs_code_dialogs import AddHSCodeDialog, EditHSCodeDialog
from ..components.deepseek_dialogs import DeepSeekWorker


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
        card_layout.addWidget(self.add_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)
        self.country_combo = QComboBox()
        self.country_combo.setEditable(False)
        self.country_combo.setPlaceholderText("Country")
        self.country_combo.addItem("All")
        self.country_combo.addItem("")
        # Initialize database and populate from unified country list
        init_db()
        all_countries = get_all_available_countries()
        for country in all_countries:
            self.country_combo.addItem(country)
        self.hs_input = QLineEdit()
        self.hs_input.setPlaceholderText("Enter HS code or description...")
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.do_search)
        self.search_btn.setObjectName("primaryBtn")
        self.refresh_btn = QPushButton("Refresh Table")
        self.refresh_btn.clicked.connect(self.do_search)
        self.refresh_btn.setObjectName("secondaryBtn")
        search_layout.addWidget(self.country_combo)
        search_layout.addWidget(self.hs_input)
        search_layout.addWidget(self.search_btn)
        search_layout.addWidget(self.refresh_btn)
        card_layout.addLayout(search_layout)
        # Results table (remove Actions column)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["HS Code", "Country", "Description"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setObjectName("zenTable")
        card_layout.addWidget(self.table)
        
        # Action buttons below table
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)
        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.edit_selected_hs_code)
        self.edit_btn.setObjectName("secondaryBtn")
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_selected_hs_code)
        self.delete_btn.setObjectName("dangerBtn")
        action_layout.addWidget(self.edit_btn)
        action_layout.addWidget(self.delete_btn)
        action_layout.addStretch(1)
        card_layout.addLayout(action_layout)
        card.setLayout(card_layout)
        outer_layout.addWidget(card)
        self.setLayout(outer_layout)
        self.populate_table([])
        self.loading_dialog = None
        self.deepseek_thread = None
        self.theme = 'light'  # Track current theme
        self.setStyleSheet(self.zen_stylesheet(self.theme))
        
        # Cursor setting removed due to linter compatibility issues
        # Hover effects in stylesheet provide excellent visual feedback
        
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
            QPushButton#secondaryBtn {
                background: #6B7C93;
                color: #E0E4EA;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton#secondaryBtn:hover {
                background: #5A6B82;
            }
            QPushButton#dangerBtn {
                background: #DC3545;
                color: #E0E4EA;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton#dangerBtn:hover {
                background: #C82333;
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
            QPushButton#secondaryBtn {
                background: #6B7C93;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton#secondaryBtn:hover {
                background: #5A6B82;
            }
            QPushButton#dangerBtn {
                background: #DC3545;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton#dangerBtn:hover {
                background: #C82333;
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
                if save_hs_code(hs_code, desc, country):
                    self.do_search()  # Refresh table
                else:
                    QMessageBox.warning(self, "Duplicate", "This HS code for the selected country already exists.")
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Error adding HS code: {e}")
                
    def do_search(self):
        country = self.country_combo.currentText().strip()
        query = self.hs_input.text().strip().lower()
        if not country:
            QMessageBox.warning(self, "Missing Country", "Please select a country.")
            return
        # 1. Search in unified hs_codes table
        results = []
        try:
            if country == "All":
                results = get_all_hs_codes()
            else:
                results = get_hs_codes_by_country(country)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error fetching HS codes: {e}")
            return
        # 2. Filter by code/description
        filtered = [row for row in results if query in row['hs_code'].lower() or query in row['description'].lower()]
        self.populate_table(filtered)
        # 3. No DeepSeek prompt needed; handled in Add HS Code dialog
        
    def run_deepseek(self, country, query):
        # Show loading dialog
        self.loading_dialog = QMessageBox(self)
        self.loading_dialog.setWindowTitle("Loading...")
        self.loading_dialog.setText("Searching DeepSeek. Please wait...")
        self.loading_dialog.setStandardButtons(QMessageBox.StandardButton.NoButton)
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
            
    def edit_selected_hs_code(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a row to edit.")
            return
        self.edit_hs_code(current_row)
        
    def delete_selected_hs_code(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a row to delete.")
            return
        self.delete_hs_code(current_row)
        
    def edit_hs_code(self, row):
        old_country = self.table.item(row, 1).text()
        hs_code = self.table.item(row, 0).text()
        desc = self.table.item(row, 2).text()
        dialog = EditHSCodeDialog(self, old_country, hs_code, desc)
        new_code, new_desc, new_country = dialog.get_data()
        if new_code and new_desc and new_country and (new_code != hs_code or new_desc != desc or new_country != old_country):
            try:
                # Find the row id (if needed, you can pass it around or look it up)
                # For now, just update by old values
                # You may want to add a get_hs_code_id(hs_code, country) helper
                # For now, just update all matching
                all_codes = get_all_hs_codes()
                match = next((row for row in all_codes if row['hs_code'] == hs_code and row['country'] == old_country), None)
                if match:
                    update_hs_code(match['id'], new_code, new_desc, new_country)
                    self.do_search()
                else:
                    QMessageBox.warning(self, "Not Found", "Could not find the original HS code to update.")
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Error editing HS code: {e}")
                
    def delete_hs_code(self, row):
        country = self.table.item(row, 1).text()
        hs_code = self.table.item(row, 0).text()
        desc = self.table.item(row, 2).text()
        confirm = QMessageBox.question(self, "Delete HS Code", f"Delete HS code {hs_code} for {country}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                # Find the row id
                all_codes = get_all_hs_codes()
                match = next((row for row in all_codes if row['hs_code'] == hs_code and row['country'] == country), None)
                if match:
                    delete_hs_code(match['id'])
                    self.do_search()
                else:
                    QMessageBox.warning(self, "Not Found", "Could not find the HS code to delete.")
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Error deleting HS code: {e}")

    def apply_theme(self, theme):
        self.theme = theme
        self.setStyleSheet(self.zen_stylesheet(theme)) 