from PyQt5.QtWidgets import QInputDialog
import pandas as pd

LABEL_OPTIONS = ["buy", "addbuy", "sell", "addsell", "close_buy", "close_sell"]

class LabelManager:
    def __init__(self, chart):
        self.chart = chart
        self.labels = pd.DataFrame(columns=["Date", "Label", "Price"])

    def handle_click(self, row, refresh_callback):
        date = row['Date']
        existing = self.labels[self.labels['Date'] == date]

        if not existing.empty:
            options = [f"{r.Label} @ {r.Price}" for _, r in existing.iterrows()] + ["Добавить новую", "Удалить метку"]
            choice, ok = QInputDialog.getItem(self.chart, "Редактирование", "Выберите действие:", options, 0, False)
            if not ok:
                return
            if choice == "Добавить новую":
                self._add_label(row, refresh_callback)
            elif choice == "Удалить метку":
                index_to_delete, ok2 = QInputDialog.getInt(self.chart, "Удалить", "Индекс метки:", 0, 0, len(existing) - 1)
                if ok2:
                    self.labels.drop(existing.index[index_to_delete], inplace=True)
                    self.labels.reset_index(drop=True, inplace=True)
                    refresh_callback()
            else:
                idx_choice = options.index(choice)
                selected = existing.iloc[idx_choice]
                label, ok1 = QInputDialog.getItem(self.chart, "Изменить тип", "Тип:", LABEL_OPTIONS, 0, False)
                if not ok1:
                    return
                price, ok2 = QInputDialog.getDouble(self.chart, "Изменить цену", "Цена:", float(selected.Price), 0.0, 1e10, 5)
                if not ok2:
                    return
                self.labels.at[existing.index[idx_choice], 'Label'] = label
                self.labels.at[existing.index[idx_choice], 'Price'] = price
                refresh_callback()
        else:
            self._add_label(row, refresh_callback)

    def _add_label(self, row, refresh_callback):
        label, ok = QInputDialog.getItem(self.chart, "Новая метка", "Тип сигнала:", LABEL_OPTIONS, 0, False)
        if not ok or not label:
            return

        price, ok_price = QInputDialog.getDouble(self.chart, "Цена", "Введите цену сигнала:", float(row['Close']), 0.0, 1e10, 5)
        if not ok_price:
            return

        self.labels = pd.concat([
            self.labels,
            pd.DataFrame([[row['Date'], label, price]], columns=["Date", "Label", "Price"])
        ], ignore_index=True)
        refresh_callback()

    def clear(self):
        self.labels = self.labels.iloc[0:0]

def save_labeled_data(chart, filepath='labeled_data.csv', selected_columns=None):

    df = chart.data.copy()
    df['Label'] = ''
    df['LabelPrice'] = None

    df['Date'] = pd.to_datetime(df['Date'])
    labels = chart.label_manager.labels.copy()
    labels['Date'] = pd.to_datetime(labels['Date'])

    for _, row in labels.iterrows():
        match = df['Date'] == row['Date']
        idx = df.index[match]
        if not idx.empty and idx[0] > 0:
            prev_idx = idx[0] - 1
            df.at[prev_idx, 'Label'] = row['Label']
            df.at[prev_idx, 'LabelPrice'] = row['Price']

    if selected_columns:
        cols_to_save = ['Date'] + [col for col in selected_columns if col != 'Date']
        df[cols_to_save].to_csv(filepath, index=False)