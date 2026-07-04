# Язык программирования: LevelScript!

[![LEVEL](https://levelschool.tilda.ws/favicon.ico) Школа программирования LEVEL](https://levelschool.tilda.ws/)

[![Хабр](https://habr.com/favicon.ico) Статья на Habr](https://habr.com/ru/articles/1025306/)

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/LVL-SCHOOL/LevelScript)

Школа программирования LEVEL представляет язык программирования LevelScript! 
Данный язык программирования рассчитан на детей от 8 до 16 лет

### Философия языка

LevelScript сочетает в себе интуитивно понятный синтаксис, который читается как обычный текст, и при этом обладает выразительной мощью грамматических конструкций. 
На нём можно создавать что угодно: от простых игр и Telegram-ботов до полноценных серверов!

[Примеры кода](./examples)


## Сырой запуск:


### Windows
```
py -m venv .venv 
.venv/Scripts/activate
set PYTHONPATH=%CD%
pip install -r requirements.txt
py lvl.py --run hello_world.lvl
```

### Linux/Mac

#### ВАЖНО! На маке могут потребоваться "танцы с бубном!"

```
py -m venv .venv 
.venv/Scripts/activate
export PYTHONPATH=$(pwd)
pip install -r requirements.txt
py lvl.py --run hello_world.lvl
```

## Сборка(Windows):

```
build.bat
```

### Запуск exe

```
lvl.exe --run hello_world.lvl
```

Если Вы увидете такой вывод: 

![img.png](docs/img_hi_world.png)

Значит LevelScript работает штатно!

### Конфигурация

Для настройки LevelScript создайте файл lvl_config.env

## Пример кода

![img.png](docs/img_code_from_vs_code.png)


## Пример обработки ошибок

----
Язык понимает, что вы имели в виду, даже когда вы ошибаетесь!
![img.png](docs/img5.png)
![img.png](docs/img7.png)

----
Не переданные аргументы
![img.png](docs/img8.png)
![img.png](docs/img9.png)

----
Одинаковые аргументы
![img.png](docs/img10.png)
![img.png](docs/img11.png)

----
Двойное ожидание фоновой задачи
![img.png](docs/img12.png)
![img.png](docs/img13.png)

----
Хорошо понимает контекст ошибки. Показывает конкретное выражение
![img.png](docs/img14.png)
![img.png](docs/img15.png)

----
В рамках выражений, тоже хорошо понимает, что сломалось
![img.png](docs/img16.png)
![img.png](docs/img17.png)
