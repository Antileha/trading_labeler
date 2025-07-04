import ta
import json

def apply_indicators(df, config_list):
    result_df = df.copy()

    for ind in config_list:
        name = ind['type'].lower()
        period = ind['period']
        col = f"{ind['type']}_{period}"

        try:
            if name == 'ema':
                result_df[col] = ta.trend.ema_indicator(result_df['Close'], window=period)
            elif name == 'rsi':
                result_df[col] = ta.momentum.rsi(result_df['Close'], window=period)
            elif name == 'wma':
                result_df[col] = ta.trend.wma_indicator(result_df['Close'], window=period)
            elif name == 'adx':
                result_df[col] = ta.trend.adx(result_df['High'], result_df['Low'], result_df['Close'], window=period)
            elif name == 'macd':
                macd_series = ta.trend.macd(result_df['Close'])
                result_df[col] = macd_series
            elif name == 'stoch':
                result_df[col] = ta.momentum.stoch(result_df['High'], result_df['Low'], result_df['Close'], window=period)
            # можно добавлять ещё
        except Exception as e:
            print(f"[ERROR] Failed to compute {col}: {e}")

    return result_df

def save_indicator_template(config_list, filepath='indicators_template.json'):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config_list, f, indent=2, ensure_ascii=False)
        print(f"[TEMPLATE] Шаблон индикаторов сохранён в {filepath}")
    except Exception as e:
        print(f"[ERROR] Ошибка при сохранении шаблона: {e}")

def load_indicator_template(filepath='indicators_template.json'):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            config_list = json.load(f)
        print(f"[TEMPLATE] Загружено {len(config_list)} индикаторов из {filepath}")
        return config_list
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки шаблона: {e}")
        return []

