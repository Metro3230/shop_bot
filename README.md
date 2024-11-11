this is experiments tg AI chat bot )

#### Как что то исправить или просто переехать?
    1. Скачиваешь репозиторий с гита - 
    
    
    4. docker build . -t mk_req_check:vXX
    5. После сборки запускать коммандой docker run --name mk_req_check --restart unless-stopped -d mk_req_check:vXX


     

##### Поясняю:
+ kkkkk
+ lllll


Собираем:
``` docker build . -t shop_bot:vXX ```
 
 Запускаем:
 ```docker run --name shop_bot --restart unless-stopped -d shop_bot:vXX```

Запуск без остановки по причине невыполнения ничего внутри:
```docker run --name shop_bot --restart unless-stopped -d shop_bot:vXX tail -f /dev/null```

и еще этот ебучий 
--break-system-packages
каждый раз сука, е2й красноглазый люнох

