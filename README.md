# Телеграм бот ЭмБио

## Description

Телеграм бот ЭмБио - это виртуальный помощник, который всегда будет на связи с пациентом. Он поддержит, напомнит о процедуре, поделится полезными материалами и ответит на вопросы, предоставляя пользователю ощущение заботы и внимания.

## User Guide

[Руководство пользователя](Documentation/USER_GUIDE.md)

## Get started

1. **Подготовка окружения:**
   - Токен и другие конфигурационные данные для запуска бота должны быть прописаны в скрытом `.env` файле.
   - Все необходимые библиотеки указаны в файле `requirements.txt`.

2. **Создание файла `.env`:**
   В корневой директории проекта создайте файл `.env` и добавьте в него следующие строки:

   ```plaintext
   TOKEN=your_telegram_bot_token
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   URL=your_crm_url
   USERNAME_CRM=your_crm_username
   PASSWORD_CRM=your_crm_password
   REDIS_HOST= your_redis_host
   REDIS_PORT= your_redis_port
   REDIS_URL= your_redis_url
   REDIS_PASSWORD= your_redis_password
   SUPPORT_GROUP_ID = id_support_tg_group
   ```

3. **Устанока зависимостей:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Запуск бота**

   ```bash
   python run.py
   ```

## Libraries

![Libraries](https://github.com/user-attachments/assets/8cb23572-189e-4adc-a295-729eaaa37b8c)


### Brief description of the libraries used

|   **Library**  |                                **Description**                               |
|:--------------:|:----------------------------------------------------------------------------:|
| aiogram        | Фреймворк, на котором написан бот                                            |
| asyncio        | Необходим для асинхронных операций в боте                                    |
| python-dotenv  | Загрузка токенов, паролей и ссылок из файлов .env                            |
| aiohttp        | Для отправки асинхронных HTTP запросов и асинхронной обработки HTTP ответов. |
| supabase       | Библиотека для взаимодействия с базой данной Supabase.                       |
| pytest         | Библиотека для работы модульных тестов                                       |
| pytest-asyncio | Бибилотека для тестирования асинхронного кода                                |
| APScheduler    | Библиотека для отправки сообщений из очереди по времени                      |
| redis          | Библитека для выставления очереди сообщений                                  |
| httpx          | Полнофункциональный HTTP-клиент                                              |
| pytz           | Библиотека для работы с часовыми поясами и форматами времени                 |

### Documentation

|   **Frame**   |                          **Docs**                         |
|:-------------:|:---------------------------------------------------------:|
| Supabase      | <https://supabase.com/docs>                                 |
| Aiogram       | <https://docs.aiogram.dev/>                                 |
| Asyncio       | <https://docs.python.org/3/library/asyncio.html>            |
| Aiohttp       | <https://docs.aiohttp.org/>                                 |
| Pytest        | <https://docs.pytest.org/>                                  |
| APScheduler   | <https://apscheduler.readthedocs.io/>                       |
| Redis         | <https://redis.io/docs/latest/>                             |
| Httpx         | <https://www.python-httpx.org/>                             |
| Pytz          | <https://github.com/stub42/pytz/blob/master/src/README.rst> |
| Python-dotenv | <https://www.dotenv.org/docs/>                              |

## Finite state machine

![image](https://github.com/user-attachments/assets/aab25b1e-05c1-4531-94a9-f3b766d17c94)

Стейты (состояние) необходимы для управления последовательностью действий пользователя и контекстом взаимодействия. Они позволяют боту понимать, на каком этапе взаимодействия находится пользователь, и обрабатывать его ввод в зависимости от текущего состояния.
Для того, чтобы создать новый стейт, необходимо создать новый класс, наследуя его от “StatesGroup”. Далее определите новый стейт внутри класса, используя State().

Эти шаги позволят вам добавить новый класс в машину состояний (FSM).

## Structure

### Project structure

![Untitled](https://github.com/user-attachments/assets/eebf0024-4baa-4a08-8703-34a1b5bab8fd)

### Database structure

![image](https://github.com/user-attachments/assets/ec788dd5-c3cb-4a43-91df-47a52b100c58)

### .env structure

```
TOKEN = “Токен телеграм бота”
USERNAME_CRM = “Имя пользователя в CRM”
PASSWORD_CRM = “Пароль пользователя в CRM”
URL = “Ссылка на точку входа в CRM”
SUPABASE_URL = “Ссылка на базу данных supabase”
SUPABASE_KEY = “Ключ supabase”
REDIS_HOST = “ip адрес сервера redis”
REDIS_PORT = “порт сервера redis”
REDIS_URL = “ссылка вида redis://REDIS_PASSWORD:@REDIS_HOST:REDIS_PORT/0”
REDIS_PASSWORD = “Пароль от redis”
SUPPORT_GROUP_ID = “Айди супергруппы поддержки, начинающиеся с -100”
```

### Json structure

#### Types of possible content in a scenario

* text - обычный текст, без медиаматериала
* image - фотоматериал
* video - видеоматериал
* text image - текстовый материал + фото для общей отправки
* text video - текстовый материал + видео для общей отправки
* survey - опрос

#### Structure scenario json

![general-scenarios (1)](https://github.com/user-attachments/assets/8fa21aac-a220-423b-9674-1547bace426f)


#### Structure survey json

![survey-scenarios](https://github.com/user-attachments/assets/663ca310-4067-4f4f-9d60-957c9bc9f6c0)

