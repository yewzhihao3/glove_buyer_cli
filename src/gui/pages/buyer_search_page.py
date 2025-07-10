from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt


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
        self.country_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.country_combo.setPlaceholderText("Country")
        # Placeholder country list
        self.country_combo.addItems(["", "USA", "UK", "China", "Malaysia", "Germany"])
        self.hs_code_combo = QComboBox()
        self.hs_code_combo.setEditable(True)
        self.hs_code_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
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
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
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