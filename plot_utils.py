import pandas as pd
from matplotlib.patches import Rectangle


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

    _draw_candles(self, view_df, x_vals, width)

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
    for level, color in [(20, 'red'), (30, 'green'), (40, 'cyan'), (60, 'cyan'), (70, 'green'), (80, 'red')]:
        self.rsi_axes.axhline(y=level, color=color, linestyle='--', linewidth=0.8)
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
                    label = row['Label'].lower()

                    if 'close' in label:
                        symbol = '×'
                        color = 'black'
                    elif 'addbuy' in label:
                        symbol = '⇑'
                        color = 'deepskyblue'
                    elif 'buy' in label:
                        symbol = '↑'
                        color = 'blue'
                    elif 'addsell' in label:
                        symbol = '⇓'
                        color = 'hotpink'
                    elif 'sell' in label:
                        symbol = '↓'
                        color = 'red'
                    elif 'stoploss' in label:
                        symbol = '‼'
                        color = 'orange'
                    else:
                        symbol = '?'
                        color = 'gray'

                    self.axes.text(x, y, symbol, color=color, fontsize=18, ha='center', va='center')
                    self.axes.plot([x - 1, x + 1], [y, y], color='black', linewidth=1)

    self.candle_canvas.draw()
    self.rsi_canvas.draw()
    # Уменьшаем подписи осей и заголовков
    for ax in [self.axes, self.rsi_axes]:
        ax.tick_params(axis='both', labelsize=8)  # оси X и Y
        ax.title.set_fontsize(8)
        ax.legend(fontsize=8)

    # Для оси X — уменьшаем плотность и поворот дат
    self.axes.set_xticklabels(
        self.axes.get_xticklabels(),
        rotation=0,
        fontsize=6
    )
