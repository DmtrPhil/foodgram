[![Workflow main status](https://github.com/DmtrPhi/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/DmtrPhil/foodgram/actions)

![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white) ![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white) ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white) ![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)

# Foodgram

Сервис для публикации и хранения кулинарных рецептов. Пользователи могут создавать собственные рецепты, добавлять чужие в избранное, формировать список покупок и подписываться на других авторов.

## Стек технологий

- **Backend:** Python 3.9, Django 3.2.3, Django REST Framework 3.12.4
- **Frontend:** JavaScript
- **База данных:** PostgreSQL
- **Контейнеризация:** Docker, Docker Compose
- **CI/CD:** GitHub Actions

## Установка и запуск

### Требования

- Установленный Docker и Docker Compose

### Инструкция

1. Склонируйте репозиторий:

git clone https://github.com/DmtrPhil/foodgram.git
cd foodgram

2. Создайте файл .env в корне проекта и заполните его по примеру из .env.example:

POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_db
DB_NAME=your_db
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your_secret_key

3. Перейдите в папку с файлом docker-compose.prodaction.yml, что бы получить возможность запустить контейнеры

cd infra/

4. Запустите контейнеры:

sudo docker compose docker-compose.production.yml up -d

5. Выполните миграции и соберите статику:

sudo docker compose docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/

6. Загрузите ингредиенты:

sudo docker compose docker-compose.production.yml exec backend python manage.py load_ingredients

7. Проект будет доступен по адресу:

http://localhost

### Остановка проекта

sudo docker compose docker-compose.production.yml down

## API Документация

После запуска проекта документация доступна по адресу:

http://localhost/api/docs/

## Основные возможности

- Регистрация и авторизация пользователей с выдачей токена
- Управление рецептами: создание, редактирование, удаление
- Избранное: добавление рецептов в список избранного
- Список покупок: формирование и скачивание списка ингредиентов для выбранных рецептов
- Подписки: возможность подписываться на других авторов и просматривать их рецепты
- Короткие ссылки: генерация сокращённых ссылок на рецепты
- Фильтрация: поиск рецептов по автору, тегам, избранному и списку покупок
- Админ-панель: полностью руссифицированная панель администратора

## Тестирование

Для проверки функциональности API импортируйте коллекцию Postman из директории postman_collection/.

## Автор

[DmtrPhil](https://github.com/DmtrPhil)