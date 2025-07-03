# === chart_view.py ===
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QSplitter
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.backend_bases import MouseEvent, MouseButton
from plot_utils import _plot_window

class CandlestickChart(QWidget):
    def __init__(self, parent=None, label_manager=None):
        super().__init__(parent)

        self.candle_fig = Figure(figsize=(12, 5), constrained_layout=True)
        self.candle_canvas = FigureCanvas(self.candle_fig)
        self.candle_toolbar = NavigationToolbar2QT(self.candle_canvas, self)
        self.axes = self.candle_fig.add_subplot(111)

        candle_widget = QWidget()
        candle_layout = QVBoxLayout(candle_widget)
        candle_layout.setContentsMargins(0, 0, 0, 0)
        candle_layout.addWidget(self.candle_toolbar)
        candle_layout.addWidget(self.candle_canvas)

        self.rsi_fig = Figure(figsize=(12, 3), constrained_layout=True)
        self.rsi_canvas = FigureCanvas(self.rsi_fig)
        self.rsi_axes = self.rsi_fig.add_subplot(111)

        rsi_widget = QWidget()
        rsi_layout = QVBoxLayout(rsi_widget)
        rsi_layout.setContentsMargins(0, 0, 0, 0)
        rsi_layout.addWidget(self.rsi_canvas)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(candle_widget)
        splitter.addWidget(rsi_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout(self)
        layout.addWidget(splitter)
        self.setLayout(layout)

        self.candle_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.rsi_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.label_manager = label_manager
        self.candle_canvas.mpl_connect("button_press_event", self.onclick)
        self.candle_canvas.mpl_connect("scroll_event", self.on_scroll)
        self.candle_canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.candle_canvas.mpl_connect("button_release_event", self.on_mouse_release)
        self.candle_canvas.mpl_connect("key_press_event", self.on_key_press)
        self.candle_canvas.mpl_connect("key_release_event", self.on_key_release)

        self.setFocusPolicy(Qt.StrongFocus)
        self.candle_canvas.setFocusPolicy(Qt.StrongFocus)
        self.candle_canvas.setFocus()

        self.data = None
        self.original_data = None
        self.current_tf = "4h"
        self.view_start_index = 0
        self.view_window_size = 200
        self.indicator_config = []

        self._dragging = False
        self._drag_start_x = None
        self._middle_mouse_pressed = False
        self._crosshair_lines = {"v": None, "h": None}
        self._crosshair_texts = {"price": None, "date": None}

        self.ctrl_pressed = False

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Z:
            if self.label_manager:
                self.label_manager.undo_last_action()

    def on_key_press(self, event):
        if event.key == 'control':
            self.ctrl_pressed = True
        elif event.key == 'ctrl+z' or (event.key == 'z' and self.ctrl_pressed):
            if self.label_manager:
                self.label_manager.undo_last_action()

    def on_key_release(self, event):
        if event.key == 'control':
            self.ctrl_pressed = False

    def scroll_view(self, direction):
        if self.data is None:
            return
        max_index = len(self.data) - self.view_window_size
        self.view_start_index = max(0, min(self.view_start_index + direction, max_index))
        self._plot_window()

    def plot(self, df, tf):
        self.original_data = df.copy()
        self.data = df.copy()
        self.current_tf = tf
        self.view_start_index = 0
        _plot_window(self)

    def _plot_window(self):
        self.axes.clear()
        self.rsi_axes.clear()
        _plot_window(self)

    def onclick(self, event: MouseEvent):
        if self.data is None or event.inaxes != self.axes:
            return

        if event.dblclick and self.label_manager:
            self.label_manager.handle_double_click(event)
            return

        if event.button == MouseButton.LEFT:
            if self.label_manager:
                self.label_manager.handle_mouse_press(event)
                if self.label_manager._dragging_label:
                    return
            self._dragging = True
            self._drag_start_x = event.xdata

        elif event.button == MouseButton.MIDDLE:
            self._middle_mouse_pressed = True

        elif event.button == MouseButton.RIGHT:
            index = round(event.xdata)
            if 0 <= index < len(self.data) and event.ydata is not None:
                row = self.data.iloc[self.view_start_index + index].copy()
                row['Price'] = float(event.ydata)
                self.label_manager.handle_click(row, lambda: self._plot_window())

    def on_mouse_release(self, event):
        self._dragging = False
        self._drag_start_x = None

        if self.label_manager:
            self.label_manager.handle_mouse_release(event)

        if event.button == MouseButton.MIDDLE:
            self._middle_mouse_pressed = False
            self.clear_crosshair()
            self.candle_canvas.draw()

    def on_mouse_move(self, event):
        if self._middle_mouse_pressed and event.inaxes == self.axes and event.xdata and event.ydata:
            self.draw_crosshair(event.xdata, event.ydata)
            return

        if self.label_manager and self.label_manager._dragging_label:
            if event.inaxes == self.axes and event.ydata is not None:
                self.label_manager.handle_mouse_drag(event)
            return

        if self._dragging and event.xdata is not None:
            dx = event.xdata - self._drag_start_x
            bars_to_shift = int(-dx * 2)
            if bars_to_shift != 0:
                self.scroll_view(bars_to_shift)
                self._drag_start_x = event.xdata

    def on_scroll(self, event):
        if event.button == 'up':
            self.view_window_size = max(10, self.view_window_size - 10)
        elif event.button == 'down':
            self.view_window_size += 10
        self._plot_window()

    def draw_crosshair(self, x, y):
        for line in self._crosshair_lines.values():
            if line: line.remove()
        for text in self._crosshair_texts.values():
            if text: text.remove()

        self._crosshair_lines["v"] = self.axes.axvline(x=x, color='gray', linestyle='--', linewidth=0.8)
        self._crosshair_lines["h"] = self.axes.axhline(y=y, color='gray', linestyle='--', linewidth=0.8)

        self._crosshair_texts["price"] = self.axes.text(
            self.axes.get_xlim()[0], y, f"{y:.4f}",
            va='center', ha='left', fontsize=8, backgroundcolor='white'
        )
        self._crosshair_texts["date"] = self.axes.text(
            x, self.axes.get_ylim()[0], self.format_xdate(x),
            va='bottom', ha='center', fontsize=8, backgroundcolor='white'
        )

        self.candle_canvas.draw()

    def clear_crosshair(self):
        for line in self._crosshair_lines.values():
            if line: line.remove()
        for text in self._crosshair_texts.values():
            if text: text.remove()
        self._crosshair_lines = {"v": None, "h": None}
        self._crosshair_texts = {"price": None, "date": None}

    def format_xdate(self, x):
        try:
            index = int(round(x))
            if 0 <= index < len(self.data):
                date = self.data.iloc[self.view_start_index + index]['Date']
                return str(date)[:10]
        except:
            pass
        return f"{x:.2f}"