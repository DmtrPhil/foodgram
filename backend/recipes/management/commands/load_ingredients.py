import json
from pathlib import Path

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из JSON в БД с использованием ORM'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            nargs='?',
            default='recipes/data/ingredients.json',
            help='Путь к JSON-файлу'
        )

    def handle(self, *args, **options):
        file_path = Path(options['file_path'])
        if not file_path.exists():
            self.stderr.write(
                self.style.ERROR(f'Файл не найден: {file_path}')
            )
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as json_file:
                ingredients_data = json.load(json_file)
        except json.JSONDecodeError as e:
            self.stderr.write(
                self.style.ERROR(f'Ошибка в JSON: {e}')
            )
            return
        ingredients_to_create = []
        skipped_count = 0
        for ingredient_item in ingredients_data:
            ingredient_name = ingredient_item.get('name', '').strip()
            measurement_unit = ingredient_item.get(
                'measurement_unit', ''
            ).strip()
            if not ingredient_name or not measurement_unit:
                skipped_count += 1
                continue
            ingredients_to_create.append(
                Ingredient(
                    name=ingredient_name,
                    measurement_unit=measurement_unit
                )
            )
        created_count = 0
        if ingredients_to_create:
            created_count = Ingredient.objects.bulk_create(
                ingredients_to_create,
                ignore_conflicts=True,
            )
            created_count = len(created_count)

        self.stdout.write(
            self.style.SUCCESS(
                f'Загрузка завершена!'
                f'\n   Создано: {created_count}'
                f'\n   Пропущено (невалидные или дубли): {skipped_count}'
                f'\n   Всего ингредиентов в БД: {Ingredient.objects.count()}'
            )
        )
