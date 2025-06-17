import pandas as pd
import matplotlib.pyplot as plt
from ta.trend import EMAIndicator, WMAIndicator, ADXIndicator, macd
from ta.momentum import RSIIndicator, stoch

def _draw_candles(ax, data):
    ax.clear()
    width = 0.6
    for i, row in data.iterrows():
        color = 'green' if row['Close'] >= row['Open'] else 'red'
        ax.plot([i, i], [row['Low'], row['High']], color=color)
        ax.add_patch(plt.Rectangle((i - width/2, min(row['Open'], row['Close'])), width,
                                   abs(row['Close'] - row['Open']), color=color))

def _plot_window(chart):
    if chart.original_data is None:
        return

    df = chart.original_data.copy()
    chart.data = df.iloc[chart.view_start_index: chart.view_start_index + chart.view_window_size]
    df_window = chart.data.copy().reset_index(drop=True)

    chart.axes.clear()
    chart.rsi_axes.clear()

    _draw_candles(chart.axes, df_window)

    # Отрисовка пользовательских индикаторов
    for ind_cfg in chart.indicator_config:
        col_name = f"{ind_cfg['type']}_{ind_cfg['period']}"
        try:
            if ind_cfg['type'].lower() == 'ema':
                df_window[col_name] = EMAIndicator(df_window['Close'], window=ind_cfg['period']).ema_indicator()
            elif ind_cfg['type'].lower() == 'rsi':
                df_window[col_name] = RSIIndicator(df_window['Close'], window=ind_cfg['period']).rsi()
            elif ind_cfg['type'].lower() == 'wma':
                df_window[col_name] = WMAIndicator(df_window['Close'], window=ind_cfg['period']).wma()
            elif ind_cfg['type'].lower() == 'adx':
                df_window[col_name] = ADXIndicator(df_window['High'], df_window['Low'], df_window['Close'], window=ind_cfg['period']).adx()
            elif ind_cfg['type'].lower() == 'macd':
                df_window[col_name] = macd(df_window['Close'])
            elif ind_cfg['type'].lower() == 'stoch':
                df_window[col_name] = stoch(df_window['High'], df_window['Low'], df_window['Close'], window=ind_cfg['period'])
            else:
                continue

            target_ax = chart.axes if ind_cfg['axis'] == 'main' else chart.rsi_axes
            series = df_window[col_name].fillna(method='ffill').fillna(method='bfill')
            target_ax.plot(df_window.index, series, label=col_name, color=ind_cfg.get('color', 'black'))

        except Exception as e:
            print(f"[ERROR] Indicator {col_name} failed: {e}")

    chart.axes.legend(loc='upper left', fontsize=8)
    chart.axes.set_xticks(range(0, len(df_window), max(len(df_window) // 10, 1)))
    chart.axes.set_xticklabels(df_window['Date'].iloc[::max(len(df_window) // 10, 1)], rotation=0, fontsize=8)

    chart.rsi_axes.set_xticks(range(0, len(df_window), max(len(df_window) // 10, 1)))
    chart.rsi_axes.set_xticklabels(df_window['Date'].iloc[::max(len(df_window) // 10, 1)], rotation=0, fontsize=8)
    chart.rsi_axes.axhline(20, color='red', linestyle='--', linewidth=0.5)
    chart.rsi_axes.axhline(30, color='green', linestyle='--', linewidth=0.5)
    chart.rsi_axes.axhline(40, color='cyan', linestyle='--', linewidth=0.5)
    chart.rsi_axes.axhline(60, color='cyan', linestyle='--', linewidth=0.5)
    chart.rsi_axes.axhline(70, color='green', linestyle='--', linewidth=0.5)
    chart.rsi_axes.axhline(80, color='red', linestyle='--', linewidth=0.5)

    chart.candle_canvas.draw()
    chart.rsi_canvas.draw()
