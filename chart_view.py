from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QSplitter
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.backend_bases import MouseEvent, MouseButton
from plot_utils import _plot_window, _draw_candles
from indicator_utils import apply_indicators


class CandlestickChart(QWidget):
    def __init__(self, parent=None, label_manager=None):
        super().__init__(parent)

        # ==== Верхний график: свечи и EMA ====
        self.candle_fig = Figure(figsize=(12, 5), constrained_layout=True)
        self.candle_canvas = FigureCanvas(self.candle_fig)
        self.candle_toolbar = NavigationToolbar2QT(self.candle_canvas, self)
        self.axes = self.candle_fig.add_subplot(111)

        candle_widget = QWidget()
        candle_layout = QVBoxLayout(candle_widget)
        candle_layout.setContentsMargins(0, 0, 0, 0)
        candle_layout.addWidget(self.candle_toolbar)
        candle_layout.addWidget(self.candle_canvas)

        # ==== Нижний график: RSI ====
        self.rsi_fig = Figure(figsize=(12, 3), constrained_layout=True)
        self.rsi_canvas = FigureCanvas(self.rsi_fig)
        self.rsi_axes = self.rsi_fig.add_subplot(111)

        rsi_widget = QWidget()
        rsi_layout = QVBoxLayout(rsi_widget)
        rsi_layout.setContentsMargins(0, 0, 0, 0)
        rsi_layout.addWidget(self.rsi_canvas)

        # ==== QSplitter: делает оба окна раздвигаемыми ====
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(candle_widget)
        splitter.addWidget(rsi_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        # ==== Общий layout ====
        layout = QVBoxLayout(self)
        layout.addWidget(splitter)
        self.setLayout(layout)

        # ==== Служебные переменные ====
        self.candle_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.rsi_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.label_manager = label_manager
        self.candle_canvas.mpl_connect("button_press_event", self.onclick)
        self.candle_canvas.mpl_connect("scroll_event", self.on_scroll)
        self.candle_canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.candle_canvas.mpl_connect("button_release_event", self.on_mouse_release)

        self.data = None
        self.original_data = None
        self.current_tf = "4h"
        self.view_start_index = 0
        self.view_window_size = 200

        self._dragging = False
        self._drag_start_x = None

        self.indicator_config = []

    def scroll_view(self, direction):
        if self.data is None:
            return
        max_index = len(self.data) - self.view_window_size
        self.view_start_index = max(0, min(self.view_start_index + direction, max_index))
        self._plot_window()

    def plot(self, df, tf):
        self.original_data = df.copy()
        self.current_tf = tf
        if self.data is None:
            self.view_start_index = 0
        self._plot_window()

    def _plot_window(self):
        if self.original_data is None:
            return
        self.data = self.original_data.copy()
        self.data = apply_indicators(self.data, self.indicator_config)
        _plot_window(self)

    def onclick(self, event: MouseEvent):
        if self.data is None or event.inaxes != self.axes:
            return
        if event.button == MouseButton.RIGHT:
            index = round(event.xdata)
            if 0 <= index < len(self.data):
                row = self.data.iloc[self.view_start_index + index]
                self.label_manager.handle_click(row, lambda: self._plot_window())
        elif event.button == MouseButton.LEFT:
            self._dragging = True
            self._drag_start_x = event.xdata

    def on_mouse_release(self, event):
        self._dragging = False
        self._drag_start_x = None

    def on_mouse_move(self, event):
        if not self._dragging or event.xdata is None:
            return
        dx = event.xdata - self._drag_start_x
        bars_to_shift = int(-dx)
        if bars_to_shift != 0:
            self.scroll_view(bars_to_shift)
            self._drag_start_x = event.xdata

    def on_scroll(self, event):
        if event.button == 'up':
            self.view_window_size = max(10, self.view_window_size - 10)
        elif event.button == 'down':
            self.view_window_size += 10
        self.scroll_view(0)
