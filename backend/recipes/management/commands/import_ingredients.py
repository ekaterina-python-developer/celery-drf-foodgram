import csv
import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Загрузка ингредиентов из JSON или CSV файла."""

    help = 'Загружает ингредиенты из указанного файла (JSON или CSV).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/ingredients.json',
            help='Путь к файлу с ингредиентами (JSON или CSV).',
        )

    def handle(self, *args, **options):
        file_path = options['file']

        if not file_path.endswith(('.json', '.csv')):
            return self.stderr.write('Файл должен быть JSON или CSV.')

        try:
            with open(file_path, encoding='utf-8') as file:
                items = self._load_items(file, file_path)
        except FileNotFoundError:
            return self.stderr.write(f'Файл "{file_path}" не найден.')
        except json.JSONDecodeError:
            return self.stderr.write(
                f'Ошибка чтения JSON-файла "{file_path}".')

        created_count = sum(
            1 for name, unit in items
            if Ingredient.objects.get_or_create(
                name=name.strip(), measurement_unit=unit.strip()
            )[1]
        )

        self.stdout.write(
            self.style.SUCCESS(f'Загружено {created_count} ингредиентов.')
        )

    def _load_items(self, file, file_path):
        """Возвращает список ингредиентов из JSON или CSV файла."""
        if file_path.endswith('.json'):
            data = json.load(file)
            return [(i['name'], i['measurement_unit']) for i in data]
        return [row for row in csv.reader(file) if len(row) >= 2]
