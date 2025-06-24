import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant
import numpy as np
from db import db
from add_product_window import AddProductWindow
from parser_1 import Parser 
from analyzer import Analyzer


class MainApp(QWidget):
    products = None
    cur_product = None
    cur_aspect = None
    add_window = None
    model = None
    feedback = None
    
    def __init__(self):
        super().__init__()
        self.initUI()
        self.show()
        
    def parse(self):
        try: 
            if(self.cur_product[3] == 1):
                comments = Parser.parse_ym(self.cur_product[2])
            db.insert_feedback(self.cur_product[0], comments)
            db.set_collecting_time(self.cur_product[0])
            self.succes_message()
        except Exception as ex:
            self.error_message()
        
    def analyze(self):
        try: 
            feedback = db.select_feedback(self.cur_product[0])
            termins = Analyzer.get_termins(feedback)
            aspects = Analyzer.get_significant_termins(termins)
            db.insert_aspects(self.cur_product[0], aspects)
            aspects = db.select_aspects(self.cur_product[0])
            tonal = Analyzer.extraxt_tonal(feedback, aspects)
            prev_tonal = db.select_tonality_category(self.cur_product[4])
            classes = Analyzer.classify_tonality(prev_tonal, tonal)
            db.insert_tonality(classes)
            helpfullness = Analyzer.predict_helpfullness(feedback)
            db.update_helpfullness(feedback, helpfullness)
            
            self.get_aspects()
            self.succes_message()
            self.get_aspects()
        except Exception as ex:
            self.error_message(str(ex)) 
            raise ex 
        
    def initUI(self):
        
        self.setWindowTitle("Анализ отзывов")
        self.setGeometry(400, 250, 900, 600)
        
        #инициализация лэйаутов
        main_layout = QVBoxLayout()
        header_layout = QVBoxLayout()
        subheader_layout = QHBoxLayout()
        menu_layout = QVBoxLayout()
        prod_layout = QHBoxLayout()
        polarity_layout = QHBoxLayout()
        table_layout = QVBoxLayout()
        actions_layout = QHBoxLayout()
        
        #шрифты
        label_font = QFont()
        label_font.setPointSize(13)
        
        #заголовок
        prod_label = QLabel("Выберите продукт")
        prod_label.setFont(label_font)
        
        self.products_combo_box = QComboBox()
        self.get_products()
        self.products_combo_box.setStyleSheet("QComboBox { font-size: 14px;  padding: 3px}")
        self.products_combo_box.setFixedWidth(250)
        self.products_combo_box.currentIndexChanged.connect(self.product_changed)
        
        add_product_btn = QPushButton("Добавить продукт")
        add_product_btn.setFixedSize(120, 30)
        add_product_btn.setStyleSheet("QPushButton { font-size: 13px;}")
        add_product_btn.clicked.connect(self.open_add_window)

        aspect_label = QLabel("Выберите аспект")
        aspect_label.setStyleSheet("QLabel {margin-top: 10px;}")
        aspect_label.setFont(label_font)
        
        self.aspects_combo_box = QComboBox()
        self.aspects_combo_box.addItem("Экран")
        self.get_aspects()
        self.aspects_combo_box.setStyleSheet("QComboBox { font-size: 15px; margin-bottom: 20px; padding: 5px;}")
        self.aspects_combo_box.setFixedWidth(250)
        self.aspects_combo_box.currentIndexChanged.connect(self.aspect_changed)


        #радиокнопки
        self.positive_radio_btn = QRadioButton("Положительные")
        self.positive_radio_btn.setChecked(True)
        self.positive_radio_btn.clicked.connect(self.draw_results)
        self.negative_radio_btn = QRadioButton("Отрицательные")
        self.neutral_radio_btn = QRadioButton("Нейтральные")
        self.negative_radio_btn.clicked.connect(self.draw_results)
        self.neutral_radio_btn.clicked.connect(self.draw_results)

        #таблица
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.feedback = db.select_result(self.cur_product[0], self.cur_aspect[0])
        self.draw_results()
        
        
        table_layout.addWidget(self.table)
        
        #кнопки действий
        parse_button = QPushButton("Собрать отзывы")
        analyze_button = QPushButton("Проанализировать отзывы")
        parse_button.setFixedSize(200, 50)
        analyze_button.setFixedSize(200, 50)
        
        analyze_button.clicked.connect(self.analyze)
        parse_button.clicked.connect(self.parse)
        
        menu_layout.addWidget(prod_label)
        prod_layout.addWidget(self.products_combo_box)
        prod_layout.addWidget(add_product_btn)
        menu_layout.addLayout(prod_layout)
        menu_layout.addWidget(aspect_label)
        menu_layout.addWidget(self.aspects_combo_box)
        subheader_layout.addLayout(menu_layout)
        subheader_layout.addStretch(1)
        header_layout.addLayout(subheader_layout)
        actions_layout.addWidget(parse_button)
        actions_layout.addWidget(analyze_button)
        polarity_layout.addWidget(self.positive_radio_btn)
        polarity_layout.addStretch(1)
        polarity_layout.addWidget(self.negative_radio_btn)
        polarity_layout.addStretch(1)
        polarity_layout.addWidget(self.neutral_radio_btn)
        
        main_layout.addLayout(header_layout)
        main_layout.addLayout(polarity_layout)
        main_layout.addLayout(table_layout)
        main_layout.addLayout(actions_layout)

        self.setLayout(main_layout)
    
    def open_add_window(self):
        self.add_window = AddProductWindow()
        self.add_window.window_closed.connect(self.get_products)
        self.add_window.show()

    def get_products(self):
        self.products_combo_box.clear()
        self.products = db.select_products()
        
        if(len(self.products) > 0):
            for product in self.products:
                self.products_combo_box.addItem(product[1])
            self.cur_product = self.products[0]
            
    def get_aspects(self):
        self.aspects_combo_box.clear()
        self.aspects = db.select_aspects(self.cur_product[0])
        
        if(len(self.aspects) > 0):
            for aspect in self.aspects:
                self.aspects_combo_box.addItem(aspect[2])
            self.cur_aspect = self.aspects[0]

            
    def aspect_changed(self):
        self.cur_aspect = self.aspects[self.aspects_combo_box.currentIndex()]
        self.feedback = db.select_result(self.cur_product[0], self.cur_aspect[0])
        self.draw_results()

    def draw_results(self):
        cur_ton = 0
        if(self.positive_radio_btn.isChecked()):
            cur_ton = 2
        elif(self.neutral_radio_btn.isChecked()):
            cur_ton = 1
        else:
            cur_ton = 0
        self.table.clear()
        table_data = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        for review in self.feedback:
            if review[6] == cur_ton:
                table_data.append(review[:-1])
            if review[6] == 0:
                negative_count += 1
            elif review[6] == 1:
                neutral_count += 1
            elif review[6] == 2:
                positive_count += 1
        self.positive_radio_btn.setText(f"Положительные ({positive_count})") 
        self.negative_radio_btn.setText(f"Отрицательные ({negative_count})")
        self.neutral_radio_btn.setText(f"Нейтральные ({neutral_count})")
        self.table.setRowCount(len(table_data))
        for i, review in enumerate(table_data):
            for j, el in enumerate(review):
                self.table.setItem(i, j, QTableWidgetItem(str(el)))
            self.table.setRowHeight(i, 200)
        self.table.setHorizontalHeaderLabels(["Дата", "Оценка", "Текст",
                                         "Посчитали \nполезным", 
                                         "Посчитали \nбесполезным",
                                         "Прогнозируемая \nполезность"])
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 400)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 110)
        

    def product_changed(self):
        self.cur_product = self.products[self.products_combo_box.currentIndex()]
        self.get_aspects()
            
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
