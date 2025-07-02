from PyQt5.QtWidgets import QInputDialog
import pandas as pd

LABEL_OPTIONS = ["buy", "addbuy", "sell", "addsell", "close_buy", "close_sell"]

class LabelManager:
    def __init__(self, chart):
        self.chart = chart
        self.labels = pd.DataFrame(columns=["Date", "Label", "Price"])
        self._selected_label_index = None
        self._dragging_label = False

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

        price, ok_price = QInputDialog.getDouble(self.chart, "Цена", "Введите цену сигнала:", float(row['Price']), 0.0, 1e10, 5)
        if not ok_price:
            return

        self.labels = pd.concat([
            self.labels,
            pd.DataFrame([[row['Date'], label, price]], columns=["Date", "Label", "Price"])
        ], ignore_index=True)
        refresh_callback()

    def clear(self):
        self.labels = self.labels.iloc[0:0]

    def save_label_session(self, filepath='labels_session.csv'):
        """Сохраняет текущие метки в указанный файл"""
        self.labels.to_csv(filepath, index=False)
        print(f"[INFO] Разметка сохранена в {filepath}")

    def load_label_session(self, filepath='labels_session.csv'):
        """Загружает разметку из указанного файла"""
        try:
            loaded = pd.read_csv(filepath, parse_dates=['Date'])
            loaded = loaded.dropna(subset=['Date', 'Price', 'Label'])
            self.labels = pd.concat([self.labels, loaded], ignore_index=True)
            self.labels.drop_duplicates(subset=['Date', 'Label'], inplace=True)
            self.labels.sort_values(by='Date', inplace=True)
            print(f"[INFO] Загружено {len(loaded)} меток из {filepath}")
        except FileNotFoundError:
            print(f"[WARN] Файл {filepath} не найден")
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке разметки: {e}")

    def autosave_labels(self, filepath='labels_autosave.csv'):
        """Автоматическое сохранение в конец сессии"""
        self.labels.to_csv(filepath, index=False)
        print(f"[AUTO] Автосохранение в {filepath}")

    # def autoload_labels(self, filepath='labels_autosave.csv'):
    #     """Автоматическая загрузка меток при запуске"""
    #     try:
    #         loaded = pd.read_csv(filepath, parse_dates=['Date'])
    #         loaded = loaded.dropna(subset=['Date', 'Price', 'Label'])
    #         self.labels = pd.concat([self.labels, loaded], ignore_index=True)
    #         self.labels.drop_duplicates(subset=['Date', 'Label'], inplace=True)
    #         self.labels.sort_values(by='Date', inplace=True)
    #         print(f"[AUTO] Загружено {len(loaded)} автосохранённых меток из {filepath}")
    #     except FileNotFoundError:
    #         print("[INFO] Автосохранение отсутствует")
    #     except Exception as e:
    #         print(f"[ERROR] Ошибка автозагрузки: {e}")

    def draw_labels(self, chart):
        if self.labels.empty or chart.data is None:
            return

        df_window = chart.data.reset_index(drop=True)
        df_original = chart.original_data.reset_index(drop=True)

        date_to_global_idx = {row["Date"]: idx for idx, row in df_original.iterrows()}

        for i, row in self.labels.iterrows():
            date = row["Date"]
            if date not in date_to_global_idx:
                continue

            global_idx = date_to_global_idx[date]
            local_idx = global_idx - chart.view_start_index

            if not (0 <= local_idx < chart.view_window_size):
                continue

            price = row["Price"]
            label = row["Label"]
            is_selected = (i == self._selected_label_index)

            # Цвет и маркер
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

            # Точка с обводкой — только один scatter
            chart.axes.scatter(
                local_idx, price,
                s=100,
                marker=marker,
                facecolors=color,
                edgecolors='red' if is_selected else 'black',
                linewidths=2 if is_selected else 0.5,
                zorder=5
            )

            # Горизонтальная линия
            x_start = max(0, local_idx - 2)
            x_end = min(chart.view_window_size - 1, local_idx + 3)
            chart.axes.plot(
                [x_start, x_end], [price, price],
                color='black', linestyle='-', alpha=1, linewidth=1.5, zorder=4
            )

    def handle_double_click(self, event):
        if event.xdata is None or event.ydata is None:
            return

        for i, row in self.labels.iterrows():
            label_date = row["Date"]
            label_price = row["Price"]

            df = self.chart.original_data
            if label_date not in df["Date"].values:
                continue

            global_idx = df[df["Date"] == label_date].index[0]
            local_idx = global_idx - self.chart.view_start_index

            if not (0 <= local_idx < self.chart.view_window_size):
                continue

            dx = abs(event.xdata - local_idx)
            dy = abs(event.ydata - label_price)

            if dx < 1 and dy < 0.5:
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

    def handle_mouse_drag(self, event):
        if self._dragging_label and self._selected_label_index is not None:
            if event.xdata is None or event.ydata is None:
                return

            x_index = int(round(event.xdata))
            y_price = float(event.ydata)

            # Привязка к индексу и проверка границ
            df = self.chart.data
            if not (0 <= x_index < len(df)):
                return

            new_date = df.iloc[x_index]['Date']
            print(f"[DEBUG] Перемещаем метку {self._selected_label_index} → {new_date}, {y_price:.5f}")

            self.labels.at[self._selected_label_index, 'Date'] = new_date
            self.labels.at[self._selected_label_index, 'Price'] = y_price

            self.chart._plot_window()

    def handle_mouse_release(self, event):
        if self._dragging_label:
            print(f"[DEBUG] Завершено перемещение")
        self._dragging_label = False

    def handle_mouse_press(self, event):
        if event.button == 1 and self._selected_label_index is not None:
            print(f"[DEBUG] Активировано перемещение метки")
            self._dragging_label = True


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
