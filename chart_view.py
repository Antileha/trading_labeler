from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.backend_bases import MouseEvent, MouseButton
import pandas as pd


class CandlestickChart(QWidget):
    def __init__(self, parent=None, label_manager=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(12, 8), constrained_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.axes = self.figure.add_subplot(211)
        self.rsi_axes = self.figure.add_subplot(212, sharex=self.axes)

        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.label_manager = label_manager
        self.canvas.mpl_connect("button_press_event", self.onclick)
        self.canvas.mpl_connect("scroll_event", self.on_scroll)
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)
        self.canvas.mpl_connect("button_release_event", self.on_mouse_release)

        self.data = None
        self.original_data = None
        self.current_tf = "4h"
        self.view_start_index = 0
        self.view_window_size = 200

        self._dragging = False
        self._drag_start_x = None

    def scroll_view(self, direction):
        if self.data is None:
            return
        max_index = len(self.data) - self.view_window_size
        self.view_start_index = max(0, min(self.view_start_index + direction, max_index))
        self._plot_window()

    def plot(self, df, tf):
        self.original_data = df.copy()
        self.current_tf = tf
        if self.data is None:  # сохраняем положение при повторном вызове
            self.view_start_index = 0
        self._plot_window()

    def _plot_window(self):
        self.axes.clear()
        self.rsi_axes.clear()

        df = self.original_data.copy()
        df.set_index('Date', inplace=True)
        df_resampled = df.resample(self.current_tf).agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()

        df_resampled['EMA13'] = df_resampled['Close'].ewm(span=13, adjust=False).mean()
        df_resampled['EMA50'] = df_resampled['Close'].ewm(span=50, adjust=False).mean()
        df_resampled['EMA100'] = df_resampled['Close'].ewm(span=100, adjust=False).mean()

        delta = df_resampled['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        df_resampled['RSI12'] = 100 - (100 / (1 + gain.rolling(12).mean() / loss.rolling(12).mean()))
        df_resampled['RSI21'] = 100 - (100 / (1 + gain.rolling(21).mean() / loss.rolling(21).mean()))
        df_resampled['RSI50'] = 100 - (100 / (1 + gain.rolling(50).mean() / loss.rolling(50).mean()))

        df_resampled.dropna(inplace=True)
        df_resampled.reset_index(inplace=True)
        self.data = df_resampled

        start = self.view_start_index
        end = start + self.view_window_size
        view_df = df_resampled.iloc[start:end]
        x_vals = list(range(len(view_df)))
        width = 0.8

        self._draw_candles(view_df, x_vals, width)

        self.axes.plot(x_vals, view_df['EMA13'], color='blue', label='EMA13')
        self.axes.plot(x_vals, view_df['EMA50'], color='red', label='EMA50')
        self.axes.plot(x_vals, view_df['EMA100'], color='green', label='EMA100')
        self.axes.set_title('Candlestick Chart with EMA')
        self.axes.legend()
        self.axes.set_xticks(x_vals[::max(1, len(x_vals)//10)])
        self.axes.set_xticklabels(view_df['Date'].dt.strftime('%Y-%m-%d').iloc[::max(1, len(x_vals)//10)], rotation=45)

        self.rsi_axes.plot(x_vals, view_df['RSI12'], color='green', label='RSI12')
        self.rsi_axes.plot(x_vals, view_df['RSI21'], color='black', label='RSI21')
        self.rsi_axes.plot(x_vals, view_df['RSI50'], color='cyan', label='RSI50')
        self.rsi_axes.axhline(70, color='gray', linestyle='--')
        self.rsi_axes.axhline(30, color='gray', linestyle='--')
        self.rsi_axes.set_title("RSI Indicators")
        self.rsi_axes.legend()

        if self.label_manager:
            for _, row in self.label_manager.labels.iterrows():
                match_idx = df_resampled[df_resampled['Date'] == pd.to_datetime(row['Date'])]
                if not match_idx.empty:
                    index = match_idx.index[0] - start
                    if 0 <= index < len(x_vals):
                        x = x_vals[index]
                        y = row['Price']
                        label = row['Label']
                        symbol = '^' if 'buy' in label else 'v' if 'sell' in label else 'x'
                        color = 'blue' if 'buy' in label else 'red' if 'sell' in label else 'black'
                        self.axes.text(x, y, symbol, color=color, fontsize=16, ha='center', va='center')

        self.canvas.draw()

    def _draw_candles(self, df, x_vals, width):
        for i, x in enumerate(x_vals):
            open_, high, low, close = df.iloc[i][['Open', 'High', 'Low', 'Close']]
            color = 'green' if close >= open_ else 'red'
            self.axes.plot([x, x], [low, high], color='black', linewidth=0.8)
            rect = Rectangle(
                (x - width / 2, min(open_, close)),
                width,
                abs(close - open_),
                color=color,
                zorder=2
            )
            self.axes.add_patch(rect)

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
