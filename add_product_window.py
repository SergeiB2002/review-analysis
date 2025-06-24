from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSignal
import numpy as np
from db import db

class AddProductWindow(QWidget):
    window_closed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.sources = np.array(db.select_sources())
        self.cur_source_id = self.sources[0][0]
        self.categories = np.array(db.select_categories())
        self.cur_category_id = self.categories[0][0]
        self.init_UI()
        
    def init_UI(self):
        self.setWindowTitle('Добавить продукт')
        self.setGeometry(200, 200, 400, 300)
        layout = QVBoxLayout()
        
        label_font = QFont()
        label_font.setPointSize(13)
         
        self.product_name_label = QLabel("Название продукта:")
        self.product_name_label.setFont(label_font)
        self.product_name_input = QLineEdit()
        self.product_name_input.setStyleSheet("QLineEdit { font-size: 15px; margin-bottom: 20px;}")
        layout.addWidget(self.product_name_label)
        layout.addWidget(self.product_name_input)
        
        self.source_label = QLabel("Источник:")
        self.source_label.setFont(label_font)
        
        self.source_combobox = QComboBox()
        self.source_combobox.setStyleSheet("QComboBox { font-size: 15px; margin-bottom: 20px;}")
        self.source_combobox.addItems(self.sources[:, 1]) 
        self.source_combobox.currentIndexChanged.connect(self.source_changed)
        
        self.caategory_label = QLabel("Категория:")
        self.caategory_label.setFont(label_font)
        
        self.caategory_combobox = QComboBox()
        self.caategory_combobox.setStyleSheet("QComboBox { font-size: 15px; margin-bottom: 20px;}")
        self.caategory_combobox.addItems(self.categories[:, 1]) 
        self.caategory_combobox.currentIndexChanged.connect(self.category_changed)
        
        
        layout.addWidget(self.source_label)
        layout.addWidget(self.source_combobox)
        
        layout.addWidget(self.caategory_label)
        layout.addWidget(self.caategory_combobox)
        
        self.url_label = QLabel("URL страницы отзывов:")
        self.url_label.setFont(label_font)
        self.url_input = QLineEdit()
        self.url_input.setStyleSheet("QLineEdit { font-size: 15px; margin-bottom: 20px;}")
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.setFixedSize(150, 30)
        self.save_button.setStyleSheet("QPushButton { font-size: 15px; }")
        self.save_button.clicked.connect(self.save)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setFixedSize(150, 30)
        self.cancel_button.setStyleSheet("QPushButton { font-size: 15px; }")
        self.cancel_button.clicked.connect(self.cancel)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def cancel(self):
        self.close()
    
    def source_changed(self):
        self.cur_source_id = self.sources[self.source_combobox.currentIndex(), 0]
    
    def category_changed(self):
        self.cur_category_id = self.categories[self.caategory_combobox.currentIndex(), 0]
    
    def save(self):
        if(self.product_name_input.text() == "" or self.url_input.text() == ""):
            self.error_message("Введите данные")
            return
        try:
            db.insert_product(self.product_name_input.text(), self.url_input.text(), self.cur_source_id, self.cur_category_id)
            self.succes_message()
            self.close()
        except Exception as e:
            self.error_message(str(e))
            return
        
    def succes_message(self):
        success_dialog = QMessageBox()
        success_dialog.setIcon(QMessageBox.Information)
        success_dialog.setWindowTitle("Успех")
        success_dialog.setText("Операция выполнена успешно.")
        success_dialog.setStandardButtons(QMessageBox.Ok)
        success_dialog.exec_()
        
    def error_message(self, message):
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Ошибка")
        error_dialog.setText(f"Произошла ошибка: {message}")
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.exec_()
    
    def closeEvent(self, event):
        self.window_closed.emit()  
        event.accept()