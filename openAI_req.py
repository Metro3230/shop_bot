from dotenv import load_dotenv
from openai import AsyncOpenAI, APIError
from pathlib import Path
import os
import configparser

script_dir = Path(__file__).parent  # Определяем путь к текущему скрипту
data_dir = script_dir / 'data'
log_file = script_dir / data_dir / 'log.log'
env_file = script_dir / data_dir / '.env'
config_file = data_dir / 'config.ini'
 
config = configparser.ConfigParser()  # настраиваем и читаем файл конфига
config.read(config_file)

load_dotenv(env_file)
# ai_API_key = os.getenv('OPENAI_API_KEY')    # читаем token ai c .env 
ai_model = config['AIconf']['ai_model']
contacts_key_words = config['AIconf']['contacts_key_words'].split(',')  #массив с ключевыми словами, изменяющими модель поведения


# подгружаем ключи, столько, сколько их есть у нас в .env
ai_API_keys = []
i = 1
while True:
    env_var_name = f"OPENAI_API_KEY_{i}"
    api_key = os.getenv(env_var_name)
    if api_key is None:
        break
    ai_API_keys.append(api_key)
    i += 1


# client = AsyncOpenAI(
#     api_key=ai_API_keys,
#     base_url=config['AIconf']['ai_API_url'],
#     timeout=float(config['AIconf']['ai_req_timeout']),
# )

system_role = {"role": "system", "content": config['AIconf']['ai_role']}
system_role_contacts = {"role": "system", "content": config['AIconf']['ai_role'] + '. ' + config['AIconf']['ai_role_instruction']}


def is_part_in_list(strCheck):   #Проверка наличия ключевых слов     
    for i in range(len(contacts_key_words)):
        if strCheck.find(contacts_key_words[i]) != -1:
            return True
    return False



async def req_to_ai(msgs):
    if is_part_in_list(msgs[-1]['content']):  # если в последней фразе есть слова из списка
        msgs.insert(0, system_role_contacts)
    else:
        msgs.insert(0, system_role)
    
    last_exception = None  # Сохраняем последнее исключение
    
    for ai_api_key in ai_API_keys:
        client = AsyncOpenAI(
            api_key=ai_api_key,
            base_url=config['AIconf']['ai_API_url'],
            timeout=float(config['AIconf']['ai_req_timeout']),
        )
        try:
            response = await client.chat.completions.create(
                model=ai_model,
                messages=msgs,
            )
            return response  # Если запрос успешен, возвращаем ответ
        except Exception as e:  # Отлавливаем ЛЮБОЕ исключение
            last_exception = e  # Сохраняем исключение
            continue  # Пробуем следующий ключ
    
    if last_exception:
        raise Exception("All API keys failed") from last_exception  # поднимаем исключение с причиной
    else:
        raise Exception("No API keys available or no exception was caught")  # что то другое



async def req_to_ai_norole(msg):
    
    req = [{"role": "user", "content": msg}]
    
    for ai_api_key in ai_API_keys:                    
        client = AsyncOpenAI(
            api_key=ai_api_key,
            base_url=config['AIconf']['ai_API_url'],
            timeout=float(config['AIconf']['ai_req_timeout']),
        )
        try:
            response = await client.chat.completions.create(
                model=ai_model,
                messages=req,
            )
            return response  # Если запрос успешен, возвращаем ответ
        except Exception as e:  # Отлавливаем ЛЮБОЕ исключение
            last_exception = e  # Сохраняем исключение
            continue  # Пробуем следующий ключ
    
    if last_exception:
        raise Exception("All API keys failed") from last_exception  # поднимаем исключение с причиной
    else:
        raise Exception("No API keys available or no exception was caught")  # что то другое









# otvet = [
#     {'role': 'assistant', 'content': 'Расскажи чуть подробнее о своих желаниях?'},
#     {'role': 'user', 'content': 'Мы с моей девушкой любим чуть пожесче, что ты мог бы предложить?'},
#     {'role': 'assistant', 'content': 'У нас есть отличные наборы для БДСМ, а так же советую обратить внимание на наручники и плети! '},
#     {'role': 'user', 'content': 'Ого, наручники?'},
#     {'role': 'assistant', 'content': 'Да, специальные наручники сделают Ваш вечер незабываемым, немного вина, и ваши желания воплотятся в реальность!'},
#     {'role': 'user', 'content': 'Вау, это интересно, а как можно поступить с ключиком?'}
#     ]


# response = req_to_ai(otvet)

# response_text = response.choices[0].message.content

# print(response)
# print(response_text)








