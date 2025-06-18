from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QComboBox, QColorDialog

class IndicatorManagerDialog(QDialog):
    def __init__(self, indicator_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройка индикаторов")
        self.indicator_config = indicator_config.copy()

        self.layout = QVBoxLayout(self)

        # список текущих индикаторов
        self.list_widget = QListWidget()
        self.refresh_list()
        self.layout.addWidget(self.list_widget)

        # выбор нового индикатора
        type_layout = QHBoxLayout()
        self.indicator_type = QComboBox()
        self.indicator_type.addItems(["EMA", "RSI", "WMA", "MACD", "ADX", "STOCH"])
        self.period_input = QLineEdit()
        self.period_input.setPlaceholderText("Период")
        self.axis_selector = QComboBox()
        self.axis_selector.addItems(["main", "rsi"])
        self.color_button = QPushButton("Цвет")
        self.selected_color = "black"
        self.color_button.clicked.connect(self.pick_color)

        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.add_indicator)

        type_layout.addWidget(QLabel("Тип:"))
        type_layout.addWidget(self.indicator_type)
        type_layout.addWidget(QLabel("Период:"))
        type_layout.addWidget(self.period_input)
        type_layout.addWidget(QLabel("Ось:"))
        type_layout.addWidget(self.axis_selector)
        type_layout.addWidget(self.color_button)
        type_layout.addWidget(add_button)

        self.layout.addLayout(type_layout)

        # кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        self.layout.addWidget(close_btn)

        self.setMinimumWidth(600)

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color.name()
            self.color_button.setStyleSheet(f"background-color: {self.selected_color}")

    def refresh_list(self):
        self.list_widget.clear()
        for indicator in self.indicator_config:
            item = QListWidgetItem(f"{indicator['type']}({indicator['period']}) на оси {indicator['axis']} цвет {indicator.get('color', 'black')}")
            self.list_widget.addItem(item)

    def add_indicator(self):
        ind_type = self.indicator_type.currentText()
        try:
            period = int(self.period_input.text())
        except ValueError:
            return
        axis = self.axis_selector.currentText()
        self.indicator_config.append({"type": ind_type, "period": period, "axis": axis, "color": self.selected_color})
        self.refresh_list()
        self.period_input.clear()
        self.selected_color = "black"
        self.color_button.setStyleSheet("")

    def get_updated_config(self):
        return self.indicator_config
