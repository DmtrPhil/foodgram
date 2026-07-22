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
        created_count = 0
        updated_count = 0
        skipped_count = 0
        for ingredient_item in ingredients_data:
            ingredient_name = ingredient_item.get('name', '').strip()
            measurement_unit = ingredient_item.get('measurement_unit', '').strip()
            if not ingredient_name or not measurement_unit:
                skipped_count += 1
                continue
            _, created = Ingredient.objects.update_or_create(
                name=ingredient_name,
                defaults={'measurement_unit': measurement_unit}
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        self.stdout.write(
            self.style.SUCCESS(
                f'Загрузка завершена!'
                f'\n   Создано новых: {created_count}'
                f'\n   Обновлено существующих: {updated_count}'
                f'\n   Пропущено: {skipped_count}'
                f'\n   Всего ингредиентов в БД: {Ingredient.objects.count()}'
            )
        )