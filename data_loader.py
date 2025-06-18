import pandas as pd

def load_csv_data(file_path, format=None):
    try:
        if format is None:
            # Автоопределение
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

        elif format == "yfinance":
            df = pd.read_csv(file_path)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]

        elif format == "custom":
            df = pd.read_csv(file_path, skiprows=3)
            df.columns = ['Date', 'Close', 'High', 'Low', 'Open', 'Volume']
            df['Date'] = pd.to_datetime(df['Date'])

        else:
            raise ValueError("Неизвестный формат")

        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in df.columns:
                df[col] = df[col].astype(float)

        df.sort_values('Date', inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    except Exception as e:
        raise ValueError(f"Ошибка при загрузке: {e}")
