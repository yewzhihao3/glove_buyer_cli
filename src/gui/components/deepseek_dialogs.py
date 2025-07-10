from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QScrollArea, QCheckBox, QPushButton, QLabel, QWidget
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QProgressDialog, QMessageBox
from deepseek_agent import query_deepseek_for_hs_codes, parse_hs_codes_from_deepseek
from GUI_db import save_hs_code

# Dialog for selecting which DeepSeek results to save
class DeepSeekSaveDialog(QDialog):
    def __init__(self, parent, parsed, country):
        super().__init__(parent)
        self.setWindowTitle("Save DeepSeek HS Codes")
        self.setMinimumSize(650, 480)
        self.setStyleSheet("""
            QDialog {
                background: #f8fafc;
                border-radius: 18px;
                border: 1px solid #e0e4ea;
                padding: 0px;
            }
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #2E3A59;
                margin-bottom: 8px;
            }
            QCheckBox {
                font-size: 15px;
                padding: 12px 10px 12px 0px;
                border-radius: 8px;
                background: transparent;
            }
            QCheckBox:hover {
                background: #e0e4ea;
            }
            QPushButton {
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 16px;
                font-weight: 600;
                margin: 0 8px;
            }
            QPushButton#primaryBtn {
                background: #0078D4;
                color: white;
                border: none;
            }
            QPushButton#primaryBtn:hover {
                background: #005fa3;
            }
            QPushButton#secondaryBtn {
                background: #6B7C93;
                color: white;
                border: none;
            }
            QPushButton#secondaryBtn:hover {
                background: #5A6B82;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        self.parsed = parsed
        self.country = country
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(18)
        layout.addWidget(QLabel(f"Select which HS codes to save for {country}:"))
        # Select All checkbox
        self.select_all = QCheckBox("Select All")
        self.select_all.stateChanged.connect(self.toggle_all)
        layout.addWidget(self.select_all)
        # Scroll area for checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        vbox = QVBoxLayout()
        vbox.setSpacing(10)
        self.checkboxes = []
        for row in parsed:
            cb = QCheckBox(f"HS Code: {row['hs_code']}\nDescription: {row['description']}")
            cb.setChecked(True)
            self.checkboxes.append(cb)
            vbox.addWidget(cb)
        inner.setLayout(vbox)
        scroll.setWidget(inner)
        layout.addWidget(scroll, stretch=1)
        # Save/Cancel buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        save_btn = QPushButton("Save Selected")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)
        self.setLayout(layout)
        
        # Cursor setting removed due to linter compatibility issues
        
    def toggle_all(self, state):
        for cb in self.checkboxes:
            cb.setChecked(state == 2)
            
    def get_selected(self):
        return [row for row, cb in zip(self.parsed, self.checkboxes) if cb.isChecked()]


class DeepSeekWorker(QThread):
    result_ready = Signal(list)
    error = Signal(str)
    
    def __init__(self, country, query):
        super().__init__()
        self.country = country
        self.query = query
        
    def run(self):
        try:
            output = query_deepseek_for_hs_codes(self.country)
            parsed = parse_hs_codes_from_deepseek(output)
            # Optionally, filter DeepSeek results by query
            filtered_parsed = [row for row in parsed if self.query in row['hs_code'].lower() or self.query in row['description'].lower()]
            self.result_ready.emit(filtered_parsed)
        except Exception as e:
            self.error.emit(str(e))


class AddDeepSeekWorker(QThread):
    result_ready = Signal(list)
    error = Signal(str)
    
    def __init__(self, country):
        super().__init__()
        self.country = country
        
    def run(self):
        try:
            output = query_deepseek_for_hs_codes(self.country)
            parsed = parse_hs_codes_from_deepseek(output)
            self.result_ready.emit(parsed)
        except Exception as e:
            self.error.emit(str(e)) 