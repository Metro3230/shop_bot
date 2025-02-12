import json
import os
from datetime import datetime
from pathlib import Path
import shutil
# from config import chatconf
import configparser
import sqlite3

import time


script_dir = Path(__file__).parent  # Определяем путь к текущему скрипту
data_dir = script_dir / 'data'
msg_hist_dir = script_dir / 'data/msg_hits'   #папка с историями сообщений
msg_arch_dir = msg_hist_dir / 'archive'    #папка с историями удалившихся пользователей
config_file = data_dir / 'config.ini'
user_db = data_dir / 'users.db'

config = configparser.ConfigParser()  # настраиваем и читаем файл конфига
config.read(config_file)

# Подключение к базе данных (или создание, если её нет)
conn = sqlite3.connect(user_db)
cursor = conn.cursor()

# Создание таблиц
cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
    UserID INTEGER PRIMARY KEY,
    SenderName TEXT,
    UserName TEXT,
    MessagesToday INTEGER,
    LastUpdate_at TEXT DEFAULT CURRENT_TIMESTAMP,
    Exited INTEGER,
    Banned INTEGER
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Admins ( 
    UserID INTEGER PRIMARY KEY,
    SpamFlag INTEGER,
    NoRoleQFlag INTEGER,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Messages (
    MsgID INTEGER PRIMARY KEY,
    UserID INTEGER,
    Role TEXT,
    Text TEXT,
    Sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
    Del INTEGER,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
)
''')

conn.commit()
if conn:
    conn.close()



def add_user(user_id, sender_name=None, user_name=None):    #---------- Добавление нового пользователя ----------
    '''
    Функция добавления нового пользователя
    '''
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(user_db)
    cursor = conn.cursor()
    
    # Проверяем, существует ли пользователь в таблице Admins
    cursor.execute('SELECT UserID FROM Users WHERE UserID = ?', (user_id,))
    if cursor.fetchone():
        conn.close()
        return
    
    # Значения по умолчанию
    messages_today = 0
    exit = 0
    banned = 0  # По умолчанию пользователь не забанен
    
    # Вставляем нового пользователя в таблицу Users
    cursor.execute('''
    INSERT INTO Users (UserID, SenderName, UserName, Exited, MessagesToday, Banned)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, sender_name, user_name, exit, messages_today, banned))
    
    # Сохраняем изменения и закрываем соединение
    conn.commit()
    if conn:
        conn.close()



def make_admin(user_id):    #---------- Сделать пользователя администратором ----------
    '''
    Функция создания администратора
    '''
    
    conn = sqlite3.connect(user_db)
    cursor = conn.cursor()
    
    # Проверяем, существует ли пользователь в таблице Admins
    cursor.execute('SELECT UserID FROM Admins WHERE UserID = ?', (user_id,))
    if cursor.fetchone():
        conn.close()
        return
    
    # Значения по умолчанию для флагов
    spam_flag = 0
    no_role_q_flag = 0
    
    # Вставляем пользователя в таблицу Admins
    cursor.execute('''
    INSERT INTO Admins (UserID, SpamFlag, NoRoleQFlag)
    VALUES (?, ?, ?)
    ''', (user_id, spam_flag, no_role_q_flag))
    
    conn.commit()
    if conn:
        conn.close()



def remove_admin(user_id):    #---------- Удалить администратора ----------
    '''
    Функция удаления администратора
    '''
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(user_db)
    cursor = conn.cursor()
    
    # Удаляем администратора из таблицы Admins
    cursor.execute('DELETE FROM Admins WHERE UserID = ?', (user_id,))
        
    # Сохраняем изменения и закрываем соединение
    conn.commit()
    if conn:
        conn.close()


def is_admin(user_id):    #---------- Проверить, является ли пользователь администратором ----------
    '''
    Функция проверки, является ли пользователь администратором
    '''
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(user_db)
    cursor = conn.cursor()
    
    # Проверяем, есть ли пользователь в таблице Admins
    cursor.execute('SELECT UserID FROM Admins WHERE UserID = ?', (user_id,))
    result = cursor.fetchone()
    
    if conn:
        conn.close()
    
    # Если результат есть, возвращаем True, иначе False
    return result is not None



def get_admins():    #---------- Функция возврата всех администраторов ----------
    '''
    
    '''
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(user_db)
    cursor = conn.cursor()
    
    # Выполняем запрос для получения всех администраторов
    cursor.execute('SELECT UserID FROM Admins')
    
    # Получаем все строки результата
    admins = cursor.fetchall()
    
    # Закрываем соединение
    if conn:
        conn.close()
    
    # Возвращаем список администраторов
    return [admin[0] for admin in admins]  # Преобразуем список кортежей в список UserID



def add_message(user_id, role, text, msg_id=None):    #---------- Функция добавления нового сообщения ---------- 
    '''
    Функция добавления нового сообщения
    '''
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(user_db)
    cursor = conn.cursor()
    
    delete = 0
    
    # Если MsgID не передан, используем автоинкремент        (не пользоваться в проде !!!!)
    if msg_id is None:
        cursor.execute('''
        INSERT INTO Messages (UserID, Role, Text, Del)
        VALUES (?, ?, ?, ?)
        ''', (user_id, role, text, delete))
    else:
        cursor.execute('''
        INSERT INTO Messages (MsgID, UserID, Role, Text, Del)
        VALUES (?, ?, ?, ?, ?)
        ''', (msg_id, user_id, role, text, delete))
    
    # Сохраняем изменения и закрываем соединение
    conn.commit()
    if conn:
        conn.close()



def get_last_messages(user_id, limit):    #---------- Функция получение последних limit пользователей ---------- 
    '''
    Функция получения последних limit пользователей
    '''
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(user_db)
    cursor = conn.cursor()

    # Выполняем SQL-запрос для получения последних сообщений пользователя, где Del = 0
    cursor.execute('''
        SELECT Role, Text 
        FROM Messages 
        WHERE UserID = ? AND Del = 0
        ORDER BY MsgID DESC 
        LIMIT ?
    ''', (user_id, limit))

    # Получаем все строки результата
    rows = cursor.fetchall()

    # Закрываем соединение с базой данных
    if conn:
        conn.close()

    # Форматируем результат в требуемый вид
    messages = [{'role': row[0], 'content': row[1]} for row in rows]

    return messages[::-1]



def delete_msgs_flag(user_id):    #---------- Функция "удаления" всех сообщений от пользователя ---------- 
    """
    Функция "удаления" всех сообщений от пользователя.
    Устанавливает флаг Del в 1 для всех сообщений определенного пользователя.

    :param db_path: Путь к базе данных SQLite3
    :param user_id: ID пользователя, сообщения которого нужно пометить как удаленные
    """
    # Подключаемся к базе данных
    conn = sqlite3.connect(user_db)
    cursor = conn.cursor()

    # Обновляем флаг Del для всех сообщений пользователя
    cursor.execute('''
        UPDATE Messages
        SET Del = 1
        WHERE UserID = ?
    ''', (user_id,))

    # Сохраняем изменения
    conn.commit()
    if conn:
        conn.close()















# Тесты функций работы с БД:

# add_user("1", "Test User 1", "testuser")
# add_user("2", "Test User 2", "testuser")
# add_user("3", "Test User 3", "testuser")
# add_user("4", "Test User 4", "testuser")
# add_user("5", "Test User 5", "testuser")
# add_user("6", "Test User 6", "testuser")
# add_user("7", "Test User 7", "testuser")
# add_user("8", "Test User 8", "testuser")
# add_user("9", "Test User 9", "testuser")
# add_user("10", "Test User 10", "testuser")

# make_admin("1")
# make_admin("2")
# make_admin("3")

# print(is_admin("2"))

# remove_admin("2")

# print(is_admin("2"))

# print(get_admins())

#  добавление сообщений
user_id = 2
add_message(user_id, "assistant", "Hello, world!") 
time.sleep(1) 
add_message(user_id, "user", "Hi there!")  
time.sleep(1) 
add_message(user_id, "assistant", "Hello 2, world!") 
time.sleep(1) 
add_message(user_id, "user", "Hi 2 there!")  
time.sleep(1) 
add_message(user_id, "assistant", "Hello 3,  world!") 
time.sleep(1) 
add_message(user_id, "user", "Hi 3 there!")  
time.sleep(1) 
add_message(user_id, "assistant", "Hello 4, world!") 
time.sleep(1) 
add_message(user_id, "user", "Hi 4 there!")  
time.sleep(1) 
add_message(user_id, "assistant", "one", "2345") 
add_message(user_id, "user", "two", "45674")  

# # получение сообщений 
# user_id = 2
# limit = 20
# last_messages = get_last_messages(user_id, limit)
# for message in last_messages:
#     print(message)

# delete_msgs_flag(2)
