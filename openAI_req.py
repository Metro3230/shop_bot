from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
from config import AIconf
import os

script_dir = Path(__file__).parent  # Определяем путь к текущему скрипту
data_dir = script_dir / 'data'
log_file = script_dir / data_dir / 'log.log'
env_file = script_dir / data_dir / '.env'

load_dotenv(env_file)
ai_API_key = os.getenv('OPENAI_API_KEY')    # читаем token ai c .env
 
client = OpenAI(
    api_key=ai_API_key,
    base_url=AIconf.ai_API_url,
)

system_role = {"role": "system", "content": AIconf.ai_role}

def req_to_ai(msgs):
    msgs.insert(0, system_role)
    response = client.chat.completions.create(
    model="gpt-4o",
    messages=msgs,
    )

    return response





test_msg = "Ах, ищешь немного острых ощущений, да? 😏 В мире БДСМ у нас полно горячих штучек. В зависимости от твоего опыта и предпочтений, вот несколько из любимчиков:\n\n1. **Бондаж и фиксаторы**: шикарные кожаные или атласные веревки, наручники, ошейники – всё для сладостного подчинения.\n\n2. **Плети и шлепалки**: от мягких перышков до более жёсткого кожаного веера, выбирай уровень интенсивности для сладкой боли.\n\n3. **Маски и кляпы**: чтобы создать тайну и усилить ощущения. Ничто так не разбавит обстановку, как небольшой кляп.\n\n4. **Фетиш-одежда**: латекс, винил или кожа – всё, что заставит сердца биться чаще.\n\n5. **Электростимуляция**: для тех, кто хочет чего-то необычного, небольшая порция электричества может стать приятным сюрпризом.\n\nКонечно, всегда помни о безопасном слове и согласии, ведь удовольствие должно быть для всех сторон. Если есть вопросы или что-то конкретно интересует, дай знать! 😉"

def req_to_ai_TEST(msgs):

    return test_msg





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








