import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import threading
import platform
import os
import logging
from logging.handlers import RotatingFileHandler
import subprocess
import json
import re
import shlex
from datetime import datetime
from typing import Optional

CONFIG_FILE = 'ping_monitor_config.json'
MAX_LOG_LINES = 1000
MAX_LOG_SIZE = 1024 * 1024  # 1 MB
MAX_LOG_FILES = 5


class PingStats:
    def __init__(self):
        self.total_pings = 0
        self.failed_pings = 0
        self.start_time = None
        self.last_failure = None
        self.current_status = "Не запущен"

    def reset(self):
        self.__init__()


class PingMonitorApp:
    def setup_logging(self):
        """Настройка системы логирования"""
        log_dir = os.path.expanduser('~')
        log_file = os.path.join(log_dir, 'ping_monitor.log')

        self.logger = logging.getLogger('PingMonitor')
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')

        # Ротация логов
        handler = RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=MAX_LOG_FILES,
            encoding='utf-8'
        )
        handler.setFormatter(formatter)

        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def __init__(self, root):
        self.root = root
        self.root.title("Ping Monitor")
        self.root.geometry("520x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f4f7")

        # Инициализация базовых атрибутов
        self.stop_event = threading.Event()
        self.stop_event.set()  # Устанавливаем в True при старте
        self.thread: Optional[threading.Thread] = None
        self.stats = PingStats()

        # Сначала настраиваем логгер
        self.setup_logging()

        # Проверка наличия ping в системе
        if not self._check_ping_availability():
            messagebox.showerror("Ошибка", "Команда ping недоступна в системе")
            root.destroy()
            return

        # Значения по умолчанию для конфигурации
        self.config = {'last_host': '8.8.8.8', 'last_interval': 2}
        self.load_config()

        # Настройка UI
        self.setup_ui()

        # Обновление статистики каждую секунду
        self.update_stats()

        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _check_ping_availability(self) -> bool:
        """Проверка доступности команды ping"""
        try:
            if platform.system().lower() == 'windows':
                subprocess.run(['ping'], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            else:
                subprocess.run(
                    ['ping', '-c', '1'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Стили
        style = ttk.Style()
        style.configure("Error.TLabel", foreground="red")
        style.configure("Success.TLabel", foreground="green")

        # Фреймы
        input_frame = ttk.Frame(self.root, padding="5")
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        stats_frame = ttk.Frame(self.root, padding="5")
        stats_frame.pack(fill=tk.X, padx=5)

        log_frame = ttk.Frame(self.root, padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Элементы ввода
        ttk.Label(input_frame, text="Хост:").grid(
            row=0, column=0, padx=5, pady=5)
        self.host_entry = ttk.Entry(input_frame, width=30)
        self.host_entry.grid(row=0, column=1, padx=5, pady=5)
        self.host_entry.insert(0, self.config.get('last_host', '8.8.8.8'))

        ttk.Label(input_frame, text="Интервал (сек):").grid(
            row=0, column=2, padx=5, pady=5)
        self.interval_entry = ttk.Entry(input_frame, width=7)
        self.interval_entry.grid(row=0, column=3, padx=5, pady=5)
        self.interval_entry.insert(0, str(self.config.get('last_interval', 2)))

        self.start_button = ttk.Button(
            input_frame, text="Старт", command=self.toggle_monitoring)
        self.start_button.grid(row=0, column=4, padx=5, pady=5)

        # Статистика
        self.stats_labels = {}
        labels = [
            ("status", "Статус:"),
            ("total", "Всего пингов:"),
            ("failed", "Неудачных:"),
            ("uptime", "Время работы:"),
            ("last_failure", "Последний сбой:")
        ]

        for i, (key, text) in enumerate(labels):
            ttk.Label(stats_frame, text=text).grid(
                row=i, column=0, sticky='w', padx=5, pady=2)
            self.stats_labels[key] = ttk.Label(stats_frame, text="-")
            self.stats_labels[key].grid(
                row=i, column=1, sticky='w', padx=5, pady=2)

        # Лог
        self.log_text = scrolledtext.ScrolledText(
            log_frame, width=60, height=15,
            font=("Consolas", 10),
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("info", foreground="blue")

        # Контекстное меню для лога
        self.create_context_menu()

        # Меню
        self.create_menu()

    def create_context_menu(self):
        """Создание контекстного меню для лога"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(
            label="Копировать", command=self.copy_selection)
        self.context_menu.add_command(
            label="Копировать всё", command=self.copy_all)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Очистить", command=self.clear_log)

        self.log_text.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Показ контекстного меню"""
        self.context_menu.post(event.x_root, event.y_root)

    def copy_selection(self):
        """Копирование выделенного текста"""
        try:
            selected_text = self.log_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            pass  # Ничего не выделено

    def copy_all(self):
        """Копирование всего текста"""
        text = self.log_text.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def create_menu(self):
        """Создание главного меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Сохранить лог...", command=self.save_log)
        file_menu.add_command(label="Очистить лог", command=self.clear_log)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_closing)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=edit_menu)
        edit_menu.add_command(label="Копировать выделенное",
                              command=self.copy_selection)
        edit_menu.add_command(label="Копировать всё", command=self.copy_all)

    def is_valid_host(self, host: str) -> bool:
        """Проверка валидности хоста/IP"""
        if not host or len(host) > 255:
            return False

        # Проверка IP
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ip_pattern, host):
            return all(0 <= int(i) <= 255 for i in host.split('.'))

        # Проверка домена
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'
        return bool(re.match(domain_pattern, host))

    def safe_ping(self, host: str) -> bool:
        """Безопасное выполнение ping"""
        try:
            if platform.system().lower() == 'windows':
                command = ['ping', '-n', '1', '-w', '1000', host]
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                result = subprocess.run(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    startupinfo=startupinfo,
                    timeout=5
                )
            else:
                # Для Unix-систем используем shlex.quote
                safe_host = shlex.quote(host)
                command = ['ping', '-c', '1', '-W', '1', safe_host]
                result = subprocess.run(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5
                )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    def toggle_monitoring(self):
        """Переключение состояния мониторинга"""
        if self.stop_event.is_set():  # Если мониторинг остановлен
            if self.thread and self.thread.is_alive():
                messagebox.showerror("Ошибка", "Мониторинг уже запущен")
                return

            host = self.host_entry.get().strip()
            if not self.is_valid_host(host):
                messagebox.showerror("Ошибка", "Некорректный формат хоста")
                return

            try:
                interval = max(1, int(self.interval_entry.get()))
            except ValueError:
                messagebox.showerror(
                    "Ошибка", "Интервал должен быть целым числом")
                return

            self.stop_event.clear()
            self.stats.reset()
            self.stats.start_time = datetime.now()
            self.stats.current_status = "Запущен"

            self.start_button.configure(text="Стоп")
            self.host_entry.configure(state='disabled')
            self.interval_entry.configure(state='disabled')

            self.thread = threading.Thread(
                target=self.monitor,
                args=(host, interval),
                daemon=True
            )
            self.thread.start()
        else:  # Если мониторинг запущен
            self.stop_monitoring()

    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            if self.thread.is_alive():
                self.logger.warning(
                    "Не удалось корректно остановить поток мониторинга")

        self.stats.current_status = "Остановлен"
        self.start_button.configure(text="Старт")
        self.host_entry.configure(state='normal')
        self.interval_entry.configure(state='normal')

    def monitor(self, host: str, interval: int):
        """Функция мониторинга"""
        self.log(
            f"Мониторинг запущен для хоста {host} (интервал {interval} сек)", "info")
        failed_attempts = 0

        while not self.stop_event.is_set():
            self.stats.total_pings += 1
            if not self.safe_ping(host):
                failed_attempts += 1
                self.stats.failed_pings += 1
                self.stats.last_failure = datetime.now()

                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                error_msg = f"{timestamp} - Хост {host} недоступен (попытка {failed_attempts})"
                self.logger.error(error_msg)
                self.log(error_msg, "error")
                self.beep()
            else:
                if failed_attempts > 0:
                    self.log(f"Соединение с {host} восстановлено", "success")
                failed_attempts = 0

            self.stop_event.wait(interval)

        self.log("Мониторинг остановлен", "info")

    def update_stats(self):
        """Обновление статистики"""
        if self.stats.start_time:
            uptime = datetime.now() - self.stats.start_time
            hours = int(uptime.total_seconds() // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)

            self.stats_labels["status"].configure(
                text=self.stats.current_status,
                style="Success.TLabel" if self.stats.current_status == "Запущен" else ""
            )
            self.stats_labels["total"].configure(
                text=str(self.stats.total_pings))
            self.stats_labels["failed"].configure(
                text=str(self.stats.failed_pings),
                style="Error.TLabel" if self.stats.failed_pings > 0 else ""
            )
            self.stats_labels["uptime"].configure(text=f"{hours}ч {minutes}м")
            self.stats_labels["last_failure"].configure(
                text=self.stats.last_failure.strftime(
                    '%Y-%m-%d %H:%M:%S') if self.stats.last_failure else "-"
            )

        self.root.after(1000, self.update_stats)

    def beep(self):
        """Звуковой сигнал"""
        try:
            if platform.system() == 'Windows':
                import winsound
                winsound.Beep(1000, 500)
            else:
                os.system('echo -e "\a"')
        except Exception as e:
            self.logger.error(f"Ошибка звукового сигнала: {e}")

    def log(self, message: str, level: str = "info"):
        """Логирование сообщений"""
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, message + '\n', level)

        # Ограничение размера лога
        lines = self.log_text.get('1.0', tk.END).splitlines()
        if len(lines) > MAX_LOG_LINES:
            self.log_text.delete('1.0', f"{len(lines) - MAX_LOG_LINES}.0")

        self.log_text.see(tk.END)
        self.log_text.configure(state='normal')

    def save_log(self):
        """Сохранение лога в файл"""
        try:
            filename = f"ping_monitor_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get('1.0', tk.END))
            messagebox.showinfo("Успех", f"Лог сохранен в файл: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить лог: {e}")

    def clear_log(self):
        """Очистка лога"""
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.configure(state='disabled')

    def load_config(self):
        """Загрузка конфигурации"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
        except Exception as e:
            self.logger.warning(f"Ошибка загрузки конфигурации: {e}")

    def save_config(self):
        """Сохранение конфигурации"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({
                    'last_host': self.host_entry.get(),
                    'last_interval': int(self.interval_entry.get())
                }, f)
        except Exception as e:
            self.logger.error(f"Ошибка сохранения конфигурации: {e}")
            messagebox.showerror("Ошибка", "Не удалось сохранить настройки")

    def on_closing(self):
        """Обработка закрытия программы"""
        if not self.stop_event.is_set():
            self.stop_monitoring()
        self.save_config()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PingMonitorApp(root)
    root.mainloop()
