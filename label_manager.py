import pandas as pd
from PyQt5.QtWidgets import QInputDialog

LABEL_OPTIONS = ["buy", "addbuy", "sell", "addsell", "close_buy", "close_sell", 'stoploss']

class LabelManager:
    def __init__(self, chart):
        self.chart = chart
        self.labels = pd.DataFrame(columns=["Date", "Label", "Price"])
        self._selected_label_index = None
        self._dragging_label = False
        self._history = []

    def save_state(self):
        self._history.append(self.labels.copy(deep=True))
        if len(self._history) > 100:
            self._history.pop(0)

    def undo_last_action(self):
        if self._history:
            self.labels = self._history.pop()
            self._selected_label_index = None
            print("[UNDO] Последнее действие отменено.")
            self.chart._plot_window()
        else:
            print("[UNDO] История пуста")

    def handle_click(self, row, refresh_callback):
        self.save_state()
        date = row['Date']
        existing = self.labels[self.labels['Date'] == date]

        if not existing.empty:
            options = [f"{r.Label} @ {r.Price}" for _, r in existing.iterrows()] + ["Добавить новую", "Удалить метку"]
            choice, ok = QInputDialog.getItem(self.chart, "Редактирование", "Выберите действие:", options, 0, False)
            if not ok:
                return
            if choice == "Добавить новую":
                self.save_state()
                self._add_label(row, refresh_callback)
            elif choice == "Удалить метку":
                index_to_delete, ok2 = QInputDialog.getInt(self.chart, "Удалить", "Индекс метки:", 0, 0, len(existing) - 1)
                if ok2:
                    self.save_state()
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
                self.save_state()
                self.labels.at[existing.index[idx_choice], 'Label'] = label
                self.labels.at[existing.index[idx_choice], 'Price'] = price
                refresh_callback()
        else:
            self.save_state()
            self._add_label(row, refresh_callback)

    def _add_label(self, row, refresh_callback):
        label, ok = QInputDialog.getItem(self.chart, "Новая метка", "Тип сигнала:", LABEL_OPTIONS, 0, False)
        if not ok or not label:
            return

        price, ok_price = QInputDialog.getDouble(self.chart, "Цена", "Введите цену сигнала:", float(row['Price']), 0.0, 1e10, 5)
        if not ok_price:
            return

        self.save_state()
        self.labels = pd.concat([
            self.labels,
            pd.DataFrame([[row['Date'], label, price]], columns=["Date", "Label", "Price"])
        ], ignore_index=True)
        refresh_callback()

    def handle_double_click(self, event):
        if event.xdata is None or event.ydata is None or not hasattr(self.chart, "view_dates"):
            return

        x_idx = int(round(event.xdata))
        if 0 <= x_idx < len(self.chart.view_dates):
            date = self.chart.view_dates.iloc[x_idx]
            for i, row in self.labels.iterrows():
                if row["Date"] == date and abs(row["Price"] - event.ydata) < 0.5:
                    if self._selected_label_index == i:
                        print(f"[DEBUG] Снята метка: {row['Label']} @ {row['Price']}")
                        self._selected_label_index = None
                        self._dragging_label = False
                    else:
                        print(f"[DEBUG] Выбрана метка: {row['Label']} @ {row['Price']}")
                        self._selected_label_index = i
                        self._dragging_label = False
                    self.chart._plot_window()
                    return

    def handle_mouse_press(self, event):
        if event.button == 1 and self._selected_label_index is not None:
            print(f"[DEBUG] Активировано перемещение метки")
            self._dragging_label = True

    def handle_mouse_drag(self, event):
        if self._dragging_label and self._selected_label_index is not None:
            if event.ydata is None:
                return

            self.save_state()
            y_price = float(event.ydata)
            self.labels.at[self._selected_label_index, 'Price'] = y_price

            if self.chart.ctrl_pressed and event.xdata is not None:
                x_index = int(round(event.xdata))
                if 0 <= x_index < len(self.chart.view_dates):
                    new_date = self.chart.view_dates.iloc[x_index]
                    self.labels.at[self._selected_label_index, 'Date'] = new_date
                    print(f"[DEBUG] Перемещаем метку {self._selected_label_index} → {new_date}, {y_price:.5f}")

            self.chart._plot_window()

    def handle_mouse_release(self, event):
        if self._dragging_label:
            print("[DEBUG] Завершено перемещение")
        self._dragging_label = False

    def draw_labels(self, chart):
        if self.labels.empty or chart.data is None or not hasattr(chart, "view_dates"):
            return

        # Сопоставление: дата → индекс в текущем окне отображения
        date_to_index = {date: idx for idx, date in enumerate(chart.view_dates)}

        for i, row in self.labels.iterrows():
            date = row["Date"]
            if date not in date_to_index:
                continue

            local_idx = date_to_index[date]
            price = row["Price"]
            label = row["Label"]
            is_selected = (i == self._selected_label_index)

            # Выбор цвета и формы метки
            if label.lower() in ['buy', 'addbuy']:
                color = 'cyan'
                marker = '^'
            elif label.lower() in ['sell', 'addsell']:
                color = 'red'
                marker = 'v'
            elif label.lower() in ['close_buy', 'close_sell']:
                color = 'black'
                marker = 'X'
            elif 'stoploss' in label.lower():
                color = 'orange'
                marker = 's'
            else:
                color = 'blue'
                marker = 'o'

            # Отрисовка метки
            chart.axes.scatter(
                local_idx, price,
                s=100,
                marker=marker,
                facecolors=color,
                edgecolors='red' if is_selected else 'black',
                linewidths=2 if is_selected else 0.5,
                zorder=5
            )

            # Горизонтальная линия уровня
            x_start = max(0, local_idx - 2)
            x_end = min(chart.view_window_size - 1, local_idx + 3)
            chart.axes.plot(
                [x_start, x_end], [price, price],
                color='black', linestyle='-', alpha=1, linewidth=1.5, zorder=4
            )

    def clear(self):
        self.labels = self.labels.iloc[0:0]
        self._selected_label_index = None
        self._dragging_label = False
        self._history.clear()

    def save_label_session(self, filepath='labels_session.csv'):
        """Сохраняет текущие метки в указанный файл"""

        self.labels.to_csv(filepath, index=False)
        print(f"[INFO] Разметка сохранена в {filepath}")

    def load_label_session(self, filepath='labels_session.csv'):
        try:
            df = pd.read_csv(filepath)

            # Если в файле есть 'Date' — пытаемся преобразовать
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            else:
                raise ValueError("Файл меток не содержит колонки 'Date'")

            df = df.dropna(subset=['Date', 'Price', 'Label'])
            self.labels = pd.concat([self.labels, df[['Date', 'Label', 'Price']]], ignore_index=True)
            self.labels.drop_duplicates(subset=['Date', 'Label'], inplace=True)
            self.labels.sort_values(by='Date', inplace=True)

            print(f"[INFO] Загружено {len(df)} меток из {filepath}")
        except FileNotFoundError:
            print(f"[WARN] Файл {filepath} не найден")
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке разметки: {e}")

    def autosave_labels(self, filepath='labels_autosave.csv'):
        """Автоматическое сохранение в конец сессии"""

        self.labels.to_csv(filepath, index=False)
        print(f"[AUTO] Автосохранение в {filepath}")

    def load_labels_from_dataframe(self, df):
        """Загружает метки из датафрейма с колонками Label и LabelPrice"""
        if 'Label' not in df.columns or 'LabelPrice' not in df.columns:
            print("[LOAD] Нет нужных колонок Label и LabelPrice в датафрейме")
            return

        label_rows = df[['Date', 'Label', 'LabelPrice']].dropna(subset=['Label'])
        label_rows = label_rows.rename(columns={'LabelPrice': 'Price'})
        label_rows['Date'] = pd.to_datetime(label_rows['Date'])

        self.labels = label_rows[['Date', 'Label', 'Price']].reset_index(drop=True)
        self._selected_label_index = None
        self._dragging_label = False
        self.chart._plot_window()
        print(f"[LOAD] Загружено {len(self.labels)} меток из CSV")

    def delete_selected_label(self):
        if self._selected_label_index is not None:
            self.save_state()
            self.labels.drop(index=self._selected_label_index, inplace=True)
            self.labels.reset_index(drop=True, inplace=True)
            print(f"[DELETE] Удалена метка с индексом {self._selected_label_index}")
            self._selected_label_index = None
            self.chart._plot_window()


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


