from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QDialogButtonBox, 
    QWidget, QComboBox, QTextEdit, QPushButton, QMessageBox, QProgressDialog
)
from PySide6.QtCore import Qt
from GUI_db import save_hs_code, init_db, get_all_available_countries
from .deepseek_dialogs import AddDeepSeekWorker, DeepSeekSaveDialog


class AddHSCodeDialog(QMessageBox):
    def __init__(self, parent, country):
        super().__init__(parent)
        self.setWindowTitle("Add HS Code")
        self.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        self.setDefaultButton(QMessageBox.StandardButton.Ok)
        self.country = country
        
        # Custom layout
        self.dialog = QDialog(parent)
        self.dialog.setWindowTitle("Add HS Code")
        self.dialog.setMinimumSize(800, 500)
        self.dialog.resize(800, 500)
        
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Country dropdown
        self.country_combo = QComboBox()
        # Get all countries from unified country list
        init_db()
        all_countries = get_all_available_countries()
        self.country_combo.addItems(all_countries)
        if country in all_countries:
            self.country_combo.setCurrentText(country)
        self.country_combo.setMinimumHeight(36)
        self.country_combo.setStyleSheet("font-size: 14px; padding: 6px 10px; border-radius: 8px;")
        layout.addWidget(QLabel("Country:"))
        layout.addWidget(self.country_combo)
        
        # HS Code section
        layout.addWidget(QLabel("HS Code:"))
        self.hs_code_input = QLineEdit()
        self.hs_code_input.setPlaceholderText("Enter HS Code")
        self.hs_code_input.setMinimumHeight(40)
        self.hs_code_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e4ea;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #0078D4;
            }
        """)
        layout.addWidget(self.hs_code_input)
        
        # Description section
        layout.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Enter description")
        self.desc_input.setMinimumHeight(120)
        self.desc_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e0e4ea;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background: white;
            }
            QTextEdit:focus {
                border-color: #0078D4;
            }
        """)
        layout.addWidget(self.desc_input)
        
        # Buttons row (OK, Cancel, DeepSeek)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.dialog.accept)
        buttons.rejected.connect(self.dialog.reject)
        buttons.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton[text="OK"] {
                background: #0078D4;
                color: white;
                border: none;
            }
            QPushButton[text="OK"]:hover {
                background: #005fa3;
            }
            QPushButton[text="Cancel"] {
                background: #6B7C93;
                color: white;
                border: none;
            }
            QPushButton[text="Cancel"]:hover {
                background: #5A6B82;
            }
        """)
        self.deepseek_btn = QPushButton("Search with DeepSeek")
        self.deepseek_btn.setStyleSheet("background: #4DA6FF; color: #121A26; border-radius: 6px; padding: 8px 20px; font-size: 14px; font-weight: 500;")
        self.deepseek_btn.clicked.connect(self.search_deepseek)
        # Layout for all buttons
        btn_row = QHBoxLayout()
        btn_row.addWidget(buttons)
        btn_row.addWidget(self.deepseek_btn)
        layout.addLayout(btn_row)
        
        self.dialog.setLayout(layout)
        
    def get_data(self):
        if self.dialog.exec() == 1:
            return self.hs_code_input.text().strip(), self.desc_input.toPlainText().strip()
        return None, None

    def search_deepseek(self):
        country = self.country_combo.currentText().strip()
        if not country:
            QMessageBox.warning(self.dialog, "Missing Country", "Please select a country to search for HS codes.")
            return
        self.deepseek_btn.setEnabled(False)
        self.deepseek_btn.setText("Searching...")
        self.progress = QProgressDialog("Searching DeepSeek for HS codes...", "Cancel", 0, 0, self.dialog)
        self.progress.setWindowTitle("DeepSeek Search")
        self.progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress.setMinimumDuration(0)
        self.progress.show()
        self.worker = AddDeepSeekWorker(country)
        self.worker.result_ready.connect(self.on_deepseek_result)
        self.worker.error.connect(self.on_deepseek_error)
        self.worker.start()

    def on_deepseek_result(self, parsed):
        self.deepseek_btn.setEnabled(True)
        self.deepseek_btn.setText("Search with DeepSeek")
        if hasattr(self, 'progress') and self.progress:
            self.progress.close()
        if not parsed:
            QMessageBox.information(self.dialog, "DeepSeek Results", "No results found from DeepSeek.")
            return
        # Show selection dialog
        dlg = DeepSeekSaveDialog(self.dialog, parsed, self.country_combo.currentText().strip())
        if dlg.exec() == 1:
            selected = dlg.get_selected()
            saved = 0
            for row in selected:
                country = self.country_combo.currentText().strip()
                if save_hs_code(row['hs_code'], row['description'], country, source='DeepSeek'):
                    saved += 1
            QMessageBox.information(self.dialog, "Saved", f"Saved {saved} HS codes to the database.")
        else:
            QMessageBox.information(self.dialog, "DeepSeek Results", "No HS codes were saved.")

    def on_deepseek_error(self, error_msg):
        self.deepseek_btn.setEnabled(True)
        self.deepseek_btn.setText("Search with DeepSeek")
        if hasattr(self, 'progress') and self.progress:
            self.progress.close()
        QMessageBox.critical(self.dialog, "DeepSeek Error", f"Error calling DeepSeek: {error_msg}")

    def closeEvent(self, event):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        if hasattr(self, 'progress') and self.progress:
            self.progress.close()
        super().closeEvent(event)


class EditHSCodeDialog(QDialog):
    def __init__(self, parent, country, hs_code, desc):
        super().__init__(parent)
        self.setWindowTitle("Edit HS Code")
        self.setFixedSize(800, 500)
        
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Country dropdown
        country_combo = QComboBox()
        # Get all countries from unified country list
        init_db()
        all_countries = get_all_available_countries()
        country_combo.addItems(all_countries)
        if country in all_countries:
            country_combo.setCurrentText(country)
        country_combo.setMinimumHeight(36)
        country_combo.setStyleSheet("font-size: 14px; padding: 6px 10px; border-radius: 8px;")
        self.country_combo = country_combo
        layout.addWidget(QLabel("Country:"))
        layout.addWidget(self.country_combo)
        
        # HS Code section
        layout.addWidget(QLabel("HS Code:"))
        self.hs_code_input = QLineEdit(hs_code)
        self.hs_code_input.setMinimumHeight(40)
        self.hs_code_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e4ea;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #0078D4;
            }
        """)
        layout.addWidget(self.hs_code_input)
        
        # Description section
        layout.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlainText(desc)
        self.desc_input.setMinimumHeight(120)
        self.desc_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e0e4ea;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background: white;
            }
            QTextEdit:focus {
                border-color: #0078D4;
            }
        """)
        layout.addWidget(self.desc_input)
        
        # Push buttons to the bottom
        layout.addStretch()
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton[text="OK"] {
                background: #0078D4;
                color: white;
                border: none;
            }
            QPushButton[text="OK"]:hover {
                background: #005fa3;
            }
            QPushButton[text="Cancel"] {
                background: #6B7C93;
                color: white;
                border: none;
            }
            QPushButton[text="Cancel"]:hover {
                background: #5A6B82;
            }
        """)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        # Cursor setting removed due to linter compatibility issues
        
    def get_data(self):
        if self.exec() == 1:
            return (
                self.hs_code_input.text().strip(),
                self.desc_input.toPlainText().strip(),
                self.country_combo.currentText().strip()
            )
        return None, None, None 