# Руководство пользователя Ассистент ЭмБио

## Аутентификация

При заходе в бота, пользователь имеет доступ к единственной кнопке – /start.\
После нажатия на кнопку, начинается аутентификация.\
Пользователь может ввести номер телефона вручную в формате +7 или поделиться с помощью кнопки “Поделиться своим номера телефона”.\
Если учетной записи с таким номером нет в CRM, то выводится сообщение ”Номер телефона не был найден на сервере. Пожалуйста, введите номер, который привязан к учетной записи”.\
Если учетная запись пациента есть, то для подтверждения нужно ввести 4 последний цифра номера паспорта.\
Если учетная запись врача есть, то для подтверждения нужно ввести ID врача из CRM.

<img src="https://github.com/user-attachments/assets/66ab6fce-d595-458b-b0bc-6b7e8cfd6b11" width="400">


## Пациент

### Клавиатура пациента

Клавиатура пациента представляет из себя набор кнопок для удобной навигации по боту, а также список команд для навигации:
Клавиатура пациента состоит из следующих кнопок:

* Расписание
* Задать вопрос

#### Кнопка “Расписание”

При нажатие кнопки “Расписание” пациент получает сообщение с информацией о ближайшей процедуре:

* Дата и время
* Название процедуры
* ФИО врача

<img src="https://github.com/user-attachments/assets/aa724df8-ab06-4538-b46e-25cb5b9daa55" width="400">

#### Раздел “Задать вопрос”

Раздел "Задать вопрос" предоставляет пациентам возможность напрямую обратиться в Call Center клиники. После нажатия на кнопку “Задать вопрос” получает сообщение “Задайте свой вопрос, который отправится в поддержку”, клавиатура пользователя меняется на кнопку “Вернуться в меню”.

Если пользователь нажимает кнопку  “Вернуться в меню”, его переводит в главное меню и выводит клавиатуру основного меню.

Пользователь может отправить текст в пределах одного сообщения. Затем бот отправляет сообщение в беседу Call Center клиники в Telegram. Пока заявка на помощь активна, кнопка “Задать вопрос” в клавиатуре заменяется на кнопку “Отменить вопрос”.

Беседа Call Center клиники может ответить на вопрос с помощью функционала Telegram, нажав на сообщение и выбрав кнопку “Ответить”. После получения ответа на вопрос, заявка будет автоматически закрыта, и у пользователя появится кнопка "Задать вопрос" повторно для возможности задать новый вопрос.

<img src="https://github.com/user-attachments/assets/009cbcec-ed11-43d5-8862-07ec75ae9330" width="400">

### Раздел “Опросы”

В раздел “Опросы” пользователь может попасть только, когда присылается опрос по отложенной очереди сообщений. Раздел представляет из себя опрос с закрытыми или открытыми вопросами.\
Если опрос с закрытыми вариантами, то приходит сообщение с инлайн-кнопками ответов. Пока пользователь не пройдет опрос, клавиатура пациента исчезает.\
Если опрос с открытыми вариантами, то приходит сообщение с инлайн-кнопкой “Нет вопросов”, клавиатура пациента исчезает.\
Если пользователь нажмет “Нет вопросов”, то опрос закончится и вернется клавиатура пациента.\
Ответ пользователя в пределах одного сообщения. При отправке сообщения, появляется сообщение “Спасибо за сообщение” и возвращается клавиатура пациента.

<img src="https://github.com/user-attachments/assets/650f18dc-ca99-4e71-8743-a12b4ae48202" width="400">

## Врач

### Клавиатура врача

Клавиатура врача представляет из себя набор кнопок для удобной навигации по боту, а также список команд для навигации:
Клавиатура врача состоит из следующих кнопок:

* Мои пациенты
* Найти пациента по фамилии

#### Раздел “Мои пациенты”

В раздел “Мои пациенты” пользователь может попасть только при нажатие на кнопку “Мои пациенты”. После этого клавиатура врача меняется на кнопку “Вернуться в меню” и отправляется сообщение с инлайн-кнопками с этапами лечения:

* Начало лечебной программы
* Стимуляция овуляции
* Пункция фолликулов
* Прием на 5 день после пункции
* Перенос эмбрионов
* С результатом ХГЧ
* УЗИ на 21 день

После нажатия на инлайн-кнопку этапа, то кнопки у сообщения меняются и появляются инлайн-кнопки с именами пациентов на этом этапе и последняя в списке инлайн-кнопка “Выбрать другого пациента”.\
Если пользователь нажмет “Выбрать другого пациента”, то снова появятся инлайн-кнопки с этапами.\
Если пользователь нажмет на инлайн-кнопку с именем пациента, то отправится [Сообщение “Карточка пациента”](#сообщение-карточка-пациента).

<img src="https://github.com/user-attachments/assets/f93dfab2-1027-4a30-af3f-088103168d96" width="400">

#### Раздел “Поиск пациента по фамилии”

В раздел “Поиск пациента по фамилии” пользователь может попасть только при нажатие на кнопку “Найти пациента по фамилии”.\
После нажатия на кнопку отправляется сообщение “Введите фамилию по образцу: Иванова”, клавиатура пользователя меняется на кнопку “Вернуться в меню”.\
Если введены некорректные данные или пациента с такой фамилией нет, то отправляется сообщение “Пациент не найден”, клавиатура пользователя с кнопкой “Вернуться в меню” остается.\
Если пациент с введенной фамилией привязан к врачу, то отправляется [Сообщение “Карточка пациента”](#сообщение-карточка-пациента).

<img src="https://github.com/user-attachments/assets/696bfbe7-0c5a-443d-8a0a-e59600935869" width="400">

### Сообщение “Карточка пациента”

Сообщение “Карточка пациента” доступно только врачу и администратору, содержит информацию:

* ФИО пациента
* Номер телефона
* User name Telegram-аккаунта
* Текущий сценарий пациента

![image](https://github.com/user-attachments/assets/c5941ed8-d9a0-4990-9ff6-def5d3a7d739)

## Администратор

### Вход в админа

При заходе в бота, пользователь имеет доступ к единственной кнопке – /start.
После нажатия на кнопку, если Telegram ID пользователя есть в базе данных, появляется клавиатура администратора.

### Клавиатура администратора

Клавиатура администратора представляет из себя набор кнопок для удобной навигации по боту, а также список команд для навигации:
Клавиатура администратора состоит из следующих кнопок:

* Отправить сценарий;
* Изменить сценарий;
* Найти пациента.

#### Раздел “Отправить сценарий”

В раздел “Отправить сценарий” пользователь может попасть только при нажатие на кнопку “Отправить сценарий”.\
После нажатия в чат приходит сообщение “Введите номер телефона пациента в формате +7”, клавиатура пользователя меняется на кнопку “Назад”.\
Если номер не найден или введен с ошибкой, то приходит сообщение “”.\
Если пациент с введенный номер прошел аутентификацию, то в чат присылается сообщением с инлайн-кнопками этапами лечения.\
После нажатия на инлайн-кнопку в чат приходят сообщения всего этапа, в конце сообщение “Введите номер сообщений для отправки”.\
Если отправка происходит успешно, то приходит сообщение “Сообщение успешно отправлено!”.\
Если отправить сообщение не удалось, то приходит сообщение “Не удалось отправить сообщение, попробуйте ещё раз”.\
В чат отправляется сообщение “Отправить ещё сообщение?”, на клавиатуре пользователя две кнопки “Да” и “Нет”.\
Если пользователь нажмет “Да”, то действия повторятся с инлайн-кнопок с этапами лечения.\
Если пользователь нажмет “Нет”, то вернется в основное меню.

<img src="https://github.com/user-attachments/assets/2c194388-d623-487c-a994-e1138b25060c" width="400">

#### Раздел “Изменить сценарий”

В раздел “Изменить сценарий” пользователь может попасть только при нажатие на кнопку “Изменить сценарий”.
После нажатия на кнопку, клавиатура пользователя меняется на клавиатуру Изменения сценария:

* Изменить сценарий у пациента;
* Изменить общий сценарий;
* Вернуться в меню.

<img src="https://github.com/user-attachments/assets/669a7cfe-6b3c-49a1-a5c8-dba94f23b488" width="400">

##### Изменить общий сценарий

В чат присылается сообщением с инлайн-кнопками этапами лечения, клавиатура пользователя меняется на кнопку “Назад.\
После нажатия на инлайн-кнопку в чат приходят сообщения всего этапа, в конце сообщение “Введите номер сообщений для редактирования”.\
После отправки номера сообщения, приходит сообщение “Что именно вы хотите редактировать?” с инлайн-кнопками “Текст”, “Время отправки”.\
Если пользователь нажмет инлайн-кнопку “Текст”, то сообщение с инлайн-кнопками исчезает, бот присылает сообщение, которое будет редактироваться. После присланное от пользователя сообщение заменит этот текст.\
Если пользователь нажмет инлайн-кнопку “Время отправки”, то сообщение с инлайн-кнопками исчезает, бот присылает сообщение-пояснение, как задавать время. После присланное от пользователя сообщение заменит этот текст.\
В чат отправляется сообщение “Хотите изменить ещё одно сообщение?”, на клавиатуре пользователя две кнопки “Да” и “Нет”.\
Если пользователь нажмет “Да”, то действия повторятся с инлайн-кнопок с этапами лечения.\
Если пользователь нажмет “Нет”, то вернется в основное меню.

##### Изменить сценарий у пациента

При нажатие на кнопку “Изменить сценарий у пациент” в чат приходит сообщение “Введите номер телефона пациента в формате +7”, клавиатура пользователя меняется на кнопку “Назад”.
Если номер не найден или введен с ошибкой, то приходит сообщение “”.
Если пациент с введенный номер прошел аутентификацию, то в чат присылается сообщением с инлайн-кнопками этапами лечения и дальше алгоритм, как в [Изменении общего сценария](#изменить-общий-сценарий).

#### Раздел “Поиск пациента”

В раздел “Поиск пациента” пользователь может попасть только при нажатие на кнопку “Найти пациента”. 
После нажатия на кнопку, клавиатура пользователя меняется на клавиатуру Поиска пациента

* Поиск по фамилии;
* Поиск по врачу;
* Поиск по номеру телефона;
* Вернуться в меню.

##### Поиск по фамилии

После нажатия на кнопку “Поиск по фамилии” отправляется сообщение “Введите фамилию по образцу: Иванова”, клавиатура пользователя меняется на кнопку “Вернуться в меню”. 
Если введены некорректные данные или пациента с такой фамилией нет, то отправляется сообщение “Пациент не найден”, клавиатура пользователя с кнопкой “Вернуться в меню” остается.
Если пациент с введенной фамилией прошел аутентификацию в боте, то отправляется [Сообщение “Карточка пациента”](#сообщение-карточка-пациента).

##### Поиск по врачу

После нажатия на кнопку “Поиск по врачу” отправляется сообщение с инлайн-кнопками ФИО врачей, которые прошли аутентификацию в боте, клавиатура пользователя меняется на кнопку “Вернуться в меню”. 
После нажатия ФИО врача сообщение изменяет инлайн-кнопки на этапы лечения:

* Начало лечебной программы;
* Стимуляция овуляции;
* Пункция фолликулов;
* Прием на 5 день после пункции;
* Перенос эмбрионов;
* С результатом ХГЧ;
* УЗИ на 21 день.

После нажатия на инлайн-кнопку этапа, то кнопки у сообщения меняются и появляются инлайн-кнопки с именами пациентов на этом этапе и последняя в списке инлайн-кнопка “Выбрать другого пациента”.
Если пользователь нажмет “Выбрать другого пациента”, то снова появятся инлайн-кнопки с этапами.
Если пользователь нажмет на инлайн-кнопку с именем пациента, то отправится [Сообщение “Карточка пациента”](#сообщение-карточка-пациента).

<img src="https://github.com/user-attachments/assets/18a52210-ad2a-4994-8815-1e3e0526717d" width="400">

##### Поиск по номеру телефона

После нажатия на кнопку “Поиск по номеру телефона” отправляется сообщение “Введите номер телефона пациента в формате +7”, клавиатура пользователя меняется на кнопку “Вернуться в меню”. 
Если введены некорректные данные или пациента с таким номером телефона нет, то отправляется сообщение “Пациент не найден”, клавиатура пользователя с кнопкой “Вернуться в меню” остается.
Если пациент с введенным номером телефона прошел аутентификацию в боте, то отправляется [Сообщение “Карточка пациента”](#сообщение-карточка-пациента).