from django.db import models
from django.contrib.auth.models import User

class School(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class ClassLevel(models.Model):
    level = models.IntegerField()
    letter = models.CharField(max_length=1)

    def __str__(self):
        return f"{self.level}{self.letter}"

class Question(models.Model):
    text = models.TextField()
    test_type = models.CharField(
        max_length=20,
        choices=[
            ('primary', 'Первичная диагностика'),
            ('interim', 'Промежуточная диагностика'),
            ('final', 'Итоговая диагностика')
        ]
    )

    def __str__(self):
        return self.text[:50]

class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    option_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.option_text

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100) 
    last_name = models.CharField(max_length=100)
    school = models.ForeignKey(School, on_delete=models.PROTECT)
    class_level = models.ForeignKey(ClassLevel, on_delete=models.PROTECT)
    class_letter = models.CharField(max_length=1)
    primary_diagnosis_score = models.FloatField(null=True, blank=True)
    interim_diagnosis_score = models.FloatField(null=True, blank=True)
    final_diagnosis_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
