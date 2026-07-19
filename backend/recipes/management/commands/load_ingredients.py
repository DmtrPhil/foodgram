import json
from pathlib import Path

from django.db import connection
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из JSON в БД'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            nargs='?',
            default='../data/ingredients.json',
            help='Путь к JSON-файлу'
        )

    def handle(self, *args, **options):
        file_path = Path(options['file_path'])
        if not file_path.exists():
            self.stderr.write(
                self.style.ERROR(f'Файл не найден: {file_path}')
            )
            return
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='recipes_ingredient';")
        with open(file_path, 'r', encoding='utf-8') as json_file:
            ingredients_data = json.load(json_file)
        created_count = 0
        skipped_count = 0
        for ingredient_item in ingredients_data:
            ingredient_name = ingredient_item.get('name', '').strip()
            measurement_unit = ingredient_item.get('measurement_unit', '').strip()
            if not ingredient_name:
                skipped_count += 1
                continue
            ingredient, is_created = Ingredient.objects.get_or_create(
                name=ingredient_name,
                measurement_unit=measurement_unit
            )
            if is_created:
                created_count += 1
            else:
                skipped_count += 1
        self.stdout.write(
            self.style.SUCCESS(
                f'Загрузка завершена!'
                f'\n   Создано: {created_count}'
                f'\n   Пропущено: {skipped_count}'
                f'\n   Всего ингредиентов в БД: {Ingredient.objects.count()}'
            )
        )