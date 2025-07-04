from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QFileDialog, QVBoxLayout,
    QWidget, QLabel, QComboBox, QHBoxLayout, QDialog, QCheckBox
)
from data_loader import load_csv_data
from label_manager import LabelManager
from chart_view import CandlestickChart
from indicator_dialog import IndicatorManagerDialog
from label_manager import (
    save_labeled_data
)

import pandas as pd

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Trading Labeling Assistant")
        self.resize(1400, 900)

        self.chart = CandlestickChart(self)
        self.label_manager = LabelManager(self.chart)
        self.chart.label_manager = self.label_manager

        self.load_default_indicator_template()

        self.label = QLabel("Загрузите CSV с историей торгов")
        self.tf_selector = QComboBox()
        self.tf_selector.addItems(["4h", "1d", "1w"])
        self.tf_selector.currentTextChanged.connect(self.update_plot)

        self.load_button = QPushButton("Загрузить CSV")
        self.load_button.clicked.connect(self.load_csv)

        self.save_button = QPushButton("Сохранить CSV с метками")
        self.save_temp_button = QPushButton("💾 Сохранить разметку")
        self.load_temp_button = QPushButton("📂 Загрузить разметку")

        self.save_button.clicked.connect(self.save_csv)
        self.save_temp_button.clicked.connect(self.save_label_session)
        self.load_temp_button.clicked.connect(self.load_label_session)

        self.indicator_button = QPushButton("Настроить индикаторы")
        self.indicator_button.clicked.connect(self.configure_indicators)

        self.prev_button = QPushButton("← Назад")
        self.prev_button.clicked.connect(self.scroll_left)

        self.next_button = QPushButton("Вперёд →")
        self.next_button.clicked.connect(self.scroll_right)

        # self.label_manager.autoload_labels('labels_autosave.csv')


        top_layout = QHBoxLayout()
        top_layout.addWidget(self.load_button)
        top_layout.addWidget(self.prev_button)
        top_layout.addWidget(self.tf_selector)
        top_layout.addWidget(self.next_button)
        top_layout.addWidget(self.save_button)
        top_layout.addWidget(self.save_temp_button)
        top_layout.addWidget(self.load_temp_button)
        top_layout.addWidget(self.indicator_button)

        # Добавляем шаблоны после основного набора
        self.save_template_button = QPushButton("💾 Шаблон индикаторов")
        self.load_template_button = QPushButton("📂 Загрузить шаблон")

        self.save_template_button.clicked.connect(self.save_indicator_template)
        self.load_template_button.clicked.connect(self.load_indicator_template)

        top_layout.addWidget(self.save_template_button)
        top_layout.addWidget(self.load_template_button)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addLayout(top_layout)
        layout.addWidget(self.chart)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.data = None

    def configure_indicators(self):
        dialog = IndicatorManagerDialog(self.chart.indicator_config, self)
        if dialog.exec_():
            self.chart.indicator_config = dialog.get_updated_config()
            self.chart._plot_window()

    from data_loader import load_csv_data  # Убедись, что импорт есть

    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите CSV файл", "", "CSV Files (*.csv)")
        if not file_path:
            return

        try:
            df = load_csv_data(file_path)  # ✅ Универсальная загрузка

            self.data = df.copy()
            self.label.setText(f"Файл загружен: {file_path.split('/')[-1]}\nСтрок: {len(df)}")
            self.label_manager.clear()

            # 🟢 Загрузка меток из колонок Label и LabelPrice, если они есть
            if 'Label' in df.columns and 'LabelPrice' in df.columns:
                self.label_manager.load_labels_from_dataframe(df)

            # ⏬ Отрисовка
            self.chart.plot(df, tf=self.tf_selector.currentText())
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

    def closeEvent(self, event):
        self.label_manager.autosave_labels('labels_autosave.csv')
        event.accept()

    def save_label_session(self):
        from PyQt5.QtWidgets import QFileDialog
        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить разметку", "labels_stage1.csv", "CSV (*.csv)")
        if filepath:
            self.label_manager.save_label_session(filepath)

    def load_label_session(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Загрузить разметку", "", "CSV (*.csv)")
        if filepath:
            self.label_manager.load_label_session(filepath)
            self.chart.plot(self.chart.original_data, self.chart.current_tf)

    def save_csv(self):
        # Получаем все доступные колонки из графика
        all_columns = list(self.chart.data.columns) + ['Label', 'LabelPrice']

        dialog = ColumnSelectionDialog(all_columns, self)
        if dialog.exec_():
            selected_columns = dialog.get_selected_columns()
            if selected_columns:
                filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "labeled_data.csv",
                                                          "CSV Files (*.csv)")
                if filepath:
                    save_labeled_data(self.chart, filepath, selected_columns)

    def save_indicator_template(self):
        from indicator_utils import save_indicator_template
        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить шаблон индикаторов", "indicators_template.json",
                                                  "JSON Files (*.json)")
        if filepath:
            save_indicator_template(self.chart.indicator_config, filepath)

    def load_indicator_template(self):
        from indicator_utils import load_indicator_template
        filepath, _ = QFileDialog.getOpenFileName(self, "Загрузить шаблон индикаторов", "", "JSON Files (*.json)")
        if filepath:
            config = load_indicator_template(filepath)
            if config:
                self.chart.indicator_config = config
                self.chart._plot_window()

    def load_default_indicator_template(self):
        from indicator_utils import load_indicator_template
        import os

        candidates = [
            "default.json",
            os.path.join("templates", "default.json")
        ]

        for path in candidates:
            if os.path.exists(path):
                config = load_indicator_template(path)
                if config:
                    self.chart.indicator_config = config
                    print(f"[AUTO] Применён шаблон индикаторов: {path}")
                    break
class ColumnSelectionDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор колонок для экспорта")
        self.selected_columns = []

        layout = QVBoxLayout(self)
        self.checkboxes = []
        for col in columns:
            cb = QCheckBox(col)
            cb.setChecked(True)
            layout.addWidget(cb)
            self.checkboxes.append(cb)

        btn_ok = QPushButton("Сохранить")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)

    def get_selected_columns(self):
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]