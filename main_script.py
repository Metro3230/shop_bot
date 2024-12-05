import chat_processing as chat
import openAI_req as openAI
from pathlib import Path
from dotenv import load_dotenv
import os
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import telegramify_markdown #библитека преобразования markdown в телеграммный markdown_n2
from datetime import datetime
import logging
import asyncio
import shutil
import configparser

script_dir = Path(__file__).parent  # Определяем путь к текущему скрипту
data_dir = script_dir / 'data'
msg_hist_dir = data_dir / 'msg_hits'   #папка с историями сообщений
log_file = data_dir / 'log.log'
env_file = data_dir / '.env'
data_zip = script_dir / 'data.zip'
config_file = data_dir / 'config.ini'

config = configparser.ConfigParser()  # настраиваем и читаем файл конфига
config.read(config_file)

load_dotenv(env_file)
tg_token = os.getenv('TG_TOKEN')    # читаем token ai c .env

bot = AsyncTeleBot(tg_token)
# async_bot = AsyncTeleBot(tg_token)


#  логгер для моего скрипта
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  #  уровень логов для моего скрипта

#  обработчик для записи в файл
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)  # Уровень для файлового обработчика
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

#  логгер для сторонних библиотек
logging.getLogger().setLevel(logging.WARNING)

temp_spam_text = None

    
#-------------------------------------\/-сервисные команды-\/----------------------------------------------------

async def remove_limit(chat_id, message): #---обнуление лимитов-----------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль, и новый токен
            await bot.send_message(chat_id, "Ошибка: формат команды /remove_limit пароль")
            return
        
        input_password = command_parts[1]

        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность сервисного пароля
            chat.remove_limit(chat_id)   #вызываем чистку лимита для чата
            await bot.send_message(chat_id, "Дневной лимит для тебя сброшен")
        else:
            await bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        logger.error(f"Ошибка обнуления лимитов - {e}")
    
    
async def simple_question(chat_id, message): #---вопрос к ИИ без роли---------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль, и новый токен
            await bot.send_message(chat_id, "Формат команды: \"/q пароль вопрос\"\n" +
                                      "Обрати внимание, что это обычный запрос к модели CHAT-GPT4o без каких либо " +
                                      "предписаний поведения и знания контекста ранней переписки и предыдущих вопросов. " +
                                      "Формулируй вопрос развёрнуто, описывая контекст и поведение вручную, если это требуется. ")
            return
        
        input_password = command_parts[1]
        text = command_parts[2]

        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность сервисного пароля
            response = await openAI.req_to_ai_norole(text)   #отправляем историю чата (чат ид) боту
            response_text = response.choices[0].message.content         #парсим текст ответа
            response_text = telegramify_markdown.markdownify(response_text)      # чистим markdown
            await bot.send_message(chat_id, response_text, parse_mode='MarkdownV2')
            await bot.send_message(chat_id, 'обрати внимание, в вопросах через /q ИИ не знает контекст переписки, и каждый вопрос для него как новый')            
        else:
            await bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        logger.error(f"Ошибка вопроса ИИ без роли - {e}")


async def handle_dw_data(chat_id, message): #---скачивание данных-------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль
            await bot.send_message(chat_id, "Ошибка: формат команды /dw_data пароль")
            return
        
        input_password = command_parts[1]

        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность пароля
            shutil.make_archive(str(data_zip).replace('.zip', ''), 'zip', data_dir)
            with open(data_zip, 'rb') as file:
                await bot.send_document(chat_id, file)
            os.remove(data_zip)
            logger.info('data скачен пользователем ' + str(chat_id))
        else:
            await bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}")
        logger.error(f"Ошибка скачивания данных - {e}")
        

async def handle_dw_config(chat_id, message): #---скачивание конфига-------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль
            await bot.send_message(chat_id, "Ошибка: формат команды /dw_config пароль")
            return
        
        input_password = command_parts[1]

        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность пароля
            with open(config_file, 'rb') as file:
                await bot.send_document(chat_id, file)
            await bot.send_message(chat_id, 'Измени файл и закинь обратно в этот чат с командой `/set_config пароль` в подписи к отправляемому файлу', parse_mode='MarkdownV2')
            logger.info('config скачен пользователем ' + str(chat_id))
        else:
            await bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}")
        logger.error(f"Ошибка скачивания данных - {e}")
        

async def handle_set_config(chat_id, message, file_id, file_name): #---обновление конфига-------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль
            await bot.send_message(chat_id, "Ошибка: формат команды /set_config пароль")
            return
        
        input_password = command_parts[1]

        if input_password == os.getenv('SERVICE_PASS') and file_name == 'config.ini':        # Проверяем правильность пароля
            file_path = (await bot.get_file(file_id)).file_path
            downloaded_file = await bot.download_file(file_path)
            with open(config_file, 'wb') as new_file:            # Сохраняем файл на сервере, заменяя старый
                new_file.write(downloaded_file)
            await bot.send_message(chat_id, "Файл настроек успешно обновлён, надеюсь он адекватный и Вы ничего не сломали")
            logger.info('config.ini заменён пользователем ' + str(chat_id))
        else:
            await bot.send_message(chat_id, "Либо файл называется не *config\.ini*\, либо пароль не верен\. Используй `/set_config пароль` как описание при отправке файла *config\.ini*", parse_mode='MarkdownV2')

    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}")
        logger.error(f"Ошибка скачивания данных - {e}")
        
        

async def handle_new_service_pass(chat_id, message): #----------обновление сервисного пароля--------------+
    try:
        old_service_pass = os.getenv('SERVICE_PASS')       # пишем в лог старый файл на всякий
        logger.info('попытка смены сервисного пароля: "' + old_service_pass + '" на новый...')

        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 3:         # Проверяем, что есть и пароль, и новый токен
            await bot.send_message(chat_id, "Ошибка: формат команды /new_service_pass сервисный_пароль новый_сервисный_пароль")
            return
        
        input_password = command_parts[1]
        new_service_pass = command_parts[2]

        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность старого сервисного пароля
            update_env_variable('SERVICE_PASS', new_service_pass)
            await bot.send_message(chat_id, "Сервисный пароль успешно обновлён!")
            logger.info('новый сервсиный пароль установлен: ' + new_service_pass)
        elif input_password == os.getenv('FOLLOW_PASS'):  #если это пароль на подписку
            await bot.send_message(chat_id, "Это пароль на подписку. Так не прокатит.")
            logger.info('Сервисный пароль не обновлён пользователем ' + str(chat_id) + '(ввёл пароль на подписку)')
        else:
            await bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        logger.error(f"Произошла ошибка обновления сервисного пароля - {e}")
        await bot.send_message(chat_id, f"Произошла ошибка: {e}")



def update_env_variable(key, value): #---функция обновления параметра в файле secrets.env-----------+

    if os.path.exists(env_file):    # Считаем текущие данные из .env файла
        with open(env_file, 'r') as file:
            lines = file.readlines()
    else:
        lines = []

    key_found = False    # Флаг, чтобы понять, был ли ключ найден
    new_lines = []

    for line in lines:    # Проходим по каждой строке и ищем ключ
        if line.startswith(f'{key}='):        # Если строка начинается с нужного ключа, заменяем его
            new_lines.append(f'{key}={value}\n')
            key_found = True
        else:
            new_lines.append(line)

    if not key_found:    # Если ключ не найден, добавляем его в конец
        new_lines.append(f'{key}={value}\n')

    with open(env_file, 'w') as file:    # Записываем обновленные данные обратно в .env файл
        file.writelines(new_lines)
    
    load_dotenv(env_file, override=True)    # повторно загружаем значения из env с перезаписью


async def get_stat(chat_id, message): #---вывод статистики-------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль
            await bot.send_message(chat_id, "Ошибка: формат команды /stat пароль")
            return
        
        input_password = command_parts[1]

        active_users = chat.get_active_users()
        departed_users = chat.get_departed_users()
        


        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность пароля
            text = (f'Активных пользователей: {active_users}\n'+
                    f'Удаливших чат с ботом: {departed_users}')
            text = telegramify_markdown.markdownify(text)      # чистим markdown
            await bot.send_message(chat_id, text, parse_mode='MarkdownV2')                  # Отправка сообщение с ссылкой
        else:
            await bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}")
        logger.error(f"Ошибка скачивания данных - {e}")
        
#----------------------------------------------------------------------------------------------------------


#----------------------------------------------\/-СПАМ-\/---------------------------------------------------
        
async def new_spam(chat_id, message): #---создание СПАМ рассылки ------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль, и новый токен
            await bot.send_message(chat_id, "Ошибка: формат команды /spam пароль")
            return
        
        input_password = command_parts[1]
              
        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность сервисного пароля
            text = ('*Следующим сообщением отпарвь то, что хочешь отправить всем пользователям БОТа*\n' +
                    '* к сообщению может быть прикреплена ссылка, 1 картинка, 1 документ\n' +
                    '* можно использовать форматирование\n' +
                    '* опросы и виктарины *не* поддерживаются\n')
            text = telegramify_markdown.markdownify(text)      # чистим markdown
            await bot.send_message(chat_id, text, parse_mode='MarkdownV2')
            chat.spam_flag(chat_id, 1)    #присваиваем флагу ожидания сообщения со спам рассылкой статус 1 для этого пользователя
        else:
            await bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        logger.error(f"Ошибка создания СПАМ рассылки - {e}")


async def spam_processing(chat_id, message_id, message_text): #--обработка СПАМ рассылки-------------+
    global temp_spam_text
    try:
        if (message_text == "ДA"):
            await bot.send_message(chat_id, "Идёт рассылка...\nничего не отправляйте в чат", reply_markup=types.ReplyKeyboardRemove())
            actual_users = chat.get_actual_ids() #получаем список актуальных пользователей
            await sent_spam(actual_users, chat_id, message_id-2) #рассылаем, копируя пред-предыдущее сообщение
            temp_spam_text = None   # удаляем временный текст рассылки
            chat.spam_flag(chat_id, 0)   #опускание флага
            
        elif (message_text == "ОТMЕHА"):   
            await bot.send_message(chat_id,"Рассылка отменена",reply_markup=types.ReplyKeyboardRemove())
            temp_spam_text = None   # удаляем временный текст рассылки
            chat.spam_flag(chat_id, 0)   #опускание флага

        else:
            await bot.copy_message(   #отправка сообщения на проверку самому себе
                chat_id=chat_id,  # Кому отправляем
                from_chat_id=chat_id,  # Откуда берем сообщение
                message_id=message_id  # ID сообщения для копирования
            )
            temp_spam_text = message_text
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)    # Создаем объект клавиатуры
            markup_1 = types.KeyboardButton("ДA")     # Добавляем кнопки
            markup_2 = types.KeyboardButton("ОТMЕHА")
            keyboard.row(markup_1, markup_2)   
            await bot.send_message(chat_id, "⬆ Так будет выглядеть рассылка в чатах пользователей.\n" +
                                            "Начать рассылку? ", reply_markup=keyboard)       # Отправляем сообщение с клавиатурой
    except Exception as e:
        logger.error(f"Ошибка обработки СПАМ рассылки - {e}")


async def sent_spam(users, chat_id, message_id):#---рассылка спама (users кому слать (массив), chat_id из какого чата, message_id ид сообщения)---+
    try:
        luck_sends = 0 #счётчик удачных отпрвлений
        interval = 1 / config['mainconf']['requests_per_second']
        next_request_time = asyncio.get_event_loop().time()
        i = 0 
        
        while i < len(users):           # цикл по всем пользователям
            current_time = asyncio.get_event_loop().time()
            if current_time >= next_request_time:
                try:
                    await bot.copy_message(     # ---рассылаем ---
                        chat_id=users[i],  # Кому отправляем
                        from_chat_id=chat_id,  # Откуда берем сообщение
                        message_id=message_id  # ID сообщения для копирования
                    )
                    if temp_spam_text is not None:
                        chat.save_message_to_json(chat_id=users[i], role="assistant", message=temp_spam_text)      #и записываем рекламный текст от БОТА в историю сообщений каждого участника
                    luck_sends += 1
                except Exception as e: # в архив, если ошибка отправки от сервера тг = 400
                    if(e.error_code == 400):
                        try:
                            chat.arch_chat(users[i])  #если не удалось отправить, значит пользователь удалил и остановил бота, отправляем его в архив
                        except Exception as e:
                            logger.error(f"Ошибка добавления чата {users[i]} в архив - {e}")
                
                i += 1  # Переход к следующему получателю
                next_request_time += interval
            else:                                              # игнорим отправку, если слишком быстро отправляем
                await asyncio.sleep(next_request_time - current_time)
            
        await bot.send_message(chat_id, f"Отправлено {luck_sends} пользователям.\n")
        
    except Exception as e:
        logger.error(f"Ошибка рассылки спама - {e}")
        await bot.send_message(chat_id, f"Ошибка рассылки - {e}. Сообщите разработчику.")



#----------------------------------------------------------------------------------------------------------


#----------------------------------------стандартная обработка стандартного вопроса------------------------

async def question_for_ai(chat_id, username, message_text):
    try:
        chat.save_message_to_json(chat_id=chat_id, role="user", sender_name=username, message=message_text)   #записываем текст сообщения от ЮЗЕРА в историю сообщений
        last_messages = chat.get_last_messages(chat_id)
        response = await openAI.req_to_ai(last_messages)   #отправляем историю чата (чат ид) боту
        response_text = response.choices[0].message.content         #парсим текст ответа
        # response_text = openAI.req_to_ai_TEST(chat.get_last_messages(chat_id))   #ТЕСТОВЫЙ ОТВЕТ БЕЗ ТРАТЫ ТОКЕНОВ
        response_text = telegramify_markdown.markdownify(response_text)      # чистим markdown
        chat.save_message_to_json(chat_id=chat_id, role="assistant", sender_name=username, message=response_text)      #записываем текст сообщения от БОТА в историю сообщений
        await bot.send_message(chat_id, response_text, parse_mode='MarkdownV2', reply_markup=types.ReplyKeyboardRemove())     #отправляем ответ
    except Exception as e:
        logger.error(f"Ошибка стандартной обработки стандартного вопроса - {e}")

#----------------------------------------------------------------------------------------------------------


# -----------------------------------Основной обработчик всех сообщений------------------------------------

@bot.message_handler(content_types=['text', 'photo', 'document', 'video', 'voice', 'audio', 'contact', 'location', 'sticker', 'animation'])
async def handle_message(message):
    
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
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)    # Создаем объект клавиатуры
                markup_1 = types.KeyboardButton(config['mainconf']['btn_text_1'])     # Добавляем кнопки
                markup_2 = types.KeyboardButton(config['mainconf']['btn_text_2'])
                markup_3 = types.KeyboardButton(config['mainconf']['btn_text_3'])
                markup_4 = types.KeyboardButton(config['mainconf']['btn_text_4'])
                markup_5 = types.KeyboardButton(config['mainconf']['btn_text_5'])
                keyboard.row(markup_1, markup_2)
                keyboard.row(markup_3)
                keyboard.row(markup_4)
                keyboard.row(markup_5)
                await bot.send_message(chat_id, config['mainconf']['start_message'], reply_markup=keyboard)       # Отправляем сообщение с клавиатурой
                
            elif message_text == "/service" or message_text == "/admin":
                text = ('`/q` - задать вопрос Chat-GPT вне формата бота\n' +
                        '`/spam пароль` - рассылка всем пользователям бота\n\n' +
                        '`/dw_data пароль` - скачать папку с данными\n' +
                        '`/remove_limit пароль` - обнулить лимит на сегодня\n' +
                        '`/dw_config пароль` - скачать текущий файл настроек\n' +
                        '`/new_service_pass старый_пароль новый_пароль` - замена сервисного пароля\n')
                text = telegramify_markdown.markdownify(text)      # чистим markdown
                await bot.send_message(chat_id, text, parse_mode='MarkdownV2')
                
            elif message_text.startswith('/remove_limit'): 
                await remove_limit(chat_id, message_text)
                
            elif message_text.startswith('/dw_data'):
                await handle_dw_data(chat_id, message_text)
                
            elif message_text.startswith('/spam'):
                await new_spam(chat_id, message_text)         
                       
            elif message_text.startswith('/q'):
                await simple_question(chat_id, message_text)
                
            elif message_text.startswith('/new_service_pass'):
                await handle_new_service_pass(chat_id, message_text)
                
            elif message_text.startswith('/stat'):
                await get_stat(chat_id, message_text)
                
            elif message_text.startswith('/dw_config'):
                await handle_dw_config(chat_id, message_text)
                
            elif message_text.startswith('/set_config'):
                await handle_set_config(chat_id, message_text, message.document.file_id, message.document.file_name)
                


        else:                            #обработка обычного текста (не команд)
            
            if chat.spam_flag(chat_id):         #если у пользователя поднят флаг ожидания спам сообщения                
                await spam_processing(chat_id, message_id, message_text)                
                
            elif chat.get_msg_count(chat_id) > int(config['mainconf']['msgs_limit']): #если лимит пользователя на сегодня исчерпан
                keyboard = types.InlineKeyboardMarkup()
                url_button = types.InlineKeyboardButton(text='👀', url=config['mainconf']['contacts'])
                keyboard.add(url_button)
                await bot.send_message(chat_id, config['mainconf']['limit_msg'], reply_markup=keyboard)                  # Отправка сообщение с ссылкой
                
            else:
                await question_for_ai(chat_id, username, message_text)

       

#-------------------------------------------------------------------------------------------------------------



logger.info(f"Скрипт запущен")

# Запуск бота
async def main():
    await bot.polling()
    

if __name__ == "__main__":
    asyncio.run(main())







# ПЛАН - 
#  доделать рассылку  ok
#  переносить чаты в архив ,если не удалось сделать на них рассылку ok
#  вопрос чату без его роли  ok  
#  кнопки при приветствии
#  
# 
# 
#  биллинг токенов для каждого и суммарный
# статистика (кол-во пользователей, кол-во сообщений всего , кол-во сообщений сегодня...)  хз надо ли
# отправлять в архив после 2 неудачных попыток отправки
#  ???
# Профит
