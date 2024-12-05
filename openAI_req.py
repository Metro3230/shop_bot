from dotenv import load_dotenv
from openai import AsyncOpenAI
from pathlib import Path
# from config import AIconf
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
ai_API_key = os.getenv('OPENAI_API_KEY')    # читаем token ai c .env
 
client = AsyncOpenAI(
    api_key=ai_API_key,
    base_url=config['AIconf']['ai_API_url'],
)

contacts_key_words = config['AIconf']['contacts_key_words'].split(',')  #массив с ключевыми словами, изменяющими модель поведения

system_role = {"role": "system", "content": config['AIconf']['ai_role']}
system_role_contacts = {"role": "system", "content": config['AIconf']['ai_role'] + '. ' + config['AIconf']['ai_role_instruction']}


def is_part_in_list(strCheck):   #Провера наличия клоючевых слов     
    for i in range(len(contacts_key_words)):
        if strCheck.find(contacts_key_words[i]) != -1:
            return True
    return False


async def req_to_ai(msgs):
    if (is_part_in_list(msgs[-1]['content'])):      #если есть в последней фразе слова из списка 
        msgs.insert(0, system_role_contacts)
    else:
        msgs.insert(0, system_role)
    response = await client.chat.completions.create(
    model="gpt-4o",
    messages=msgs,
    )
    return response


async def req_to_ai_norole(msg):
    req = [{"role": "user", "content": msg}]
    response = await client.chat.completions.create(
    model="gpt-4o",
    messages=req,
    )
    return response


# test_msg = "Ах, ищешь немного острых ощущений, да? 😏 В мире БДСМ у нас полно горячих штучек. В зависимости от твоего опыта и предпочтений, вот несколько из любимчиков:\n\n1. **Бондаж и фиксаторы**: шикарные кожаные или атласные веревки, наручники, ошейники – всё для сладостного подчинения.\n\n2. **Плети и шлепалки**: от мягких перышков до более жёсткого кожаного веера, выбирай уровень интенсивности для сладкой боли.\n\n3. **Маски и кляпы**: чтобы создать тайну и усилить ощущения. Ничто так не разбавит обстановку, как небольшой кляп.\n\n4. **Фетиш-одежда**: латекс, винил или кожа – всё, что заставит сердца биться чаще.\n\n5. **Электростимуляция**: для тех, кто хочет чего-то необычного, небольшая порция электричества может стать приятным сюрпризом.\n\nКонечно, всегда помни о безопасном слове и согласии, ведь удовольствие должно быть для всех сторон. Если есть вопросы или что-то конкретно интересует, дай знать! 😉"

# def req_to_ai_TEST(msgs):

#     return test_msg








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








