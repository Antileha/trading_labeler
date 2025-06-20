import pandas as pd

def load_csv_data(file_path, format=None):
    try:
        if format is None:
            df_head = pd.read_csv(file_path, nrows=3, header=None)
            if df_head.shape[1] == 7 and str(df_head.iloc[0, 0]).count('.') == 2 and ':' in str(df_head.iloc[0, 1]):
                format = "ffx"
            elif "Date" in pd.read_csv(file_path, nrows=0).columns:
                format = "yfinance"
            else:
                format = "custom"

        if format == "ffx":
            df = pd.read_csv(file_path, header=None)
            df.columns = ['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']
            df['Date'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%Y.%m.%d %H:%M')
            df.drop(columns=['Time'], inplace=True)

        else:
            df = pd.read_csv(file_path)
            df.columns = [col.lower().strip() for col in df.columns]

            # Обработка даты
            if 'date' in df.columns:
                df = df.rename(columns={'date': 'Date'})
            elif 'time' in df.columns:
                df = df.rename(columns={'time': 'Date'})
            else:
                raise ValueError("Нет колонки с датой (date или time)")

            # Переименование цен
            rename_map = {
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
            }
            df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

            # Выбор одной колонки объёма
            if 'tick_volume' in df.columns:
                df['Volume'] = df['tick_volume']
            elif 'real_volume' in df.columns:
                df['Volume'] = df['real_volume']
            elif 'volume' in df.columns:
                df['Volume'] = df['volume']

            df.drop(columns=[col for col in ['tick_volume', 'real_volume', 'volume'] if col in df.columns], inplace=True)

            # Проверка наличия колонок
            keep_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            missing = [col for col in keep_cols if col not in df.columns]
            if missing:
                raise ValueError(f"В файле не хватает колонок: {missing}")

            df = df[keep_cols]
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

        # Приведение типов
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in df.columns:
                df[col] = df[col].astype(float)

        df = df.dropna(subset=['Date'])
        df.sort_values('Date', inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    except Exception as e:
        raise ValueError(f"Ошибка при загрузке: {e}")
