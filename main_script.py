import chat_processing as chat
import openAI_req as openAI
from pathlib import Path
from dotenv import load_dotenv
import re
import os
# import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from config import mainconf
import telegramify_markdown #библитека преобразования markdown в телеграммный markdown_n2


script_dir = Path(__file__).parent  # Определяем путь к текущему скрипту
data_dir = script_dir / 'data'
log_file = script_dir / data_dir / 'log.log'
env_file = script_dir / data_dir / '.env'

load_dotenv(env_file)
tg_token = os.getenv('TG_TOKEN')    # читаем token ai c .env

bot = AsyncTeleBot(tg_token)

#-----------------\/-сервисные команды обновления сервисных файлов и клава-\/----------------------------

async def remove_limit(chat_id, message): #---обновление токена мультикарты---
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль, и новый токен
            await bot.send_message(chat_id, "Ошибка: формат команды /remove_limit <service pass>")
            return
        
        input_password = command_parts[1]

        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность сервисного пароля
            chat.remove_limit(chat_id)   #вызываем чистку лимита для чата
            await bot.send_message(chat_id, "Дневной лимит для тебя сброшен")
        else:
            await bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        pass
#----------------------------------------------------------------------------------------


# --------------------Обработчик для всех текстовых сообщений----------------------------
@bot.message_handler(func=lambda message: True)
async def echo_message(message):
    message_text = message.text
    chat_id = message.chat.id
    username = message.from_user.username
    
    if message_text.startswith('/'): #обработка сервисных команд
        if message_text == "/start":
            await bot.send_message(chat_id, mainconf.start_message)
        elif message_text == "/service":
            await bot.send_message(chat_id, '/remove_limit <service pass> - заменить Bearer токен S1\n' +
                                            'что то еще\n')
        elif message_text.startswith('/remove_limit'):
            await remove_limit(chat_id, message_text)
            
    else:
        if chat.get_msg_count(chat_id) > mainconf.msgs_limit:            
            keyboard = types.InlineKeyboardMarkup()
            url_button = types.InlineKeyboardButton(text='👀', url=mainconf.site_url)
            keyboard.add(url_button)
            await bot.send_message(chat_id, mainconf.limit_msg, reply_markup=keyboard)                  # Отправка сообщение с ссылкой
        else:
            chat.save_message_to_json(chat_id, "user", username, message_text)   #записываем текст сообщения от ЮЗЕРА в историю сообщений
            # response = openAI.req_to_ai(chat.get_last_messages(chat_id))   #отправляем историю чата (чат ид) боту
            # response_text = response.choices[0].message.content         #парсим текст ответа
            response_text = openAI.req_to_ai_TEST(chat.get_last_messages(chat_id))   #ТЕСТОВЫЙ ОТВЕТ БЕЗ ТРАТЫ ТОКЕНОВ
            response_text = telegramify_markdown.markdownify(response_text)      # чистим markdown
            chat.save_message_to_json(chat_id, "assistant", username, response_text)      #записываем текст сообщения от БОТА в историю сообщений
            await bot.send_message(chat_id, response_text, parse_mode='MarkdownV2')     #отправляем ответ
            
#----------------------------------------------------------------------------------------

# Запуск бота
async def main():
    await bot.polling()
    

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())










# chat_id = 1234562789

# print(openAI.req_to_ai(chat.get_last_messages(chat_id)))

