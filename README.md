this is experiments tg AI chat bot )

#### Как что то исправить или просто переехать?
    -1. Скачиваешь репозиторий с гита - 
    -2. С рабочего бота стягиваешь папку data - /dw_data ...
    -3. ...если нужно, все проверяешь все настройки в а) .env b) config.py
    -4. docker build . -t mk_req_check:vXX
    -5. После сборки запускать коммандой docker run --name mk_req_check --restart unless-stopped -d mk_req_check:vXX


     

##### Поясняю:
бот для бизнеса с OpenAI, который общается за тебя и продаёт твой товар/услуги



Собираем:
``` docker build . -t shop_bot:vXX ```
 
 Запускаем:
 ```docker run --name shop_bot --restart unless-stopped -d shop_bot:vXX```

Запуск без остановки по причине невыполнения ничего внутри:
```docker run --name shop_bot --restart unless-stopped -d shop_bot:vXX tail -f /dev/null```

