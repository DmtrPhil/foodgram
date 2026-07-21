[![Workflow main status](https://github.com/arefiture/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/arefiture/foodgram/actions)

![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white) ![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white) ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white) ![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)

## Описание проекта

Foodgram - учебный проект от Яндекс.Практикум.

Цель этого сайта — дать возможность пользователям создавать и хранить рецепты на онлайн-платформе. Кроме того, можно скачать список продуктов, необходимых для приготовления блюда, просмотреть рецепты друзей и добавить любимые рецепты в список избранных.

## Технологии

- Python 3.9
- Django 3.2.3
- Django REST framework 3.12.4
- JavaScript

## Запуск проекта из образов с Docker Hub

При первом запуске убедитесь, что Docker есть и работает:

```bash
sudo systemctl status docker
```
<details>
    <summary>Что делать, если Docker отсутствует</summary>
    
1. Скачиваем и устанавилваем curl:

    ```bash
    sudo apt update
    sudo apt install curl
    ```

2. С помощью утилиты скачиваем скрипт для установки докера с официального сайта:

    ```bash
    curl -fSL https://get.docker.com -o get-docker.sh 
    ```

3. Запускаем сохраненный скрипт:

    ```bash
    sudo sh ./get-docker.sh
    ```

4. Дополнительно скачиваем утилу Docker Compose:

    ```bash
    sudo apt install docker-compose-plugin 
    ```

5. Проверяем работоспособность Docker:

    ```bash
    sudo systemctl status docker
    ```

</details>

Для запуска необходимо создать папку проекта, например `foodgram` и перейти в нее:

```bash
mkdir foodgram
cd foodgram
```

В папку проекта скачиваем файл из директории infra/ `docker-compose.production.yml` и запускаем его:

```bash
sudo docker compose -f docker-compose.production.yml up -d
```

Далее автоматически скачаются образы, произойдет создание и включение контейнеров и объедение их в одну сеть.

## Настройки переменных окружения (о том, как заполнить env)

В корне проекта следует создать файл .env и заполнить по образу из файла .env.example

## После запуска: Миграции, сбор статистики

После запуска необходимо выполнить сбор статистики и миграции бэкенда.
Статистика фронтенда собирается во время запуска контейнера, после чего он останавливается. 

```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate

sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic

sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```

После этого проект будет доступен по адресам:
```
localhost
```

## На случай, если нужно наполнение тегами и ингредиентами:

После первого развёртывания для работы с рецептами нужны будут теги и ингредиенты.
Предусмотрено начальное наполнение этих таблиц в базе командой:
```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py data_loader
```
Если среди перечисленных ингредиентов и тегов нет нужных - обратитесь к админу сайта.

## Остановка проекта:

```bash
sudo docker compose -f docker-compose.production.yml down
```

## Автор:
[DmtrPhil](https://github.com/DntrPhil)