# Trading Labeling Assistant

Приложение для ручной разметки торговых данных на графике в стиле MetaTrader.

## 📦 Установка

```bash
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/macOS

pip install -r requirements.txt
```

## ▶️ Запуск

```bash
python main.py
```

## 📁 Структура проекта

```
trading_labeler/
├── main.py              # точка входа
├── ui_main.py           # интерфейс и логика управления окном
├── chart_view.py        # визуализация графика и индикаторов
├── data_loader.py       # обработка входного CSV
├── label_manager.py     # управление метками (buy/sell/...)
├── requirements.txt     # зависимости
└── README.md            # инструкция
```

## 💡 Особенности
- Поддержка нестандартных CSV без заголовков (`Date`, `Time`, `Open`, `High`, `Low`, `Close`, `Volume`)
- Таймфреймы: `4h`, `1d`, `1w`
- Индикаторы: EMA13/50/100 и RSI12/21/50
- Ручная разметка сигналов: `buy`, `addbuy`, `sell`, `addsell`, `close_buy`, `close_sell`
- Экспорт в `labels.csv`

## 🔧 Зависимости
- PyQt5
- matplotlib
- pandas
- mplfinance (0.11.1a0)
- ta
