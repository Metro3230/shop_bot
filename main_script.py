import chat_processing_db as chat_db
import export_msgs_to_html as msg_report
import openAI_req as openAI
from pathlib import Path
from dotenv import load_dotenv
import os
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import telegramify_markdown #библитека преобразования markdown в телеграммный markdown_n2
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
admins_file = data_dir / 'admins.txt'
config_file_name = 'config.ini'
config_file = data_dir / config_file_name
google_data_api = data_dir / 'google_data_api.json'
msg_report_file = data_dir / 'msg_report.html'

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


async def handle_dw_data(chat_id): #---скачивание данных-------------------------------------+
    try:
        shutil.make_archive(str(data_zip).replace('.zip', ''), 'zip', data_dir)
        with open(data_zip, 'rb') as file:
            await bot.send_document(chat_id, file)
        os.remove(data_zip)
        logger.info('data скачен пользователем ' + str(chat_id))

    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        logger.error(f"Ошибка скачивания данных - {e}")
        
        

async def handle_dw_config(chat_id,): #---скачивание конфига-------------------------------------+
    try:
        with open(config_file, 'rb') as file:
            await bot.send_document(chat_id, file)
        text = 'Аккуратно отредактируй файл и закинь обратно в этот чат (без подписи), не меняя названия'
        text = telegramify_markdown.markdownify(text)      # чистим markdown
        await bot.send_message(chat_id, text, parse_mode='MarkdownV2')
        logger.info('config скачен пользователем ' + str(chat_id))
            
    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        logger.error(f"Ошибка скачивания данных - {e}")
        
        
        
async def handle_dw_logs(chat_id,): #---скачивание логов-------------------------------------+
    try:
        with open(log_file, 'rb') as file:
            await bot.send_document(chat_id, file)
        logger.info('лог скачен пользователем ' + str(chat_id))
            
    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        logger.error(f"Ошибка скачивания логов - {e}")
        
        
        
async def handle_dw_messages(chat_id,): #---скачивание репорта по всем сообщениям-------------------------------------+
    try:
        msg_report.msg_to_html()
        with open(msg_report_file, 'rb') as file:
            await bot.send_document(chat_id, file)
        logger.info('выгрузка сообщзений скачена пользователем ' + str(chat_id))
            
    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        logger.error(f"Ошибка скачивания логов - {e}")
        


async def handle_set_config(chat_id, file_id): #---обновление конфига-------------------------------------+
    try:
        file_path = (await bot.get_file(file_id)).file_path
        downloaded_file = await bot.download_file(file_path)
        with open(config_file, 'wb') as new_file:            # Сохраняем файл на сервере, заменяя старый
            new_file.write(downloaded_file)
        config.read(config_file)
        
        await bot.send_message(chat_id, "Файл настроек успешно обновлён, надеюсь он адекватный и Вы ничего не сломали")
        logger.info(f'{config_file_name} заменён пользователем ' + str(chat_id))

    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        logger.error(f"Ошибка обновления конфига - {e}")
        
        
        
async def handle_new_admin_pass(chat_id, message): #----------обновление  пароля--------------+
    try:
        old_admin_pass = os.getenv('ADMIN_PASS')       # пишем в лог старый файл на всякий
        logger.info(f'попытка смены пароля: {old_admin_pass} на новый...')

        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 3:         # Проверяем, что есть и пароль, и новый токен
            await bot.send_message(chat_id, "Ошибка: формат команды /new_admin_pass текущий_пароль новый_пароль")
            return
        
        input_password = command_parts[1]
        new_admin_pass = command_parts[2]

        if input_password == os.getenv('ADMIN_PASS'):        # Проверяем правильность старого сервисного пароля
            update_env_variable('ADMIN_PASS', new_admin_pass)
            await bot.send_message(chat_id, "Пароль успешно обновлён!")
            logger.info('новый пароль установлен: ' + new_admin_pass)
        else:
            await bot.send_message(chat_id, "Неверный текущий пароль.")

    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        logger.error(chat_id, f"Произошла ошибка: {e}")
        
        
        
async def ban(chat_id, message): #----------забанить пользователя--------------+
    try:
        old_admin_pass = os.getenv('ADMIN_PASS')       # пишем в лог старый файл на всякий
        logger.info(f'попытка смены пароля: {old_admin_pass} на новый...')

        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 3:         # Проверяем, что есть и пароль, и новый токен
            await bot.send_message(chat_id, "Ошибка: формат команды `/ban id_или_юзернейм причина`")
            return
        
        id_or_username = command_parts[1]
        why = command_parts[2]
            
        result = chat_db.ban(id_or_username, why)       
                
        await bot.send_message(chat_id, result)

    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        logger.error(chat_id, f"Произошла ошибка: {e}")
        
        
        
async def unban(chat_id, message): #----------разбанить пользователя--------------+
    try:
        old_admin_pass = os.getenv('ADMIN_PASS')       # пишем в лог старый файл на всякий
        logger.info(f'попытка смены пароля: {old_admin_pass} на новый...')

        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль, и новый токен
            await bot.send_message(chat_id, "Ошибка: формат команды `/unban id_или_юзернейм`")
            return
        
        id_or_username = command_parts[1]
            
        result = chat_db.unban(id_or_username)       
                
        await bot.send_message(chat_id, result)

    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        logger.error(chat_id, f"Произошла ошибка: {e}")
    


async def get_stat(chat_id): #---вывод статистики-------------------------------------+
    try:
        active_users, today_users, departed_users, banned_users = chat_db.get_user_stat()
        all_msgs, today_msgs = chat_db.get_message_stat()
        text = f'''
        ---------------------------
        Статистика по пользователям:
        Активных пользователей: {active_users}
        Новых сегодня: {today_users}
        Удаливших чат с ботом: {departed_users}
        (обновляется с каждой рассылкой)
        Забаненых: {banned_users}
        ---------------------------
        Статистика по общению:
        Всего: {all_msgs}
        Сегодня: {today_msgs}
        '''
        text = telegramify_markdown.markdownify(text)      # чистим markdown
        await bot.send_message(chat_id, text, parse_mode='MarkdownV2')                  # Отправка 

    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        logger.error(f"Ошибка скачивания данных - {e}")



async def login(chat_id, message, msg_id): #---логин в админы-------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль
            await bot.send_message(chat_id, "Ошибка: формат команды /login пароль")
            return
        
        input_password = command_parts[1]
        
        if input_password == os.getenv('ADMIN_PASS'):        # Проверяем правильность пароля
            if chat_db.make_admin(chat_id): # коронует в админы (проверяя статус ответа)
                text = telegramify_markdown.markdownify("Вы стали администратором. /admin - администрирование бота.")
                await bot.send_message(str(chat_id), text, parse_mode='MarkdownV2')
                logging.info(str(chat_id) + ' залогинился в админы')
            else:
                text = telegramify_markdown.markdownify("Вы уже вдминистратор. /admin - администрирование бота.")
                await bot.send_message(str(chat_id), text, parse_mode='MarkdownV2')
            await bot.delete_message(chat_id, msg_id) #удаляем пароль из чата                 
        else:
            await bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        logger.error(f"Ошибка логина в админы - {e}")
        
        

async def unlogin(chat_id): #---разлогин из админов-(возвращает результат текстом)-----------------+
    try:        
        chat_db.remove_admin(chat_id)
        await bot.send_message(chat_id, "Вы разлогинились.")
        
    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        logger.error(f"Ошибка разлогина из админов - {e}")



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
        
#----------------------------------------------------------------------------------------------------------


#----------------------------------------------\/-СПАМ-\/---------------------------------------------------
        
async def new_spam(chat_id): #---создание СПАМ рассылки ------------------------------------+
    try:
        text = ('*Следующим сообщением отпарвь то, что хочешь отправить всем пользователям БОТа*\n' +
                '* к сообщению может быть прикреплена ссылка, 1 картинка, 1 документ\n' +
                '* можно использовать форматирование\n' +
                '* опросы и викторины *не* поддерживаются\n')
        text = telegramify_markdown.markdownify(text)      # чистим markdown
        await bot.send_message(chat_id, text, parse_mode='MarkdownV2')
        chat_db.flag(chat_id, "SpamFlag", 1)    #присваиваем флагу ожидания сообщения со спам рассылкой статус 1 для этого пользователя

    except Exception as e:
        chat_db.flag(chat_id, "SpamFlag", 0)   #опускание флага
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        logger.error(f"Ошибка создания СПАМ рассылки - {e}")


async def spam_processing(chat_id, message_id, message_text): #--обработка СПАМ рассылки-------------+
    global temp_spam_text
    try:
        if (message_text == "Отпрaвить всeм"):
            await bot.send_message(chat_id, "Идёт рассылка...\nничего не отправляйте в чат", reply_markup=types.ReplyKeyboardRemove())
            actual_users = chat_db.get_users() #получаем список актуальных пользователей
            await sent_spam(actual_users, chat_id, message_id-2) #рассылаем, копируя пред-предыдущее сообщение
            temp_spam_text = None   # удаляем временный текст рассылки
            chat_db.flag(chat_id, "SpamFlag", 0)   #опускание флага
            
        elif (message_text == "Oтменa"):   
            await bot.send_message(chat_id,"Рассылка отменена",reply_markup=types.ReplyKeyboardRemove())
            temp_spam_text = None   # удаляем временный текст рассылки
            chat_db.flag(chat_id, "SpamFlag", 0)   #опускание флага

        else:
            await bot.copy_message(   #отправка сообщения на проверку самому себе
                chat_id=chat_id,  # Кому отправляем
                from_chat_id=chat_id,  # Откуда берем сообщение
                message_id=message_id  # ID сообщения для копирования
            )
            temp_spam_text = message_text
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)    # Создаем объект клавиатуры
            markup_1 = types.KeyboardButton("Отпрaвить всeм")     # Добавляем кнопки
            markup_2 = types.KeyboardButton("Oтменa")
            keyboard.row(markup_1, markup_2)   
            await bot.send_message(chat_id, "⬆ Так будет выглядеть рассылка в чатах пользователей.\n" +
                                            "Если что-то не так, пришли новое сообщение. Если всё хорошо или передумал, воспользуйся кнопками ⬇", reply_markup=keyboard)       # Отправляем сообщение с клавиатурой
    except Exception as e:
        chat_db.flag(chat_id, "SpamFlag", 0)   #опускание флага
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        logger.error(f"Ошибка обработки СПАМ рассылки - {e}")


async def sent_spam(users, chat_id, message_id):#---рассылка спама (users кому слать (массив), chat_id из какого чата, message_id ид сообщения)---+
    try:
        luck_sends = 0 #счётчик удачных отпрвлений
        interval = 1 / int(config['mainconf']['requests_per_second'])
        next_request_time = asyncio.get_event_loop().time()
        i = 0 
        
        while i < len(users):           # цикл по всем пользователям
            current_time = asyncio.get_event_loop().time()
            if current_time >= next_request_time:
                try:
                    sent_message = await bot.copy_message(     # ---рассылаем ---
                        chat_id=users[i],  # Кому отправляем
                        from_chat_id=chat_id,  # Откуда берем сообщение
                        message_id=message_id  # ID сообщения для копирования
                    )
                    sent_message_id = sent_message.message_id
                    if temp_spam_text is not None:
                        chat_db.add_message(user_id=users[i], role="assistant", text=temp_spam_text, msg_id=sent_message_id)      #и записываем рекламный текст от БОТА в историю сообщений каждого участника
                    luck_sends += 1
                except Exception as e: # в архив, если ошибка отправки от сервера тг = 403 или 400 (отписался или неизвестен вообще)
                    if hasattr(e, 'error_code') and (e.error_code == 403 or e.error_code == 400):
                        try:
                            chat_db.flag(users[i], "Exited", 1) # выставляем параметр "вышел" в 1 
                        except Exception as e:
                            logger.error(f"Ошибка добавления чата {users[i]} в архив - {e}")
                    else: 
                        logger.error(f"Ошибка отправки рассылки {users[i]} - {e}")
                
                i += 1  # Переход к следующему получателю
                next_request_time += interval
            else:                                              # игнорим отправку, если слишком быстро отправляем
                await asyncio.sleep(next_request_time - current_time)
            
        await bot.send_message(chat_id, f"Отправлено {luck_sends} пользователям.\n")
        
    except Exception as e:
        chat_db.flag(chat_id, "SpamFlag", 0)   #опускание флага
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        await bot.send_message(chat_id, f"Ошибка рассылки - {e}. Сообщите разработчику.")



#----------------------------------------------------------------------------------------------------------


#---------------------------------------------обратботка вопроса ИИ без роли------------------------------

async def question_for_ai_norole(chat_id, message_text):
    try:        
        response = await openAI.req_to_ai_norole(message_text)   #задаем вопрос ИИ
        response_text = response.choices[0].message.content         #парсим текст ответа
        await send_msg(chat_id, response_text)
        await bot.send_message(chat_id, '-----=====-----\nОбрати внимание, в таких вопросах ИИ не знает контекст переписки, и каждый вопрос для него как новый. Что бы задать ещё один вопрос к ИИ напрямую, снова используй кнопку "задать вопрос вне формата бота"')   
        
        chat_db.flag(chat_id, "NoRoleQFlag", 0) # опускаем флаг  
            
    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        logger.error(f"Ошибка стандартной обработки стандартного вопроса - {e}")

#----------------------------------------------------------------------------------------------------------


#----------------------------------------стандартная обработка стандартного вопроса------------------------

async def question_for_ai(chat_id, message_text, receiv_message_id):
    wait_message_sent = False
    wait_message_id = None
    typing_task = None
    wait_message_task = None    
    try:
        
        # отправлчяем статус "набирает сообщение" каждые Х секунд
        async def send_typing_periodically(): 
            while True:
                try:
                    await bot.send_chat_action(chat_id, 'typing', timeout=10)
                    await asyncio.sleep(7)
                except Exception as e:
                    logger.error(f"send_chat_action не отправлен (для chat_id {chat_id}) -- {e}")
                    break
                                
        # задача для отправки успокаивающего сообщения через Х секунд после начала ожидания ответа от API ИИ
        async def send_wait_message():
            nonlocal wait_message_sent, wait_message_id
            await asyncio.sleep(int(config['mainconf']['a_calming_message_delay']))
            text = telegramify_markdown.markdownify(config['mainconf']['a_calming_message'])      # чистим markdown
            msg = await bot.send_message(chat_id, text, parse_mode='MarkdownV2', reply_markup=types.ReplyKeyboardRemove())
            wait_message_sent = True
            wait_message_id = msg.message_id

        # Запускаем задачи /\
        typing_task = asyncio.create_task(send_typing_periodically())
        wait_message_task = asyncio.create_task(send_wait_message())
                        
        chat_db.add_message(user_id=chat_id, role="user", text=message_text, msg_id=receiv_message_id)      #записываем текст сообщения от ЮЗЕРА в историю сообщений

        last_messages = chat_db.get_last_messages(chat_id, config['mainconf']['latest_posts'])    #получаем последние (на глубину контекста) сообщения переписки

        response = await openAI.req_to_ai(last_messages)   #отправляем историю чата (чат ид) боту
        response_text = response.choices[0].message.content         #парсим текст ответа
        
        # Отменяем задачу отправки сообщения "Нужно ещё подождать", если она еще не выполнена
        wait_message_task.cancel()
        try:
            await wait_message_task
        except asyncio.CancelledError:
            pass  # Ожидаем завершения задачи, игнорируем ошибку отмены
        
        sent_message_id = await send_msg(chat_id, response_text)    # отправляем, получая id сообщения        
        
        chat_db.add_message(user_id=chat_id, role="assistant", text=response_text, msg_id=sent_message_id)      #записываем текст сообщения от БОТА в историю сообщений 

    except Exception as e:
        text = telegramify_markdown.markdownify(config['mainconf']['msg_if_req_error'])      # чистим markdown
        await bot.send_message(chat_id, text, parse_mode='MarkdownV2', reply_markup=types.ReplyKeyboardRemove())
        logger.error(f"Ошибка при обработке запроса к ИИ от {chat_id} - {e}")
        
    finally:
        # Если сообщение "нужно подождать" было отправлено, удаляем его
        if wait_message_sent:
            try:
                await bot.delete_message(chat_id, wait_message_id)
            except Exception as e:
                logger.error(f"Не удалось удалить сообщение: {e}")

        # Останавливаем задачу отправки 'typing'
        if typing_task:
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass  # Ожидаем завершения задачи, игнорируем ошибку отмены

#----------------------------------------------------------------------------------------------------------

#------------------------------------------отправка сообщения (с проверкой на длину)-----------------------

async def send_msg(chat_id, message_text):
    try:
        message_text = telegramify_markdown.markdownify(message_text)      # чистим markdown
        max_msg_length = config['mainconf']['max_msg_length']
        text_lines = message_text.split('\n')
        current_message = ''
        for line in text_lines:
            if len(current_message) + len(line) + 1 > int(max_msg_length):
                sent_message = await bot.send_message(chat_id, current_message, parse_mode='MarkdownV2', reply_markup=types.ReplyKeyboardRemove())   
                sent_message_id = sent_message.message_id
                current_message = line
            else:
                if current_message:
                    current_message += '\n' + line
                else:
                    current_message = line
        if current_message:
            sent_message = await bot.send_message(chat_id, current_message, parse_mode='MarkdownV2', reply_markup=types.ReplyKeyboardRemove())   
            sent_message_id = sent_message.message_id
        return sent_message_id
    except Exception as e:
        await bot.send_message(chat_id, f"Ошибка - {e}")   
        logger.error(f"Ошибка стандартной обработки стандартного вопроса - {e}")
        
#----------------------------------------------------------------------------------------------------------

# -----------------------------------Основной обработчик всех сообщений------------------------------------

@bot.message_handler(content_types=['text', 'photo', 'document', 'video', 'voice', 'audio', 'contact', 'location', 'sticker', 'animation'])
async def handle_message(message):
    try:
        # content_type = message.content_type
        message_text = message.text if message.text is not None else message.caption #текст или описание = текст
        chat_id = message.chat.id
        username = message.from_user.username
        message_id = message.message_id         
           
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name        
        first_name = "" if first_name is None else first_name
        last_name = "" if last_name is None else last_name        
        sendername = first_name + " " + last_name
        # caption=message.caption
        

        if (message_text):
            if message_text == "/start":   #  === регистрация и приветствие ===
                chat_db.add_user(chat_id, sendername, username)  # добавляем нового пользователя                    
                start_mgs = telegramify_markdown.markdownify(config['mainconf']['start_message'])      # получаем стартовое сообщение ( и чистим markdown )  
                
                if int(config['mainconf']['show_buttons']): # если показывать кнопки
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
                    await bot.send_message(chat_id, start_mgs, reply_markup=keyboard, parse_mode='MarkdownV2')       # Отправляем сообщение с клавиатурой 
                
                else: # без кнопок
                    await bot.send_message(chat_id, start_mgs, parse_mode='MarkdownV2')       #  без клавиатуры
                    
                    
            elif not chat_db.is_user(chat_id): # === если пользователь не зарегестрирован ===
                mgs = telegramify_markdown.markdownify(config['mainconf']['msg_before_start'])      # получаем ДОстартовое сообщение ( и чистим markdown )  
                await bot.send_message(chat_id, mgs, parse_mode='MarkdownV2')       # Отправляем сообщение           
            
            
            elif chat_db.flag(chat_id, "Banned") and not chat_db.is_admin(chat_id) and not message_text.startswith('/login'):  # === если пользователь забанен (и не админ) ===
                chat_db.add_message(user_id=chat_id, role="user", text=message_text, msg_id=message_id)      #записываем текст в историю (хз зачем)            
                chat_db.delete_msgs_flag(chat_id)   # удалёнными            
                why_ban = chat_db.flag(chat_id, "WhyBan")
                await bot.send_message(chat_id, f"{config['mainconf']['if_banned']}\nПричина - {why_ban}.\nЕсли есть вопросы, свяжись с {config['mainconf']['admin_link']}")   
                            
                            
            elif message_text.startswith('/'): # === если это сервисная команда ===
                
                if message_text.startswith('/login'): # логин
                    await login(chat_id, message_text, message_id) 
                
                elif message_text.startswith('/restart'): # чистка контекста                    
                    start_mgs = telegramify_markdown.markdownify(config['mainconf']['restart_message'])
                    await bot.send_message(chat_id, start_mgs, parse_mode='MarkdownV2')   
                    chat_db.delete_msgs_flag(chat_id)                    
                        
                        
                elif chat_db.is_admin(chat_id): #если админ              
                    if message_text == "/dev":
                        text = ('-----------------для разработчиков-------------------\n' +
                                '/dw_data - скачать папку с данными\n' +
                                '/dw_messages - скачать выгрузку сообщений\n' +
                                '`/ban id_или_ник причина` - забанить пользователя\n' +
                                '`/unban id_или_ник` - разабанить пользователя\n' +
                                '/logs - посмотреть логи\n')          
                        text = telegramify_markdown.markdownify(text)      # чистим markdown
                        await bot.send_message(chat_id, text, parse_mode='MarkdownV2')    
                            
                    elif message_text == "/admin":
                        markup = types.InlineKeyboardMarkup()
                        but_spam = types.InlineKeyboardButton("создать рассылку", callback_data='call_btn_spam')  # Добавляем кнопки
                        but_norole_q = types.InlineKeyboardButton("задать вопрос ИИ вне формата бота", callback_data='call_btn_norole_q')
                        but_stat = types.InlineKeyboardButton("статистика", callback_data='call_btn_stat')    
                        but_service = types.InlineKeyboardButton("сервис", callback_data='call_btn_service')    
                        markup.row(but_spam)
                        markup.row(but_norole_q)
                        markup.row(but_stat, but_service)
                        await bot.send_message(chat_id, "Администрирование бота:", reply_markup=markup)       # Отправляем сообщение с клавиатурой
                                                                                                                        
                    elif message_text == "/dw_data":
                        await handle_dw_data(chat_id)
                        
                    elif message_text == "/dw_config":
                        await handle_dw_config(chat_id)
                        
                    elif message_text.startswith('/new_admin_pass'):
                        await handle_new_admin_pass(chat_id, message_text)
                        
                    elif message_text == "/unlogin":
                        await unlogin(chat_id) 
                        
                    elif message_text == "/logs":
                        await handle_dw_logs(chat_id) 
                        
                    elif message_text == "/dw_messages":
                        await handle_dw_messages(chat_id) 
                        
                    elif message_text.startswith('/ban'):
                        await ban(chat_id, message_text) 
                        
                    elif message_text.startswith('/unban'):
                        await unban(chat_id, message_text) 
                        
                    # elif message_text == "/start_spam_games":
                    #     await games_spam() 
                    
                else:  #если не админ
                    text = telegramify_markdown.markdownify(config['mainconf']['noadmin_text'])
                    await bot.send_message(chat_id, text, parse_mode='MarkdownV2')   
                    logger.info(f"{username}, ({chat_id}), пытался выполнить {message_text}")  
                    

            else:                            # === обработка обычного текста (не команд) ===
                
                if chat_db.is_admin(chat_id) and chat_db.flag(chat_id, "SpamFlag"):         #если у пользователя поднят флаг ожидания спам сообщения                
                    await spam_processing(chat_id, message_id, message_text)  
                    
                elif chat_db.is_admin(chat_id) and chat_db.flag(chat_id, "NoRoleQFlag"):         #если у пользователя поднят флаг ожидания вопроса ИИ без роли
                    await question_for_ai_norole(chat_id, message_text)       
                    
                elif chat_db.hm_responses_today(chat_id) > int(config['mainconf']['responses_limit']) and not chat_db.is_admin(chat_id): #если лимит пользователя на сегодня исчерпан (и пользовтаель не админ)
                    keyboard = types.InlineKeyboardMarkup()
                    url_button = types.InlineKeyboardButton(text='👀', url=config['mainconf']['contacts'])
                    keyboard.add(url_button)
                    await bot.send_message(chat_id, config['mainconf']['limit_msg'], reply_markup=keyboard)                  # Отправка сообщение с ссылкой
                    
                else:
                    await question_for_ai(chat_id, message_text, message_id)


        elif hasattr(message, 'document') and hasattr(message.document, 'file_name') and message.document.file_name == config_file_name:  # если пришел файл с настройками
            if chat_db.is_admin(chat_id): #если админ              
                await handle_set_config(chat_id, message.document.file_id) 
                logger.info(f"{username}, ({chat_id}), поменял файл настроек")      
            else: 
                text = telegramify_markdown.markdownify(config['mainconf']['noadmin_text']) #если не админ
                await bot.send_message(chat_id, text, parse_mode='MarkdownV2')   
                logger.info(f"{username}, ({chat_id}), пытался поменять файл настроек")  
                
        
    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}, свяжитесь с {config['mainconf']['admin_link']}")
        logger.error(f"Ошибка обработчика любых сообщений - {e}")



       

# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
async def callback_query(call):
    try:
        chat_id = call.message.chat.id
        
        if chat_db.is_admin(chat_id): #если админ
            if call.data == 'call_btn_spam':
                await new_spam(chat_id)
                await bot.answer_callback_query(call.id)
                
            elif call.data == 'call_btn_stat':
                await get_stat(chat_id)
                await bot.answer_callback_query(call.id)
                    
            elif call.data == 'call_btn_norole_q':
                text = telegramify_markdown.markdownify("Следующим сообщением задай вопрос ИИ.\n" +
                                        "Обрати внимание, что это обычный запрос к модели CHAT-GPT4o без каких либо " +
                                        "предписаний поведения и знания контекста ранней переписки и предыдущих вопросов. " +
                                        "Формулируй вопрос развёрнуто, описывая контекст и поведение ассистента, если это требуется. \n" +
                                        "Например _Составь рекламное сообщение..._ или _Посоветуй как написать..._") #если не админ
                await bot.send_message(chat_id, text, parse_mode='MarkdownV2')  
                chat_db.flag(chat_id, "NoRoleQFlag", 1) # поднимаем флаг
                await bot.answer_callback_query(call.id)
                    
            elif call.data == 'call_btn_service':
                text = ('`/new_admin_pass старый_пароль новый_пароль` - замена пароля\n' + 
                        '/dw_config - скачать текущий файл настроек\n' +
                        '/unlogin - разлогиниться (перестать быть администратором)\n')            #в будущем убрать (?)
                text = telegramify_markdown.markdownify(text)      # чистим markdown
                await bot.send_message(chat_id, text, parse_mode='MarkdownV2')   
                await bot.answer_callback_query(call.id)
                    
            else:
                raise ValueError(f"Кнопка {call.data} не найдена.") #принудительная ошибка
            

        else: 
            text = telegramify_markdown.markdownify(config['mainconf']['noadmin_text']) #если не админ
            await bot.send_message(chat_id, text, parse_mode='MarkdownV2')   
            await bot.answer_callback_query(call.id, "Вы не администратор")    
    
    except Exception as e:
        await bot.answer_callback_query(call.id, "Что то пошло не так.")
        logger.error(f"Ошибка обработки нажатия на inline кнопки - {e}")
        
        
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
#  биллинг токенов для каждого и суммарный
# статистика (кол-во пользователей, кол-во сообщений всего , кол-во сообщений сегодня...)  хз надо ли
# отправлять в архив после 2 неудачных попыток отправки
#  ???
# Профит
