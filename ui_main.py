from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QFileDialog, QVBoxLayout,
    QWidget, QLabel, QComboBox, QHBoxLayout
)
from data_loader import load_csv_data
from label_manager import LabelManager
from chart_view import CandlestickChart
import pandas as pd

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading Labeling Assistant")
        self.resize(1400, 900)

        self.chart = CandlestickChart(self)
        self.label_manager = LabelManager(self.chart)
        self.chart.label_manager = self.label_manager

        self.label = QLabel("Загрузите CSV с историей торгов")
        self.tf_selector = QComboBox()
        self.tf_selector.addItems(["4h", "1d", "1w"])
        self.tf_selector.currentTextChanged.connect(self.update_plot)

        self.load_button = QPushButton("Загрузить CSV")
        self.load_button.clicked.connect(self.load_csv)

        self.save_button = QPushButton("Сохранить разметку")
        self.save_button.clicked.connect(self.save_labels)

        self.prev_button = QPushButton("← Назад")
        self.prev_button.clicked.connect(self.scroll_left)

        self.next_button = QPushButton("Вперёд →")
        self.next_button.clicked.connect(self.scroll_right)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.load_button)
        top_layout.addWidget(self.prev_button)
        top_layout.addWidget(self.tf_selector)
        top_layout.addWidget(self.next_button)
        top_layout.addWidget(self.save_button)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addLayout(top_layout)
        layout.addWidget(self.chart)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.data = None

    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите CSV файл", "", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            self.data = load_csv_data(file_path)
            self.label.setText(f"Файл загружен: {file_path.split('/')[-1]}\nСтрок: {len(self.data)}")
            self.label_manager.clear()
            self.update_plot()
        except Exception as e:
            self.label.setText(f"Ошибка при загрузке: {str(e)}")

    def update_plot(self):
        if self.data is not None:
            tf = self.tf_selector.currentText()
            self.chart.plot(self.data, tf)

    def scroll_left(self):
        self.chart.scroll_view(-1)

    def scroll_right(self):
        self.chart.scroll_view(1)

    def save_labels(self):
        if self.label_manager.labels.empty:
            self.label.setText("Нет меток для сохранения.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить как", "labels.csv", "CSV Files (*.csv)")
        if file_path:
            self.label_manager.labels.to_csv(file_path, index=False)
            self.label.setText(f"Сохранено: {file_path}")
