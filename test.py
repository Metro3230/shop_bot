import telebot
from telebot import types
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
import os


script_dir = Path(__file__).parent  # Определяем путь к текущему скрипту
log_file = script_dir / 'log.log'
env_file = script_dir / '.env'

load_dotenv(env_file)
tg_token = os.getenv('TG_TOKEN')    # читаем token tg
ai_API = os.getenv('OPENAI_API_KEY')    # читаем token ai
ai_URL = "https://api.proxyapi.ru/openai/v1"

client = OpenAI(
    api_key=ai_API,
    base_url=ai_URL,
)

# описание роли ассистента
role = 'you are an AI bot for an adult toy store, your answers are a bit filthy'

# Список для хранения истории переписки а так же первый запрос внутри
conversation_history = [{"role": "system", "content": role}]

def get_response(prompt):
    global conversation_history
    # Формируем запрос к OpenAI API с учетом истории переписки
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=conversation_history + [{"role": "user", "content": prompt}]
    )
    # print(response)
    # Получаем ответ от ассистента
    assistant_reply = response.choices[0].message.content
    return assistant_reply

def main():
    print("Чат-бот консоли. Напишите 'exit' для завершения.")
    
    while True:
        global conversation_history
        # Запрашиваем сообщение от пользователя
        user_input = input("Вы: ")
        if user_input.lower() == 'exit':
            print("Чат завершен.")
            break

        # Добавляем сообщение пользователя в историю
        conversation_history.append({"role": "user", "content": user_input})
        
        # Получаем ответ ассистента и выводим его
        assistant_reply = get_response(user_input)
        print(f"Ассистент: {assistant_reply}")
        
        # Добавляем ответ ассистента в историю
        conversation_history.append({"role": "assistant", "content": assistant_reply})
        
        # Оставляем только последние 10 сообщений (5 от пользователя и 5 от ассистента)
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]

if __name__ == "__main__":
    main()
