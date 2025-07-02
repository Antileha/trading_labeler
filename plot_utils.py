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
        ax.add_patch(plt.Rectangle(
            (i - width/2, min(row['Open'], row['Close'])),
            width,
            abs(row['Close'] - row['Open']),
            color=color
        ))

def _plot_window(chart):
    if chart.original_data is None:
        return

    # Копируем и ресемплим данные
    df = chart.original_data.copy()
    df.set_index('Date', inplace=True)
    df = df.resample(chart.current_tf).agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()
    df.reset_index(inplace=True)

    # Вычисление индикаторов по всему датафрейму
    for ind_cfg in chart.indicator_config:
        col_name = f"{ind_cfg['type']}_{ind_cfg['period']}"
        try:
            if ind_cfg['type'].lower() == 'ema':
                df[col_name] = EMAIndicator(df['Close'], window=ind_cfg['period']).ema_indicator()
            elif ind_cfg['type'].lower() == 'rsi':
                df[col_name] = RSIIndicator(df['Close'], window=ind_cfg['period']).rsi()
            elif ind_cfg['type'].lower() == 'wma':
                df[col_name] = WMAIndicator(df['Close'], window=ind_cfg['period']).wma()
        except Exception:
            continue

    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    chart.data = df  # сохраняем для привязки меток

    # Окно отображения
    start = chart.view_start_index
    end = start + chart.view_window_size
    view_df = df.iloc[start:end].reset_index(drop=True)

    chart.axes.clear()
    chart.rsi_axes.clear()

    # Рисуем свечи
    _draw_candles(chart.axes, view_df)

    # Рисуем индикаторы
    for ind_cfg in chart.indicator_config:
        col_name = f"{ind_cfg['type']}_{ind_cfg['period']}"
        if col_name in view_df.columns:
            target_ax = chart.axes if ind_cfg.get("axis", "main") == "main" else chart.rsi_axes
            target_ax.plot(view_df.index, view_df[col_name], color=ind_cfg.get("color", "gray"), label=col_name)

    # RSI уровни
    for level, color in [(20, 'red'), (30, 'green'), (40, 'cyan'), (50, 'black'), (60, 'cyan'), (70, 'green'), (80, 'red')]:
        chart.rsi_axes.axhline(level, color=color, linestyle='--', linewidth=0.5)

    # Метки (с рамкой при выделении)
    if chart.label_manager:
        chart.label_manager.draw_labels(chart)

    # # Метки
    # if chart.label_manager and chart.label_manager.labels is not None:
    #     for _, row in chart.label_manager.labels.iterrows():
    #         match_idx = df[df['Date'] == pd.to_datetime(row['Date'])]
    #         if not match_idx.empty:
    #             index = match_idx.index[0] - start
    #             if 0 <= index < len(view_df):
    #                 x = index
    #                 y = row['Price']
    #                 label = row['Label'].lower()
    #                 symbol = {'buy': '↑', 'addbuy': '⇑', 'sell': '↓', 'addsell': '⇓',
    #                           'close buy': 'X', 'close sell': 'X', 'stoploss buy': '‼', 'stoploss sell': '‼'}.get(label, '?')
    #                 color = {'buy': 'blue', 'addbuy': 'deepskyblue', 'sell': 'red', 'addsell': 'hotpink',
    #                          'close buy': 'black', 'close sell': 'black', 'stoploss buy': 'orange', 'stoploss sell': 'orange'}.get(label, 'gray')
    #                 chart.axes.text(x, y, symbol, color=color, fontsize=14, ha='center', va='center')
    #                 chart.axes.plot([x - 1, x + 1], [y, y], color='black', linewidth=1)

    # Оформление
    chart.axes.set_xticks(range(0, len(view_df), max(len(view_df) // 10, 1)))
    chart.axes.set_xticklabels(view_df['Date'].dt.strftime('%Y-%m-%d').iloc[::max(len(view_df) // 10, 1)],
                                rotation=45, fontsize=8)
    chart.axes.legend(fontsize=8)

    chart.rsi_axes.set_xticks(range(0, len(view_df), max(len(view_df) // 10, 1)))
    chart.rsi_axes.set_xticklabels(view_df['Date'].dt.strftime('%Y-%m-%d').iloc[::max(len(view_df) // 10, 1)],
                                    rotation=45, fontsize=8)
    chart.rsi_axes.legend(fontsize=8)

    chart.candle_canvas.draw()
    chart.rsi_canvas.draw()
