import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import shutil
# from config import chatconf
import configparser

script_dir = Path(__file__).parent  # Определяем путь к текущему скрипту
data_dir = script_dir / 'data'
msg_hist_dir = script_dir / 'data/msg_hits'   #папка с историями сообщений
msg_arch_dir = msg_hist_dir / 'archive'    #папка с историями удалившихся пользователей
config_file = data_dir / 'config.ini'

config = configparser.ConfigParser()  # настраиваем и читаем файл конфига
config.read(config_file)


def save_message_to_json(chat_id, role, message, sender_name=None, user_name=None): #добавление сообщения

    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла
    
    new_message = {    # Структура нового сообщения
        "role": role,
        "content": message
    }
 
    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  #, загружаем существующие данные
            data = json.load(file)    
    else:
        today_date = datetime.now().strftime('%Y-%m-%d')        # Если файл не существует, создаем начальную структуру с именем отправителя и счётчиком
        data = {
            "Sender Name": sender_name,
            "Username": user_name,
            "Messages Today": 0,
            "Spam Flag": 0,
            "NoRole Q Flag": 0,
            "Games Count": 1,
            "Last Update Date": today_date,
            "Last Game": "2025-01-01",
            "Messages": [],
            "Ban": 0
        }

    # Обновляем Sender Name и Username
    if sender_name is not None:
        data["Sender Name"] = sender_name
    if user_name is not None:
        data["Username"] = user_name  

    # Увеличиваем счётчик сообщений, если это ответ бота
    if role == "assistant":
        data["Messages Today"] += 1

    data["Messages"].append(new_message)    # Добавляем новое сообщение в массив "Messages"

    with open(file_name, mode='w', encoding='utf-8') as file:    # Сохраняем обновленные данные обратно в файл
        json.dump(data, file, ensure_ascii=False, indent=4)



def get_msg_count(chat_id): #получтиь количетсво сообщений от пользователя за сегодня (возвоащает или кол-во или 0, если пользователь не зарегестрирован)

    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла

    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  #, загружаем существующие данные
            data = json.load(file)
            
        today_date = datetime.now().strftime('%Y-%m-%d')  # Получаем текущую дату
        last_update_date = data.get("Last Update Date")  # Получаем дату последнего обновления
        
        # Если дата изменилась
        if last_update_date != today_date:
            data["Messages Today"] = 0  # Сброс счётчика
            data["Last Update Date"] = today_date  # Обновляем дату
            
    else:
        return 0     # Если файл не существует, отдаём 0
        
    msgs_count = data.get("Messages Today")

    with open(file_name, mode='w', encoding='utf-8') as file:    # Сохраняем обновленные(или нет) данные обратно в файл
        json.dump(data, file, ensure_ascii=False, indent=4)
        
    return msgs_count
        
    

def get_last_messages(chat_id): #извлечение последних count сообщений из chat_id
    
    count = int(config['chatconf']['latest_posts'])    #сколько сообщений из чата вытаскивать 
    
    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла
        
    if os.path.isfile(file_name):    # Проверяем, существует ли файл
        
        with open(file_name, mode='r', encoding='utf-8') as file:    # Загружаем данные из файла
            data = json.load(file)
            
        messages = data.get("Messages", [])    # Извлекаем массив сообщений    
        last_messages = messages[-count:] if count > 0 else []    # Берем последние `count` сообщений из конца массива
        
        return last_messages
    
    else:
        return False #лож, если файла нет
        


def remove_limit(chat_id): #обнуление лимита

    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла

    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  #, загружаем существующие данные
            data = json.load(file)
            
        data["Messages Today"] = 0  # Сброс счётчика     
           
        with open(file_name, mode='w', encoding='utf-8') as file:    # Сохраняем обновленные данные обратно в файл
            json.dump(data, file, ensure_ascii=False, indent=4)
        


def clear_context(chat_id, sender_name=None, user_name=None): #очистка контекста

    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла

    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  #, загружаем существующие данные
            data = json.load(file)
            
        data["Messages"] = []  # пустой массив
    else: #создаём, если нет
        
        today_date = datetime.now().strftime('%Y-%m-%d')        # Если файл не существует, создаем начальную структуру с именем отправителя и счётчиком
        data = {
            "Sender Name": sender_name,
            "Username": user_name,
            "Messages Today": 0,
            "Spam Flag": 0,
            "NoRole Q Flag": 0,
            "Games Count": 1,
            "Last Update Date": today_date,
            "Last Game": "2025-01-01",
            "Messages": [],
            "Ban": 0
        }
        
    with open(file_name, mode='w', encoding='utf-8') as file:    # Сохраняем обновленные данные обратно в файл
        json.dump(data, file, ensure_ascii=False, indent=4)
            
     
     
def flag(chat_id, param, variable=None): # флаг  (если третий аргумент не передан - возвращает факт состояние ,если передан - меняет состояние на переданный )   

    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла

    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  #, загружаем существующие данные
            data = json.load(file)
        
        if variable is not None:            
            
            data[param] = variable  # присвоить param состояние флага (если что то передали функции)            
            with open(file_name, mode='w', encoding='utf-8') as file:    # Сохраняем обновленные данные обратно в файл
                json.dump(data, file, ensure_ascii=False, indent=4)
            
        else:
            state = data.get(param)
            return state



def arch_chat(chat_id):#---Архивирование чата chat_id-------------------------------------------------------
    
    source_path = msg_hist_dir / f'{chat_id}.json'
    
    if not os.path.exists(source_path):    # Проверяем, существует ли исходный чат
        return

    if not os.path.exists(msg_arch_dir):    # Проверяем, существует ли папка назначения, и создаем её, если нужно
        os.makedirs(msg_arch_dir)

    filename = os.path.basename(source_path)    # Получаем имя файла и расширение
    name, ext = os.path.splitext(filename)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")    # Генерируем текущую дату и время в формате YYYY-MM-DD_HH-MM-SS

    new_filename = f"{name}_{timestamp}{ext}"    # Создаем новое имя файла
    destination_path = os.path.join(msg_arch_dir, new_filename)

    shutil.move(source_path, destination_path)    # Перемещаем файл



def get_actual_ids(): #---Получение списка пользователей в виде массива-----------------------+
    json_filenames = []

    for filename in os.listdir(msg_hist_dir):    # Перебираем все файлы в папке
        if filename.endswith('.json'):        # Проверяем, имеет ли файл расширение .json
            json_filenames.append(os.path.splitext(filename)[0])            # Добавляем имя файла без расширения в массив

    return json_filenames
     

def get_active_users():#---получить кол-во активных пользователей----------------------------+
    try:
        # Получаем список файлов и папок в указанной директории
        files = os.listdir(msg_hist_dir)
        # Фильтруем только файлы с расширением .json
        json_files = [file for file in files if file.endswith('.json') and os.path.isfile(os.path.join(msg_hist_dir, file))]
        return len(json_files)
    except FileNotFoundError:
        return 'error'
    except PermissionError:
        return 'err'
    
    
def get_departed_users():#---получить количество ушедших пользователей-----------------------+
    try:
        # Получаем список файлов и папок в указанной директории
        files = os.listdir(msg_arch_dir)
        # Фильтруем только файлы с расширением .json
        json_files = [file for file in files if file.endswith('.json') and os.path.isfile(os.path.join(msg_arch_dir, file))]
        return len(json_files)
    except FileNotFoundError:
        return 'пока-что 0'
    except PermissionError:
        return 'error'
    
    
def is_banned(chat_id):
    """возвращает, забанен ли пользователь
    
    Args:
        chat_id (str): id пользователя

    Returns:
        bool: True или False
    """

    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла

    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  # Загружаем существующие данные
            data = json.load(file)
        
        # Возвращаем значение "Games Count" или 0, если ключ отсутствует
        return data.get("Ban", 0)

    
    