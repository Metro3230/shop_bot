import chat_processing as chat
import openAI_req as openAI
from pathlib import Path
from dotenv import load_dotenv
import os
# import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from config import mainconf
import telegramify_markdown #библитека преобразования markdown в телеграммный markdown_n2
import shutil
from datetime import datetime
import logging
import asyncio

script_dir = Path(__file__).parent  # Определяем путь к текущему скрипту
data_dir = script_dir / 'data'
msg_hist_dir = data_dir / 'msg_hits'   #папка с историями сообщений
msg_arch_dir = msg_hist_dir / 'archive'
log_file = data_dir / 'log.log'
env_file = data_dir / '.env'
data_zip = script_dir / 'data.zip'

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
            await bot.send_message(chat_id, "Ошибка: формат команды /remove_limit <пароль>")
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
            await bot.send_message(chat_id, "Формат команды /q <пароль> <вопрос>\n" +
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
            await bot.send_message(chat_id, "Ошибка: формат команды /dw_data <пароль>")
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
        
        

async def handle_new_service_pass(chat_id, message): #----------обновление сервисного пароля--------------+
    try:
        old_service_pass = os.getenv('SERVICE_PASS')       # пишем в лог старый файл на всякий
        logger.info('попытка смены сервисного пароля: "' + old_service_pass + '" на новый...')

        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 3:         # Проверяем, что есть и пароль, и новый токен
            await bot.send_message(chat_id, "Ошибка: формат команды /new_service_pass <сервисный_пароль> <новый_сервисный_пароль>")
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

#----------------------------------------------------------------------------------------------------------


#----------------------------------------------\/-СПАМ-\/---------------------------------------------------
        
async def new_spam(chat_id, message): #---создание СПАМ рассылки ------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль, и новый токен
            await bot.send_message(chat_id, "Ошибка: формат команды /spam <пароль>")
            return
        
        input_password = command_parts[1]
              
        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность сервисного пароля
            await bot.send_message(chat_id, 'Следующим сообщением отпарвь то, что хочешь отправить всем пользователям БОТа\.\n' +
                                            '_· к сообщению может быть прикреплена ссылка, 1 картинка, 1 документ_\n' +
                                            '_· можно использовать форматирование_\n' +
                                            '_· опросы и виктарины не поддерживаются_\n', parse_mode='MarkdownV2')
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
            actual_users = get_actual_ids() #получаем список актуальных пользователей
            luck_sends = await sent_spam(actual_users, chat_id, message_id-2) #рассылаем, копируя пред-предыдущее сообщение
            await bot.send_message(chat_id, f"Отправлено {luck_sends} пользователям.\n")
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
                                            "Начать рассылку?", reply_markup=keyboard)       # Отправляем сообщение с клавиатурой
    except Exception as e:
        logger.error(f"Ошибка обработки СПАМ рассылки - {e}")


async def sent_spam(users, chat_id, message_id):#---рассылка спама (users кому слать (массив), chat_id из какого чата, message_id ид сообщения)---+
    try:
        luck_sends = 0 #счётчик удачных отпрвлений
        
        for item in users:
            try:
                await bot.copy_message(     # рассылаем 
                    chat_id=item,  # Кому отправляем
                    from_chat_id=chat_id,  # Откуда берем сообщение
                    message_id=message_id  # ID сообщения для копирования
                )
                if temp_spam_text is not None:
                    chat.save_message_to_json(chat_id=item, role="assistant", message=temp_spam_text)      #и записываем рекламный текст от БОТА в историю сообщений каждого участника
                luck_sends += 1
            except:
                arch_chat(item)  #если не удалось отправить, значит пользователь удалил и остановил бота, отправляем его в архив

        return luck_sends
    except Exception as e:
        logger.error(f"Ошибка рассылки спама - {e}")


def get_actual_ids(): #---Получение списка пользователей в виде массива-----------------------+
    try:
        json_filenames = []

        for filename in os.listdir(msg_hist_dir):    # Перебираем все файлы в папке
            if filename.endswith('.json'):        # Проверяем, имеет ли файл расширение .json
                json_filenames.append(os.path.splitext(filename)[0])            # Добавляем имя файла без расширения в массив

        return json_filenames
    except Exception as e:
        logger.error(f"Ошибка получения списка пользователей - {e}")


def arch_chat(chat_id):#---Архивирование чата chat_id-------------------------------------------------------
    
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
        logger.error(f"Ошибка архивирования чата {chat_id} - {e}")

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
        await bot.send_message(chat_id, response_text, parse_mode='MarkdownV2')     #отправляем ответ
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
                await bot.send_message(chat_id, mainconf.start_message)
                
            elif message_text == "/service":
                await bot.send_message(chat_id, '`\/q `\- задать вопрос Chat\-GPT вне формата бота\n' +
                                                '`\/spam `\- рассылка всем пользователям бота\n\n' +
                                                '`\/dw\_data `\- скачать папку с данными\n' +
                                                '`\/remove\_limit `\- обнулить лимит на сегодня\n' +
                                                '`\/new\_service\_pass `\- замена сервисного пароля\n' +
                                                '', parse_mode='MarkdownV2')
                
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
            
        else:                            #обработка обычного текста (не команд)
            if chat.spam_flag(chat_id):         #если у пользователя поднят флаг ожидания спам сообщения                
                await spam_processing(chat_id, message_id, message_text)                
                
            elif chat.get_msg_count(chat_id) > mainconf.msgs_limit: #если лимит пользователя на сегодня исчерпан
                keyboard = types.InlineKeyboardMarkup()
                url_button = types.InlineKeyboardButton(text='👀', url=mainconf.contacts)
                keyboard.add(url_button)
                await bot.send_message(chat_id, mainconf.limit_msg, reply_markup=keyboard)                  # Отправка сообщение с ссылкой
                
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
#  биллинг токенов для каждого и суммарный
# статистика (кол-во пользователей, кол-во сообщений всего , кол-во сообщений сегодня...)  хз надо ли
#  ???
# Профит
