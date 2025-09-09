from django.contrib import admin
from .models import Question, AnswerOption

admin.site.register(Question)
admin.site.register(AnswerOption)
