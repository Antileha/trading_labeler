import pandas as pd

def load_csv_data(file_path):
    df = pd.read_csv(file_path, header=None)

    if df.shape[1] == 7:
        df.columns = ['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        df['Date'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%Y.%m.%d %H:%M')
        df.drop(columns=['Time'], inplace=True)
    elif 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    else:
        raise ValueError("Неподдерживаемый формат CSV")

    df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
    df.sort_values('Date', inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df
