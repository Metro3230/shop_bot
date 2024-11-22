import json
import os
from datetime import datetime
from pathlib import Path
from config import chatconf

script_dir = Path(__file__).parent  # Определяем путь к текущему скрипту
msg_hist_dir = script_dir / 'data/msg_hits'   #папка с историями сообщений



def save_message_to_json(chat_id, role, sender_name, message): #добавление сообщения

    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла
    
    new_message = {    # Структура нового сообщения
        "role": role,
        "content": message
    }

    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  #, загружаем существующие данные
            data = json.load(file)
        today_date = datetime.now().strftime('%Y-%m-%d')    # Проверка даты последнего сообщения и обнуление счётчика, если день изменился
        if data.get("Last Update Date") != today_date:
            data["Messages Today"] = 0  # Сброс счётчика
            data["Last Update Date"] = today_date  # Обновляем дату
    else:
        today_date = datetime.now().strftime('%Y-%m-%d')        # Если файл не существует, создаем начальную структуру с именем отправителя и счётчиком
        data = {
            "Sender Name": sender_name,
            "Messages Today": 0,
            "Spam_Flag": 0,
            "Last Update Date": today_date,
            "Messages": []
        }

    # Увеличиваем счётчик сообщений
    data["Messages Today"] += 1

    data["Messages"].append(new_message)    # Добавляем новое сообщение в массив "Messages"

    with open(file_name, mode='w', encoding='utf-8') as file:    # Сохраняем обновленные данные обратно в файл
        json.dump(data, file, ensure_ascii=False, indent=4)
        
        

def get_msg_count(chat_id): #получтиь количетсво сообщений от пользователя за сегодня (возвоащает или кол-во или 0, если пользователь не зарегестрирован)

    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла

    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  #, загружаем существующие данные
            data = json.load(file)
        today_date = datetime.now().strftime('%Y-%m-%d')    # Проверка даты последнего сообщения и обнуление счётчика, если день изменился
        if data.get("Last Update Date") != today_date:
            data["Messages Today"] = 0  # Сброс счётчика
            data["Last Update Date"] = today_date  # Обновляем дату
    else:
        return 0     # Если файл не существует, отдаём 0
        
    msgs_count = data.get("Messages Today")

    with open(file_name, mode='w', encoding='utf-8') as file:    # Сохраняем обновленные(или нет) данные обратно в файл
        json.dump(data, file, ensure_ascii=False, indent=4)
        
    return msgs_count
    
    
    

def get_last_messages(chat_id): #извлечение последних count сообщений из chat_id
    
    count = chatconf.latest_posts    #сколько сообщений из чата вытаскивать
    
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
     
     
def spam_flag(chat_id, variable=None): # флаг спам-рассылки (если второй аргумент не передан - возвращает факт состояние ,если передан - меняет состояние на переданный )

    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла

    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  #, загружаем существующие данные
            data = json.load(file)
        
        if variable is not None:
            
            data["Spam Flag"] = variable  # присвоить состояние флага (если что то передали функции)            
            with open(file_name, mode='w', encoding='utf-8') as file:    # Сохраняем обновленные данные обратно в файл
                json.dump(data, file, ensure_ascii=False, indent=4)
            
        else:
            state = data["Spam Flag"]
            return state
        
        

# chat_id = 678035955
# spam_flag(chat_id, 1)
# print(spam_flag(chat_id))
# spam_flag(chat_id, 0)
# print(spam_flag(chat_id))


# # Пример вызова функции
# chat_id = 6780359955
# count = 100  # Количество последних сообщений, которые нужно получить
# print(get_last_messages(chat_id))
# print(get_msg_count(chat_id))


# contacts_key_words = ['коллекцию', 'контакты', 'Неожиданный']

# def is_part_in_list(strCheck):
#     arr = contacts_key_words
#     for i in range(len(arr)):
#         if strCheck.find(arr[i]) != -1:
#             return True
#     return False

# test_msg = get_last_messages(7080566621)


# if (is_part_in_list(test_msg[-1]['content'])):      #если есть слова из списка 
#     print('В')
#     print(test_msg[-1]['content'])
#     print('ЕСТЬ СЛОВО ИЗ')
#     print(contacts_key_words)
# else:
#     print('В')
#     print(test_msg[-1]['content'])
#     print('НЕТ СЛОВА ИЗ')
#     print(contacts_key_words)



