from django.db import models
from django.contrib.auth.models import User

class School(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class ClassLevel(models.Model):
    level = models.IntegerField()

    def __str__(self):
        return f'{self.level}'

    
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



