import chat_processing as chat
import openAI_req as openAI
from pathlib import Path
from dotenv import load_dotenv
import os
import telebot
from telebot import types
from telebot import types
from config import mainconf
import telegramify_markdown #библитека преобразования markdown в телеграммный markdown_n2
import shutil
from datetime import datetime
import logging

script_dir = Path(__file__).parent  # Определяем путь к текущему скрипту
data_dir = script_dir / 'data'
msg_hist_dir = data_dir / 'msg_hits'   #папка с историями сообщений
msg_arch_dir = msg_hist_dir / 'archive'
log_file = data_dir / 'log.log'
env_file = data_dir / '.env'
data_zip = script_dir / 'data.zip'

load_dotenv(env_file)
tg_token = os.getenv('TG_TOKEN')    # читаем token ai c .env

bot = telebot.TeleBot(tg_token)

logging.basicConfig(level=logging.INFO, filename=log_file, format='%(asctime)s - %(levelname)s - %(message)s')

#-------------------------------------\/-сервисные команды-\/-----------------------------------------

def remove_limit(chat_id, message): #---обнуление лимитов-------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль, и новый токен
            bot.send_message(chat_id, "Ошибка: формат команды /remove_limit <пароль>")
            return
        
        input_password = command_parts[1]

        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность сервисного пароля
            chat.remove_limit(chat_id)   #вызываем чистку лимита для чата
            bot.send_message(chat_id, "Дневной лимит для тебя сброшен")
        else:
            bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        logging.error(f"Ошибка обнуления лимитов - {e}")
    
    
def question(chat_id, message): #---вопрос ИИ без роли-------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль, и новый токен
            bot.send_message(chat_id, "Ошибка: формат команды /q <пароль> вопрос")
            return
        
        input_password = command_parts[1]
        text = command_parts[2]

        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность сервисного пароля
            response = openAI.req_to_ai_norole(text)   #отправляем историю чата (чат ид) боту
            response_text = response.choices[0].message.content         #парсим текст ответа
            response_text = telegramify_markdown.markdownify(response_text)      # чистим markdown
            bot.send_message(chat_id, response_text, parse_mode='MarkdownV2')
            bot.send_message(chat_id, 'обрати внимание, в вопросах через /q ИИ не знает контекст переписки, и каждый вопрос для него как новый')            
        else:
            bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        logging.error(f"Ошибка вопроса ИИ без роли - {e}")


def handle_dw_data(chat_id, message): #---скачивание данных--------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль
            bot.send_message(chat_id, "Ошибка: формат команды /dw_data <пароль>")
            return
        
        input_password = command_parts[1]

        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность пароля
            shutil.make_archive(str(data_zip).replace('.zip', ''), 'zip', data_dir)
            with open(data_zip, 'rb') as file:
                bot.send_document(chat_id, file)
            os.remove(data_zip)
            # logging.info('data скачен пользователем ' + str(chat_id))
        else:
            bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка: {e}")
        logging.error(f"Ошибка скачивания данных - {e}")
#----------------------------------------------------------------------------------------------------------


#----------------------------------------------\/-СПАМ-\/---------------------------------------------------
        
def new_spam(chat_id, message): #---создание СПАМ рассылки ------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль, и новый токен
            bot.send_message(chat_id, "Ошибка: формат команды /spam <пароль>")
            return
        
        input_password = command_parts[1]
              
        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность сервисного пароля
            bot.send_message(chat_id, 'Следующим сообщением отпарвь то, что хочешь отправить всем пользователям БОТа\.\n' +
                                            '_· к сообщению может быть прикреплена ссылка, картинка, документ, 1 геопозиция \(без описания\)_\n' +
                                            '_· не прекрепляй более одной картинки_\n' +
                                            '_· опросы и виктарины не поддерживаются_\n', parse_mode='MarkdownV2')
            chat.spam_flag(chat_id, 1)    #присваиваем флагу ожидания сообщения со спам рассылкой статус 1 для этого пользователя
        else:
            bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        logging.error(f"Ошибка создания СПАМ рассылки - {e}")


def spam_processing(chat_id, message_id, message_text): #--обработка СПАМ рассылки-------------+
    try:
        if (message_text == "ДA"):
            bot.send_message(chat_id, "Идёт рассылка...\nничего не отправляйте в чат", reply_markup=types.ReplyKeyboardRemove())
            actual_users = get_actual_ids() #получаем список актуальных пользователей
            luck_sends = sent_spam(actual_users, chat_id, message_id-2) #рассылаем, копируя пред-предыдущее сообщение
            bot.send_message(chat_id, f"Отправлено {luck_sends} пользователям.\n")
            chat.spam_flag(chat_id, 0)   #опускание флага
            
        elif (message_text == "ОТMЕHА"):   
            bot.send_message(chat_id,"Рассылка отменена",reply_markup=types.ReplyKeyboardRemove())
            chat.spam_flag(chat_id, 0)   #опускание флага

        else:
            bot.copy_message(   #отправка сообщения на проверку самому себе
                chat_id=chat_id,  # Кому отправляем
                from_chat_id=chat_id,  # Откуда берем сообщение
                message_id=message_id  # ID сообщения для копирования
            )
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)    # Создаем объект клавиатуры
            markup_1 = types.KeyboardButton("ДA")     # Добавляем кнопки
            markup_2 = types.KeyboardButton("ОТMЕHА")
            keyboard.row(markup_1, markup_2)   
            bot.send_message(chat_id, "⬆ Так будет выглядеть рассылка в чатах пользователей.\n" +
                                            "Начать рассылку?", reply_markup=keyboard)       # Отправляем сообщение с клавиатурой
    except Exception as e:
        logging.error(f"Ошибка обработки СПАМ рассылки - {e}")



def get_actual_ids(): #---Получение списка пользователей в виде массива-----------------------+
    try:
        json_filenames = []

        for filename in os.listdir(msg_hist_dir):    # Перебираем все файлы в папке
            if filename.endswith('.json'):        # Проверяем, имеет ли файл расширение .json
                json_filenames.append(os.path.splitext(filename)[0])            # Добавляем имя файла без расширения в массив

        return json_filenames
    except Exception as e:
        logging.error(f"Ошибка получения списка пользователей - {e}")



def arch_chat(chat_id):#---Архивирование чата chat_id------------------------------------------+
    
    try:
        source_path = msg_hist_dir / f'{chat_id}.json'
        
        if not os.path.exists(source_path):    # Проверяем, существует ли исходный чат
            print(f"Файл {source_path} не найден.")
            return

        if not os.path.exists(msg_arch_dir):    # Проверяем, существует ли папка назначения, и создаем её, если нужно
            os.makedirs(msg_arch_dir)

        filename = os.path.basename(source_path)    # Получаем имя файла и расширение
        name, ext = os.path.splitext(filename)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")    # Генерируем текущую дату и время в формате YYYY-MM-DD_HH-MM-SS

        new_filename = f"{timestamp}_{name}{ext}"    # Создаем новое имя файла
        destination_path = os.path.join(msg_arch_dir, new_filename)

        shutil.move(source_path, destination_path)    # Перемещаем файл
        
    except Exception as e:
        logging.error(f"Ошибка архивирования чата chat_id - {e}")


def sent_spam(users, chat_id, message_id):#---рассылка спама (users кому слать (массив), chat_id из какого чата, message_id ид сообщения)---+
    try:
        luck_sends = 0 #счётчик удачных отпрвлений
        bad_sends = 0 #счётчик не удачных отпрвлений
        
        for item in users:
            try:
                bot.copy_message(   
                    chat_id=item,  # Кому отправляем
                    from_chat_id=chat_id,  # Откуда берем сообщение
                    message_id=message_id  # ID сообщения для копирования
                )            
                luck_sends += 1
            except:
                arch_chat(item)  #если не удалось отправить, значит пользователь удалил и остановил бота, отправляем его в архив

        return luck_sends
    except Exception as e:
        logging.error(f"Ошибка рассылки спама - {e}")

#----------------------------------------------------------------------------------------------------------


# -----------------------------------Основной обработчик всех сообщений------------------------------------

@bot.message_handler(content_types=['text', 'photo', 'document', 'video', 'voice', 
                                    'audio', 'contact', 'location', 'sticker', 'animation'])
def handle_message(message):
    
    content_type = message.content_type
    message_text = message.text if message.text is not None else message.caption #текст или описание = текст
    chat_id = message.chat.id
    username = message.from_user.username
    message_id = message.message_id
    caption=message.caption
    spam_flag = chat.spam_flag(chat_id)
    
    if (message_text):    
        if message_text.startswith('/'): #обработка сервисных команд----+-+
            if message_text == "/start":
                bot.send_message(chat_id, mainconf.start_message)
                
            elif message_text == "/service":
                bot.send_message(chat_id, '`\/remove\_limit ` \- обнулить лимит на сегодня\n' +
                                                '`\/dw\_data` \- скачать папку с данными\n' +
                                                '`\/q` \- задать вопрос Chat\-GPT \(без роли\)\, например для помощи в составлении текста рассылки \(не поддерживает историю\)\n' +
                                                '`\/spam ` \- рассылка всем пользователям бота', parse_mode='MarkdownV2')
                
            elif message_text.startswith('/remove_limit'): 
                remove_limit(chat_id, message_text)
                
            elif message_text.startswith('/dw_data'):
                handle_dw_data(chat_id, message_text)
                
            elif message_text.startswith('/spam'):
                new_spam(chat_id, message_text)         
                       
            elif message_text.startswith('/q'):
                question(chat_id, message_text)
            
        else:                            #обработка обычного текста (не комманд)
            if chat.spam_flag(chat_id):         #если у пользователя поднят флаг ожидания спам сообщения
                spam_processing(chat_id, message_id, message_text)
                
            elif chat.get_msg_count(chat_id) > mainconf.msgs_limit: #если лимит пользователя на сегодня исчерпан
                keyboard = types.InlineKeyboardMarkup()
                url_button = types.InlineKeyboardButton(text='👀', url=mainconf.contacts)
                keyboard.add(url_button)
                bot.send_message(chat_id, mainconf.limit_msg, reply_markup=keyboard)                  # Отправка сообщение с ссылкой
                
            else:
                chat.save_message_to_json(chat_id, "user", username, message_text)   #записываем текст сообщения от ЮЗЕРА в историю сообщений
                last_messages = chat.get_last_messages(chat_id)
                response = openAI.req_to_ai(last_messages)   #отправляем историю чата (чат ид) боту
                response_text = response.choices[0].message.content         #парсим текст ответа
                # response_text = openAI.req_to_ai_TEST(chat.get_last_messages(chat_id))   #ТЕСТОВЫЙ ОТВЕТ БЕЗ ТРАТЫ ТОКЕНОВ
                response_text = telegramify_markdown.markdownify(response_text)      # чистим markdown
                chat.save_message_to_json(chat_id, "assistant", username, response_text)      #записываем текст сообщения от БОТА в историю сообщений
                bot.send_message(chat_id, response_text, parse_mode='MarkdownV2')     #отправляем ответ
           


# # Универсальный обработчик сообщений
# @bot.message_handler(content_types=['text', 'photo', 'document', 'video', 'voice', 
#                                     'audio', 'contact', 'location', 'sticker', 'animation'])
# def handle_message(message):
    
#     print(message.content_type)
    
#     message_text = message.text if message.text is not None else message.caption
#     chat_id = message.chat.id
#     username = message.from_user.username
#     message_id = message.message_id
    
#     print(message_text)
#     print(chat_id)
#     print(username)
#     print(message_id)
    


#     # bot.copy_message(   #отправка сообщения на проверку самому себе
#     #     chat_id=message.chat.id,  # Кому отправляем
#     #     from_chat_id=message.chat.id,  # Откуда берем сообщение
#     #     message_id=message.message_id  # ID сообщения для копирования
#     # )
    
    
#     keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)    # Создаем объект клавиатуры
#     button_1 = types.KeyboardButton("Подписаться")     # Добавляем кнопки
#     button_2 = types.KeyboardButton("Отписаться")
#     keyboard.row(button_1, button_2)
#     bot.send_message(chat_id, "test", reply_markup=keyboard)       # Отправляем сообщение с клавиатурой
        
        

#----------------------------------------------------------------------------------------

# Запуск бота
def main():
    bot.polling()
    time.sleep(3)
    

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())










# chat_id = 1234562789

# print(openAI.req_to_ai(chat.get_last_messages(chat_id)))














# ПЛАН - 
#  доделать рассылку
#  переносить чаты в архив ,если не удалось сделать на них рассылку
#  вопрос чату без его роли
# статистика (кол-во пользователей, кол-во сообщений всего , кол-во сообщений сегодня...)
#  ???
# Профит
