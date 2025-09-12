from django.db import models
from django.contrib.auth.models import User
from .models import *

class Block(models.Model):
    number = models.PositiveIntegerField(unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Блок {self.number}"

TEST_TYPES = (
    ('primary', 'Первичная диагностика'),  # Первичный ключ, читаемое имя
    ('interim', 'Промежуточная диагностика'),
    ('final', 'Итоговая диагностика'),
)

class Question(models.Model):
    text = models.CharField(max_length=255, db_index=True)
    test_type = models.CharField(max_length=50, choices=TEST_TYPES)  # Ограничиваем выбор этими типами
    block = models.ForeignKey(Block, on_delete=models.CASCADE, default=1)
    options = models.ManyToManyField('AnswerOption', related_name='linked_questions')

    def __str__(self):
        return self.text[:50]

class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    option_text = models.CharField(max_length=255, verbose_name="Вариант ответа")
    is_correct = models.BooleanField(default=False, verbose_name="Правильный ответ?")

    def __str__(self):
        return self.option_text

class DiagnosticResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    block_number = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)  # Добавлено поле created_at
    preference = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Результат для пользователя {self.user}, блок {self.block_number}"

class AnswerRecord(models.Model):    
    question = models.ForeignKey(Question, on_delete=models.CASCADE)    
    selected_answer = models.ForeignKey(AnswerOption, on_delete=models.SET_NULL, null=True)    
    is_correct = models.BooleanField(null=True)    
    diagnostic_result = models.ForeignKey(DiagnosticResult, 
                                          related_name="answers", on_delete=models.CASCADE)