#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║               NEXUS: DEEP SPACE RPG — LAUNCHER              ║
║                                                              ║
║  Автоматическая проверка и установка всех зависимостей:      ║
║  • Python пакеты (Flask, Requests)                          ║
║  • Ollama (локальный AI-сервер)                             ║
║  • AI модель (скачивание если отсутствует)                   ║
║                                                              ║
║  После проверки — запуск игрового сервера + открытие в       ║
║  браузере.                                                   ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import json
import subprocess
import webbrowser
import shutil
import platform
from pathlib import Path

# ════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ ЛАУНЧЕРА — меняйте под свои нужды
# ════════════════════════════════════════════════════════════

LAUNCHER_CONFIG = {
    # Рекомендованная модель (можно сменить в настройках игры)
    "default_model": "hf.co/mradermacher/MN-Violet-Lotus-12B-GGUF:Q4_K_M",

    # Минимальные fallback-модели (маленькие, для слабых ПК)
    "fallback_models": [
        "llama3.1:8b",
        "gemma2:9b",
    ],

    # Порт игрового сервера
    "game_port": 8080,

    # Авто-открытие браузера
    "open_browser": True,

    # Ollama URL
    "ollama_url": "http://localhost:11434",

    # Путь для скачивания Ollama (Windows)
    "ollama_installer_url": "https://ollama.com/download/OllamaSetup.exe",
}

# ════════════════════════════════════════════════════════════
# ЦВЕТА И UI
# ════════════════════════════════════════════════════════════

class Colors:
    """ANSI цвета для терминала."""
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    MAGENTA = "\033[95m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"

    @staticmethod
    def init():
        """Включить ANSI цвета на Windows."""
        if platform.system() == "Windows":
            os.system("color")  # Enable ANSI in cmd
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except Exception:
                pass


def banner():
    Colors.init()
    print(f"""
{Colors.CYAN}{Colors.BOLD}
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║     ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗      ║
    ║     ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝      ║
    ║     ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗      ║
    ║     ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║      ║
    ║     ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║      ║
    ║     ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝      ║
    ║                                                       ║
    ║           D E E P   S P A C E   R P G                 ║
    ║                  L A U N C H E R                      ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
{Colors.RESET}""")


def status(icon, msg, color=Colors.RESET):
    print(f"  {color}{icon} {msg}{Colors.RESET}")


def step_header(num, title):
    print(f"\n{Colors.BOLD}{Colors.CYAN}  [{num}/5] {title}{Colors.RESET}")
    print(f"  {'─' * 50}")


def ask_yes_no(question, default=True):
    """Спросить да/нет у пользователя."""
    hint = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"  {Colors.YELLOW}? {question} {hint}: {Colors.RESET}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    if not answer:
        return default
    return answer in ("y", "yes", "д", "да", "1")


def ask_choice(question, options):
    """Выбор из списка опций."""
    print(f"\n  {Colors.YELLOW}? {question}{Colors.RESET}")
    for i, opt in enumerate(options, 1):
        print(f"    {Colors.CYAN}{i}{Colors.RESET}) {opt}")
    while True:
        try:
            choice = input(f"  {Colors.YELLOW}  Ваш выбор (1-{len(options)}): {Colors.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return int(choice) - 1
        print(f"  {Colors.RED}  Введите число от 1 до {len(options)}{Colors.RESET}")


# ════════════════════════════════════════════════════════════
# ПРОВЕРКИ ЗАВИСИМОСТЕЙ
# ════════════════════════════════════════════════════════════

def check_python():
    """Шаг 1: Проверка Python."""
    step_header(1, "PYTHON")

    ver = platform.python_version()
    major, minor = sys.version_info[:2]

    if major < 3 or (major == 3 and minor < 9):
        status("✗", f"Python {ver} — слишком старая версия (нужен 3.9+)", Colors.RED)
        status("→", "Скачайте Python 3.11+ с https://python.org/downloads/", Colors.YELLOW)
        status("→", "ВАЖНО: при установке отметьте 'Add Python to PATH'", Colors.YELLOW)
        return False

    status("✓", f"Python {ver} — OK", Colors.GREEN)
    return True


def check_pip_packages():
    """Шаг 2: Проверка и установка pip-пакетов."""
    step_header(2, "PYTHON ПАКЕТЫ")

    required = {
        "flask": "flask>=3.0.0",
        "requests": "requests>=2.31.0",
    }

    missing = []
    for pkg_name, pip_spec in required.items():
        try:
            __import__(pkg_name)
            status("✓", f"{pkg_name} — установлен", Colors.GREEN)
        except ImportError:
            status("✗", f"{pkg_name} — не найден", Colors.RED)
            missing.append(pip_spec)

    if not missing:
        return True

    status("→", f"Устанавливаю {len(missing)} пакет(ов)...", Colors.YELLOW)
    try:
        cmd = [sys.executable, "-m", "pip", "install"] + missing + ["--quiet"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            status("✓", "Все пакеты установлены", Colors.GREEN)
            return True
        else:
            status("✗", f"Ошибка pip: {result.stderr[:200]}", Colors.RED)
            status("→", "Попробуйте вручную: pip install flask requests", Colors.YELLOW)
            return False
    except subprocess.TimeoutExpired:
        status("✗", "Таймаут установки пакетов", Colors.RED)
        return False
    except FileNotFoundError:
        status("✗", "pip не найден", Colors.RED)
        status("→", "Установите: python -m ensurepip --upgrade", Colors.YELLOW)
        return False


def check_ollama():
    """Шаг 3: Проверка Ollama."""
    step_header(3, "OLLAMA (AI СЕРВЕР)")

    # Проверка: есть ли ollama в PATH?
    ollama_path = shutil.which("ollama")

    if ollama_path:
        status("✓", f"Ollama найден: {ollama_path}", Colors.GREEN)
    else:
        status("✗", "Ollama не найден в системе", Colors.RED)

        if platform.system() == "Windows":
            status("→", "Ollama нужен для запуска AI. Варианты:", Colors.YELLOW)
            choice = ask_choice("Как установить Ollama?", [
                "Скачать автоматически (рекомендуется)",
                "Я установлю сам (https://ollama.com/download)",
                "Пропустить (игра не будет работать без AI)",
            ])

            if choice == 0:
                return download_and_install_ollama()
            elif choice == 1:
                status("→", "Установите Ollama и перезапустите лаунчер", Colors.YELLOW)
                webbrowser.open("https://ollama.com/download")
                return False
            else:
                status("⚠", "Продолжаю без Ollama (AI не будет работать)", Colors.YELLOW)
                return True  # Allow game to start, AI just won't work

        elif platform.system() == "Linux":
            status("→", "Установка: curl -fsSL https://ollama.com/install.sh | sh", Colors.YELLOW)
            if ask_yes_no("Установить Ollama сейчас?"):
                try:
                    subprocess.run("curl -fsSL https://ollama.com/install.sh | sh",
                                   shell=True, timeout=300)
                    if shutil.which("ollama"):
                        status("✓", "Ollama установлен", Colors.GREEN)
                        return check_ollama_running()
                except Exception as e:
                    status("✗", f"Ошибка установки: {e}", Colors.RED)
            return False

        elif platform.system() == "Darwin":  # macOS
            status("→", "Установка: brew install ollama", Colors.YELLOW)
            status("→", "Или скачайте: https://ollama.com/download", Colors.YELLOW)
            webbrowser.open("https://ollama.com/download")
            return False

    # Ollama есть — проверяем, запущен ли сервер
    return check_ollama_running()


def download_and_install_ollama():
    """Скачать и установить Ollama на Windows."""
    try:
        import requests
    except ImportError:
        status("✗", "Нужен requests для скачивания", Colors.RED)
        return False

    url = LAUNCHER_CONFIG["ollama_installer_url"]
    installer_path = os.path.join(os.environ.get("TEMP", "."), "OllamaSetup.exe")

    status("↓", f"Скачиваю Ollama...", Colors.YELLOW)
    try:
        resp = requests.get(url, stream=True, timeout=30)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0

        with open(installer_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded * 100 // total
                    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                    print(f"\r  ↓ [{bar}] {pct}% ({downloaded // 1048576}MB)", end="", flush=True)
        print()

        status("→", "Запускаю установщик Ollama...", Colors.YELLOW)
        status("→", "Следуйте инструкциям в окне установки", Colors.YELLOW)
        subprocess.run([installer_path], timeout=600)

        # Дожидаемся установки
        time.sleep(3)
        if shutil.which("ollama"):
            status("✓", "Ollama установлен!", Colors.GREEN)
            return check_ollama_running()
        else:
            status("⚠", "Ollama установлен, но не найден в PATH", Colors.YELLOW)
            status("→", "Перезапустите лаунчер после завершения установки", Colors.YELLOW)
            return False

    except Exception as e:
        status("✗", f"Ошибка скачивания: {e}", Colors.RED)
        status("→", "Скачайте вручную: https://ollama.com/download", Colors.YELLOW)
        return False


def check_ollama_running():
    """Проверить, запущен ли сервер Ollama."""
    try:
        import requests
        resp = requests.get(f"{LAUNCHER_CONFIG['ollama_url']}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m.get("name", "") for m in resp.json().get("models", [])]
            status("✓", f"Ollama запущен ({len(models)} моделей)", Colors.GREEN)
            return True
    except Exception:
        pass

    status("⚠", "Ollama установлен, но сервер не запущен", Colors.YELLOW)
    status("→", "Запускаю Ollama...", Colors.YELLOW)

    try:
        # На Windows запускаем ollama serve в фоне
        if platform.system() == "Windows":
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )
        else:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # Ждём запуска (до 15 секунд)
        for i in range(15):
            time.sleep(1)
            try:
                import requests
                resp = requests.get(f"{LAUNCHER_CONFIG['ollama_url']}/api/tags", timeout=2)
                if resp.status_code == 200:
                    status("✓", "Ollama запущен!", Colors.GREEN)
                    return True
            except Exception:
                print(f"\r  ⏳ Ожидание... {i+1}/15с", end="", flush=True)
        print()
        status("✗", "Ollama не запустился за 15 секунд", Colors.RED)
        status("→", "Запустите вручную: ollama serve", Colors.YELLOW)
        return False

    except FileNotFoundError:
        status("✗", "Команда 'ollama' не найдена", Colors.RED)
        return False


def check_model():
    """Шаг 4: Проверка AI модели."""
    step_header(4, "AI МОДЕЛЬ")

    try:
        import requests
    except ImportError:
        status("⚠", "Пропускаю проверку модели (нет requests)", Colors.YELLOW)
        return True

    # Получаем список установленных моделей
    try:
        resp = requests.get(f"{LAUNCHER_CONFIG['ollama_url']}/api/tags", timeout=5)
        models = [m.get("name", "") for m in resp.json().get("models", [])]
    except Exception:
        status("⚠", "Не удалось подключиться к Ollama, пропускаю", Colors.YELLOW)
        return True

    if models:
        status("✓", f"Установлены модели:", Colors.GREEN)
        for m in models:
            size_info = ""
            for md in resp.json().get("models", []):
                if md.get("name") == m:
                    size_gb = md.get("size", 0) / (1024**3)
                    if size_gb > 0:
                        size_info = f" ({size_gb:.1f} GB)"
            status("  ", f"• {m}{size_info}", Colors.DIM)

    # Проверяем рекомендованную модель
    default_model = LAUNCHER_CONFIG["default_model"]
    
    # Нормализуем имена для сравнения (убираем :latest)
    normalized_models = []
    for m in models:
        normalized_models.append(m)
        if ":" not in m:
            normalized_models.append(m + ":latest")

    model_found = any(default_model in m or m in default_model for m in normalized_models)

    if model_found:
        status("✓", f"Рекомендованная модель найдена: {default_model}", Colors.GREEN)
        return True

    if models:
        # Есть другие модели — можно играть
        status("⚠", f"Рекомендованная модель не найдена: {default_model}", Colors.YELLOW)
        choice = ask_choice("Что делать?", [
            f"Скачать рекомендованную модель ({default_model})",
            f"Использовать {models[0]} (уже установлена)",
            "Выбрать другую модель из списка",
            "Пропустить (настрою позже в игре)",
        ])

        if choice == 0:
            return pull_model(default_model)
        elif choice == 1:
            update_config_model(models[0])
            return True
        elif choice == 2:
            idx = ask_choice("Выберите модель:", models)
            update_config_model(models[idx])
            return True
        else:
            return True
    else:
        # Нет моделей вообще
        status("✗", "Нет установленных AI моделей", Colors.RED)
        choice = ask_choice("Какую модель скачать?", [
            f"{default_model} (рекомендованная, ~7GB)",
            "llama3.1:8b (универсальная, ~4.7GB)",
            "gemma2:9b (компактная, ~5.4GB)",
            "Введу название модели вручную",
        ])

        if choice == 0:
            return pull_model(default_model)
        elif choice == 1:
            return pull_model("llama3.1:8b")
        elif choice == 2:
            return pull_model("gemma2:9b")
        elif choice == 3:
            custom = input(f"  {Colors.YELLOW}  Название модели: {Colors.RESET}").strip()
            if custom:
                return pull_model(custom)
        return False


def pull_model(model_name):
    """Скачать модель через Ollama."""
    status("↓", f"Скачиваю модель: {model_name}", Colors.YELLOW)
    status("  ", "Это может занять несколько минут...", Colors.DIM)

    try:
        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        for line in iter(process.stdout.readline, ""):
            line = line.strip()
            if line:
                # Показываем прогресс
                if "pulling" in line.lower() or "downloading" in line.lower() or "%" in line:
                    print(f"\r  ↓ {line[:70]}", end="", flush=True)
                elif "success" in line.lower():
                    print()
                    status("✓", f"Модель {model_name} скачана!", Colors.GREEN)
                else:
                    print(f"\r  ↓ {line[:70]}", end="", flush=True)

        process.wait()
        print()

        if process.returncode == 0:
            status("✓", f"Модель готова: {model_name}", Colors.GREEN)
            update_config_model(model_name)
            return True
        else:
            status("✗", f"Ошибка скачивания (код {process.returncode})", Colors.RED)
            return False

    except FileNotFoundError:
        status("✗", "Команда 'ollama' не найдена", Colors.RED)
        return False
    except Exception as e:
        status("✗", f"Ошибка: {e}", Colors.RED)
        return False


def update_config_model(model_name):
    """Обновить config.py с выбранной моделью."""
    if getattr(sys, 'frozen', False):
        config_path = os.path.join(os.path.dirname(sys.executable), "config.py")
    else:
        config_path = os.path.join(os.path.dirname(__file__), "config.py")
    if not os.path.exists(config_path):
        return

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Заменяем модель по умолчанию
        import re
        content = re.sub(
            r'OLLAMA_MODEL = os\.environ\.get\("OLLAMA_MODEL", "[^"]*"\)',
            f'OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "{model_name}")',
            content,
        )

        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)

        status("✓", f"config.py обновлён: модель = {model_name}", Colors.GREEN)
    except Exception as e:
        status("⚠", f"Не удалось обновить config.py: {e}", Colors.YELLOW)


# ════════════════════════════════════════════════════════════
# ЗАПУСК ИГРЫ
# ════════════════════════════════════════════════════════════

def launch_game():
    """Шаг 5: Запуск игрового сервера."""
    step_header(5, "ЗАПУСК ИГРЫ")

    # Определяем каталог игры
    if getattr(sys, 'frozen', False):
        game_dir = os.path.dirname(sys.executable)
    else:
        game_dir = os.path.dirname(os.path.abspath(__file__))

    server_path = os.path.join(game_dir, "src", "server", "app.py")
    if not os.path.exists(server_path):
        status("✗", f"Файл src/server/app.py не найден в {game_dir}", Colors.RED)
        return False

    port = LAUNCHER_CONFIG["game_port"]
    url = f"http://localhost:{port}"

    status("→", f"Запускаю NEXUS RPG на {url}", Colors.CYAN)
    print()
    print(f"  {Colors.BOLD}{Colors.GREEN}{'═' * 50}")
    print(f"  ║  Игра доступна: {url}")
    print(f"  ║  Для остановки нажмите Ctrl+C")
    print(f"  {'═' * 50}{Colors.RESET}")
    print()

    # Открываем браузер с задержкой
    if LAUNCHER_CONFIG["open_browser"]:
        import threading
        def open_browser():
            time.sleep(2)
            webbrowser.open(url)
        threading.Thread(target=open_browser, daemon=True).start()

    # ═══ ЗАПУСК СЕРВЕРА ═══
    os.chdir(game_dir)

    if getattr(sys, 'frozen', False):
        # === .EXE MODE: запускаем Flask IN-PROCESS ===
        # Python уже внутри .exe (PyInstaller), не нужен системный Python
        status("✓", "Режим .exe — встроенный Python", Colors.GREEN)
        try:
            # Добавляем каталог игры в путь поиска модулей
            if game_dir not in sys.path:
                sys.path.insert(0, game_dir)

            # Импортируем и запускаем Flask-сервер напрямую
            import importlib.util
            spec = importlib.util.spec_from_file_location("server", server_path)
            server_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(server_module)

            # Запускаем Flask
            server_module.app.run(
                host="127.0.0.1",
                port=port,
                debug=False,
                use_reloader=False,  # Важно: reloader не работает в .exe
            )
        except KeyboardInterrupt:
            print(f"\n\n  {Colors.YELLOW}Игра остановлена. До встречи, пилот!{Colors.RESET}\n")
        except Exception as e:
            status("✗", f"Ошибка запуска сервера: {e}", Colors.RED)
            import traceback
            traceback.print_exc()
            return False
    else:
        # === DEV MODE: запускаем как subprocess ===
        try:
            subprocess.run([sys.executable, "-m", "src.server.app"], cwd=game_dir)
        except KeyboardInterrupt:
            print(f"\n\n  {Colors.YELLOW}Игра остановлена. До встречи, пилот!{Colors.RESET}\n")
        except Exception as e:
            status("✗", f"Ошибка запуска: {e}", Colors.RED)
            return False

    return True


# ════════════════════════════════════════════════════════════
# ПРОВЕРКА ЦЕЛОСТНОСТИ ФАЙЛОВ ИГРЫ
# ════════════════════════════════════════════════════════════

def check_game_files():
    """Проверка наличия критических файлов игры."""
    if getattr(sys, 'frozen', False):
        game_dir = os.path.dirname(sys.executable)
    else:
        game_dir = os.path.dirname(os.path.abspath(__file__))

    critical_files = [
        "src/server/app.py",
        "src/core/engine.py",
        "src/config.py",
        "src/ai/connector.py",
        "src/systems/combat.py",
        "src/world/galaxy.py",
        "src/systems/subsystems.py",
        "templates/index.html",
        "static/app.js",
        "static/style.css",
    ]

    missing = []
    for f in critical_files:
        path = os.path.join(game_dir, f)
        if not os.path.exists(path):
            missing.append(f)

    if missing:
        status("✗", f"Отсутствуют файлы ({len(missing)}):", Colors.RED)
        for f in missing:
            status("  ", f"• {f}", Colors.RED)
        status("→", "Переустановите игру или распакуйте архив заново", Colors.YELLOW)
        return False

    # Проверка game_data
    game_data_dir = os.path.join(game_dir, "game_data")
    if os.path.isdir(game_data_dir):
        json_count = len([f for f in os.listdir(game_data_dir) if f.endswith(".json")])
        status("✓", f"Файлы игры — OK ({len(critical_files)} core + {json_count} data)", Colors.GREEN)
    else:
        status("✓", f"Файлы игры — OK ({len(critical_files)} core)", Colors.GREEN)

    return True


# ════════════════════════════════════════════════════════════
# ГЛАВНАЯ ФУНКЦИЯ
# ════════════════════════════════════════════════════════════

# Detect auto mode: when running as .exe, minimize questions
IS_FROZEN = getattr(sys, 'frozen', False)

def main():
    banner()

    game_dir = os.path.dirname(sys.executable) if IS_FROZEN \
               else os.path.dirname(os.path.abspath(__file__))
    print(f"  {Colors.DIM}Система: {platform.system()} {platform.release()}")
    print(f"  Каталог: {game_dir}{Colors.RESET}")

    if IS_FROZEN:
        # === .EXE MODE: автоматическая установка всего ===
        print(f"\n  {Colors.CYAN}🚀 Автоматическая подготовка...{Colors.RESET}")

        # Python — уже внутри .exe, пропускаем
        step_header(1, "PYTHON")
        status("✓", f"Python встроен в .exe", Colors.GREEN)

        # Пакеты — уже внутри .exe, пропускаем
        step_header(2, "PYTHON ПАКЕТЫ")
        status("✓", "Flask, Requests встроены", Colors.GREEN)

        # Файлы
        if not check_game_files():
            input(f"\n  {Colors.YELLOW}Нажмите Enter для выхода...{Colors.RESET}")
            sys.exit(1)

        # Ollama — автоустановка
        ollama_ok = check_ollama_auto()

        # Модель — автозагрузка
        model_ok = False
        if ollama_ok:
            model_ok = check_model_auto()

        if not ollama_ok:
            print(f"\n  {Colors.YELLOW}⚠ Ollama не установлен. AI не будет работать.")
            print(f"    Скачайте вручную: https://ollama.com/download{Colors.RESET}")
            if not ask_yes_no("Запустить игру без AI?"):
                sys.exit(0)

        # Запуск!
        launch_game()
    else:
        # === DEV MODE: интерактивная проверка ===
        results = {}

        results["python"] = check_python()
        if not results["python"]:
            input(f"\n  {Colors.YELLOW}Нажмите Enter для выхода...{Colors.RESET}")
            sys.exit(1)

        results["pip"] = check_pip_packages()

        if not check_game_files():
            input(f"\n  {Colors.YELLOW}Нажмите Enter для выхода...{Colors.RESET}")
            sys.exit(1)

        results["ollama"] = check_ollama()

        if results["ollama"]:
            results["model"] = check_model()
        else:
            results["model"] = False

        # Итог
        print(f"\n  {Colors.BOLD}{'═' * 50}{Colors.RESET}")
        all_ok = all(results.values())
        for name, ok in results.items():
            labels = {"python": "Python", "pip": "Пакеты", "ollama": "Ollama", "model": "AI Модель"}
            icon = f"{Colors.GREEN}✓" if ok else f"{Colors.YELLOW}⚠"
            print(f"  {icon} {labels.get(name, name)}{Colors.RESET}")
        print(f"  {Colors.BOLD}{'═' * 50}{Colors.RESET}")

        if not results.get("pip"):
            status("✗", "Критические пакеты не установлены.", Colors.RED)
            input(f"\n  {Colors.YELLOW}Нажмите Enter для выхода...{Colors.RESET}")
            sys.exit(1)

        if not all_ok:
            if not ask_yes_no("Не все компоненты готовы. Запустить игру всё равно?"):
                sys.exit(0)

        launch_game()


def check_ollama_auto():
    """Auto-install Ollama without asking (for .exe mode)."""
    step_header(3, "OLLAMA (AI СЕРВЕР)")

    ollama_path = shutil.which("ollama")
    if ollama_path:
        status("✓", f"Ollama найден: {ollama_path}", Colors.GREEN)
        return check_ollama_running()

    status("→", "Ollama не найден. Скачиваю автоматически...", Colors.YELLOW)

    if platform.system() == "Windows":
        return download_and_install_ollama()
    elif platform.system() == "Linux":
        try:
            status("→", "Устанавливаю Ollama...", Colors.YELLOW)
            subprocess.run("curl -fsSL https://ollama.com/install.sh | sh",
                           shell=True, timeout=300)
            if shutil.which("ollama"):
                status("✓", "Ollama установлен", Colors.GREEN)
                return check_ollama_running()
        except Exception as e:
            status("✗", f"Ошибка: {e}", Colors.RED)
    else:
        status("→", "Скачайте Ollama: https://ollama.com/download", Colors.YELLOW)
        webbrowser.open("https://ollama.com/download")

    return False


def check_model_auto():
    """Auto-pull the default model without asking (for .exe mode)."""
    step_header(4, "AI МОДЕЛЬ")

    try:
        import requests
        resp = requests.get(f"{LAUNCHER_CONFIG['ollama_url']}/api/tags", timeout=5)
        models = [m.get("name", "") for m in resp.json().get("models", [])]
    except Exception:
        status("⚠", "Не удалось подключиться к Ollama", Colors.YELLOW)
        return False

    default_model = LAUNCHER_CONFIG["default_model"]

    # Check if any model exists
    if models:
        # Check if default or similar exists
        model_found = any(default_model in m or m in default_model for m in models)
        if model_found:
            status("✓", f"Модель найдена: {default_model}", Colors.GREEN)
            return True
        # Has other models — use first available
        status("✓", f"Используем установленную: {models[0]}", Colors.GREEN)
        update_config_model(models[0])
        return True

    # No models — auto-pull default
    status("→", f"Скачиваю модель: {default_model}", Colors.YELLOW)
    status("  ", "Первый раз — это займёт 5-15 минут...", Colors.DIM)
    return pull_model(default_model)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {Colors.YELLOW}Отменено пользователем.{Colors.RESET}\n")
    except Exception as e:
        print(f"\n  {Colors.RED}Критическая ошибка: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        input(f"\n  {Colors.YELLOW}Нажмите Enter для выхода...{Colors.RESET}")
