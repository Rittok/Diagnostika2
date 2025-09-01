from django.core.management.base import BaseCommand
from ...models import *

class Command(BaseCommand):
    help = 'Заполняет базу данных начальными данными'

    def handle(self, *args, **options):
        # Добавление школ
        schools = ['Школа №1', 'Школа №2']
        for s in schools:
            School.objects.get_or_create(name=s)
        
        # Добавление уровней классов
        levels = [7, 8, 9]
        for l in levels:
            ClassLevel.objects.get_or_create(level=l)
        

        print("База данных успешно заполнена.")