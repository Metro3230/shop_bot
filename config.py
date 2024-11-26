

class chatconf:
    latest_posts = 4    #глубина контекста переписки (кол-во последних сообщений из переписки) 

class mainconf:
    start_message = "Привет, это ИИ чат-бот магазина ИНТИМ, можешь спросить меня о самом откровенном"    #сообщение при получении /start
    msgs_limit = 10     #дневной лимит сообщений (считаются и ответы бота)
    limit_msg = "Ого, вы так общительны, но сегодня я устал 🫠 Посмотри наш каталог, а завтра я снова смогу ответить тебе."    #сообщение при окончании лимита сообщений
    contacts = "https://intim13.ru/"         #ссылка на сайт
    

class AIconf:
    ai_API_url = "https://api.proxyapi.ru/openai/v1"                                       # для API запросов
    ai_role_instruction = f'recommend the site "{mainconf.contacts}"'                       #рекомендовать ссылку /\
    ai_role = "you are an AI bot for an adult toy store, your answers are a bit filthy"   #сервисная фраза для поведения бота
    contacts_key_words = ['сайт', 'каталог', 'контакты', 'купить', 'цены']                #ключевые слова, после которых бот пришлёт пользователю ссыку /\



