import asyncio
import random
import json
import os
import sys
import subprocess

# Попытка импорта requests для мощного обновления
try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError, RPCError

# --- НАСТРОЙКИ ОБНОВЛЕНИЯ ---
CURRENT_VERSION = "1.5.0"
# Ссылка на файл с версией (там должна быть только цифра, например 1.6.0)
VERSION_URL = "https://raw.githubusercontent.com/miskabejbu-byte/soft/main/version.txt"
# Ссылка на сам файл скрипта (.py) для скачивания
SCRIPT_URL = "https://raw.githubusercontent.com/miskabejbu-byte/soft/main/main.py"

# Настройка для Windows
try:
    import msvcrt
    WINDOWS = True
except ImportError:
    WINDOWS = False

class Colors:
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

BANNER_RAW = r"""
     _               _                     _   
    | |__  _   _    | |__   __ _ _ __   ___| |_ 
    | '_ \| | | |   | '_ \ / _` | '_ \ / _ \ __|
    | |_) | |_| |   | | | | (_| | | | |  __/ |_ 
    |_.__/ \__, |   |_| |_|\__,_|_| |_|\___|\__|
           |___/                                
"""

def char_gradient(text, start_count=0):
    result = ""
    count = start_count
    for char in text:
        if char in [' ', '\n', '\t', '\r']:
            result += char
            continue
        color = Colors.BLUE if count % 2 == 0 else Colors.CYAN
        result += f"{color}{char}{Colors.RESET}"
        count += 1
    return result

def clear_screen():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def gradient_input(prompt):
    if not WINDOWS:
        sys.stdout.write(char_gradient(prompt))
        sys.stdout.flush()
        return input()
    sys.stdout.write(char_gradient(prompt))
    sys.stdout.flush()
    user_input = ""
    count = 0
    try:
        while True:
            if msvcrt.kbhit():
                char = msvcrt.getwch()
                if char in ('\r', '\n'):
                    sys.stdout.write('\n')
                    break
                elif char == '\b':
                    if len(user_input) > 0:
                        user_input = user_input[:-1]
                        count -= 1
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                elif ord(char) < 32: continue
                else:
                    user_input += char
                    color = Colors.BLUE if count % 2 == 0 else Colors.CYAN
                    sys.stdout.write(f"{color}{char}{Colors.RESET}")
                    sys.stdout.flush()
                    count += 1
            else:
                import time
                time.sleep(0.01)
    except: return input()
    return user_input

def power_update():
    """Мощное автообновление: проверка, скачивание и перезапуск."""
    if not HAS_REQUESTS:
        print(char_gradient("[!] Для автообновления нужно: pip install requests"))
        return

    print(char_gradient(f"[*] Проверка обновлений... (Текущая: {CURRENT_VERSION})"))
    try:
        headers = {'User-Agent': 'Mozilla/5.0', 'Cache-Control': 'no-cache'}
        r = requests.get(VERSION_URL, headers=headers, verify=False, timeout=10)
        
        if r.status_code == 200:
            remote_version = r.text.strip()
            print(char_gradient(f"[*] Версия на GitHub: {remote_version}"))
            
            if remote_version != CURRENT_VERSION:
                print(char_gradient(f"[!] Найдена новая версия! Обновляюсь..."))
                
                new_code = requests.get(SCRIPT_URL, headers=headers, verify=False, timeout=15)
                if new_code.status_code == 200:
                    file_path = os.path.abspath(sys.argv[0])
                    with open(file_path, 'wb') as f:
                        f.write(new_code.content)
                    
                    print(char_gradient("[+] Файл обновлен. Перезапуск..."))
                    if os.name == 'nt':
                        subprocess.Popen([sys.executable, file_path])
                    else:
                        os.execv(sys.executable, [sys.executable] + sys.argv)
                    sys.exit()
            else:
                print(char_gradient("[+] У вас последняя версия.\n"))
        else:
            print(char_gradient(f"[!] Ошибка сервера: {r.status_code}\n"))
    except Exception as e:
        print(char_gradient(f"[!] Ошибка связи с GitHub. Пропускаю...\n"))

def resolve_id(target):
    target = str(target).strip()
    if target.startswith('-') and target[1:].isdigit(): return int(target)
    if target.isdigit(): return int(target)
    return target

async def send_words_task(client, target_group, text, delay):
    target_entity = resolve_id(target_group)
    words = text.split()
    for word in words:
        if not word.strip(): continue
        try:
            await client.send_message(target_entity, word)
            await asyncio.sleep(delay if delay > 0 else 0.02)
        except FloodWaitError as e:
            print(char_gradient(f"\n[!] Флуд: ждем {e.seconds} сек..."))
            await asyncio.sleep(e.seconds)
        except asyncio.CancelledError: return
        except: break

def generate_fake_info(gender):
    countries = ["Россия", "Украина"]
    country = random.choice(countries)
    cities = ["Москва", "Київ", "Одеса", "Казань"]
    names = ["Александр", "Мария", "Дмитрий", "Анна"]
    return f"\n--- ДАННЫЕ ---\nФИО: {random.choice(names)}\nГород: {random.choice(cities)}\nВозраст: {random.randint(11, 17)}\n-------------"

CONFIG_FILE = 'config.json'
current_sending_task = None

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

async def main():
    global current_sending_task
    config = load_config()
    clear_screen()
    print(char_gradient(BANNER_RAW))
    print(char_gradient(f"юз: hanet0_0 | Роль: Creator | Версия: {CURRENT_VERSION}\n"))

    power_update()

    if 'api_id' not in config:
        config['api_id'] = int(gradient_input("Введите API ID: ").strip())
        config['api_hash'] = gradient_input("Введите API HASH: ").strip()
        save_config(config)

    client = TelegramClient('hanet_session', config['api_id'], config['api_hash'])
    await client.connect()

    if not await client.is_user_authorized():
        phone = gradient_input("Phone: ").strip()
        await client.send_code_request(phone)
        code = gradient_input("Code: ").strip()
        try: await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            pwd = gradient_input("2FA: ").strip()
            await client.sign_in(password=pwd)

    target_group = config.get('target_group', 'не указана')
    print(char_gradient(f"[*] Цель: {target_group}"))
    new_target = gradient_input("[?] Новая цель (Enter для пропуска): ").strip()
    if new_target:
        config['target_group'] = new_target
        save_config(config)
        target_group = new_target

    try:
        while True:
            clear_screen()
            print(char_gradient(BANNER_RAW))
            print(char_gradient(f"юз: hanet0_0 | Роль: Creator\n"))
            print(char_gradient("[1] Троллинг\n[2] Создать лож инфу\n[3] Выход"))
            choice = await asyncio.to_thread(gradient_input, "Выберите действие: ")
            
            if choice == '1':
                clear_screen()
                print(char_gradient("[1] Turbo | [2] Normal | [3] Safe | [стоп] Назад"))
                speed = await asyncio.to_thread(gradient_input, "Скорость >> ")
                if speed.lower().strip() == 'стоп': continue
                delay = {"1": 0.0, "2": 0.2, "3": 0.8}.get(speed, 0.2)
                
                clear_screen()
                print(char_gradient(f"Троллинг (Цель: {target_group}). Введите текст или 'стоп':\n"))
                while True:
                    text = await asyncio.to_thread(gradient_input, "Текст >> ")
                    if text.lower().strip() == 'стоп':
                        if current_sending_task: current_sending_task.cancel()
                        break
                    if text.strip():
                        if current_sending_task: current_sending_task.cancel()
                        current_sending_task = asyncio.create_task(send_words_task(client, target_group, text, delay))

            elif choice == '2':
                clear_screen()
                print(char_gradient("[1] Парень | [2] Девушка | [стоп] Назад\n"))
                g_choice = await asyncio.to_thread(gradient_input, "Пол >> ")
                if g_choice.lower().strip() == 'стоп': continue
                gender = "девушка" if g_choice == "2" else "парень"
                print(char_gradient(generate_fake_info(gender)))
                await asyncio.to_thread(gradient_input, "\nНажмите Enter для меню: ")

            elif choice == '3' or choice.lower().strip() == 'выход': break
    finally:
        await client.disconnect()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt: pass
    except Exception as e:
        print(char_gradient(f"\n[КРИТИЧЕСКАЯ ОШИБКА] {e}"))
