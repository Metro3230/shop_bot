


class AIconf:
    ai_API_url = "https://api.proxyapi.ru/openai/v1"                                       #ссылка API
    ai_role = "you are an AI bot for an adult toy store, your answers are a bit filthy"   #сервисная фраза для поведения бота
    
class chatconf:
    latest_posts = 5    #глубина контекста переписки (кол-во последних сообщений из преписки)

class mainconf:
    start_message = "Привет, это чат-бот магазина ИНТИМ, можешь спросить меня о самом откровенном"    #сообщение при получении /start
    msgs_limit = 10     #дневной лимит сообщений (считаются и ответы бота)
    limit_msg = "Ого, вы так общительны, но сегодня я устал 🫠 Посмотри наш каталог, а завтра я снова смогу ответить тебе."    #сообщение при окончании лимита сообщений
    site_url = "https://intim13.ru/"         #ссылка в кнопке при окончании лимита сообщенеий

