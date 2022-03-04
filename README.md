# Яндекс.Практикум

# курс Python-разработчик

## студент  Leonid Slavutin

![](https://avatars.githubusercontent.com/u/86873729?s=400&u=79ca75646b1a1eb2fade4f19d435a8ba65a1fe58&v=4)

## Учебный проект sprint_6.  Подписки на авторов.

***

Шаблоны и структура проекта заданы.

Задачи проекта:

* В проект добавлены кастомные страницы ошибок:

    404 page_not_found

    500 server_error

    403 permission_denied_view

    Написан тест, проверяющий, что страница 404 отдает кастомный шаблон.

* С помощью sorl-thumbnail выведены иллюстрации к постам.

    Написаны тесты, которые проверяют работу с изображениями.

* Создана система комментариев

* Добавлены:

    Кеширование главной страницы

    Тестирование кэша

* Добавлена система подписки на авторов.

***

Разворачивание проекта:

Клонировать репозиторий и перейти в его папку в командной строке:

```
git clone https://github.com/coherentus/hw05_final
cd hw05_final
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

Для *nix-систем и MacOS:

```
source venv/bin/activate
```

Для windows-систем:

```
source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

Выполнить миграции:

```
cd yatube
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

Создать суперпользователя Django:

```
python3 manage.py createsuperuser
```

Сам проект и админ-панель по адресам:

```
http://127.0.0.1:8000

http://127.0.0.1:8000/admin
```

***
