import sqlite3
from pathlib import Path


script_dir = Path(__file__).parent  # Определяем путь к текущему скрипту
data_dir = script_dir / 'data'
user_db = data_dir / 'users.db'
msg_report = data_dir / 'msg_report.html'





def msg_to_html():

    # Подключение к базе данных
    conn = sqlite3.connect(user_db)
    cursor = conn.cursor()

    # Извлечение данных из таблицы Users
    cursor.execute('SELECT UserID, SenderName, UserName FROM Users')
    users = cursor.fetchall()

    # Извлечение данных из таблицы Messages
    cursor.execute('SELECT UserID, Role, Text, Sent_at, Del FROM Messages')
    messages = cursor.fetchall()

    # Создание HTML-страницы
    html = '''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Отчёт по сообщениям</title>
        <style>
            .collapsible {
                background-color: #777;
                color: white;
                cursor: pointer;
                padding: 18px;
                width: 100%;
                border: none;
                text-align: left;
                outline: none;
                font-size: 15px;
                user-select: text;
            }
            .active, .collapsible:hover {
                background-color: #555;
            }
            .content {
                padding: 0 18px;
                display: none;
                overflow: hidden;
                background-color: #f1f1f1;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
        </style>
        <!-- Подключаем библиотеку marked.js для преобразования Markdown в HTML -->
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    </head>
    <body>
        <h1>Отчёт по сообщениям</h1>
    '''

    # Добавление раскрывающихся списков для каждого пользователя
    for user in users:
        user_id, sender_name, user_name = user
        html += f'''
        <button type="button" class="collapsible">{sender_name} ({user_name}) - ID: {user_id}</button>
        <div class="content">
            <table border="1">
                <tr>
                    <th>Role</th>
                    <th>Text</th>
                    <th>Sent_at</th>
                    <th>Del</th>
                </tr>
        '''
        
        # Добавление сообщений для текущего пользователя
        for msg in messages:
            if msg[0] == user_id:
                role, text, sent_at, deleted = msg[1], msg[2], msg[3], msg[4]
                html += f'''
                <tr>
                    <td>{role}</td>
                    <td class="markdown-text">{text}</td>
                    <td>{sent_at}</td>
                    <td>{'Да' if deleted else 'Нет'}</td>
                </tr>
                '''
        
        html += '''
            </table>
        </div>
        '''

    html += '''
    <script>
        // Функция для преобразования MarkdownV2 в HTML
        function renderMarkdown() {
            const markdownElements = document.querySelectorAll('.markdown-text');
            markdownElements.forEach(element => {
                const markdown = element.textContent;
                element.innerHTML = marked.parse(markdown); // Преобразуем Markdown в HTML
            });
        }

        // Раскрывающиеся списки
        var coll = document.getElementsByClassName("collapsible");
        for (var i = 0; i < coll.length; i++) {
            coll[i].addEventListener("click", function() {
                this.classList.toggle("active");
                var content = this.nextElementSibling;
                if (content.style.display === "block") {
                    content.style.display = "none";
                } else {
                    content.style.display = "block";
                }
            });
        }

        // Преобразуем Markdown в HTML после загрузки страницы
        document.addEventListener('DOMContentLoaded', renderMarkdown);
    </script>
    </body>
    </html>
    '''

    # Сохранение HTML-страницы в файл
    with open(msg_report, 'w', encoding='utf-8') as f:
        f.write(html)

    # Закрытие соединения с базой данных
    conn.close()

    