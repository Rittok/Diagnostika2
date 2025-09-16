from django.contrib import admin
from .models import Question, AnswerOption, DiagnosticResult, AnswerRecord, Block
from diagnostic.models import School, ClassLevel

# Настройки для блока вопросов
@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('number', 'description')
    ordering = ('number',)

# Настройки для вопросов с inline-редактированием вариантов ответов
class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 3  # Кол-во пустых полей для новых вариантов ответов

@admin.register(Question)
class QuestionWithAnswersAdmin(admin.ModelAdmin):
    inlines = [AnswerOptionInline]
    list_display = ('id', 'text', 'test_type', 'block')
    search_fields = ('text',)
    list_filter = ('test_type', 'block')
    ordering = ('block', 'id')

# Настройки для вариантов ответов
@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'option_text', 'is_correct')
    list_filter = ('question', 'is_correct')
    search_fields = ('option_text',)
    ordering = ('question',)

# Настройки для остальных моделей
@admin.register(DiagnosticResult)
class DiagnosticResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'block_number', 'created_at', 'preference')
    list_filter = ('block_number', 'created_at')
    search_fields = ('user__username', 'preference')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

@admin.register(AnswerRecord)
class AnswerRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'selected_answer', 'is_correct', 'diagnostic_result')
    list_filter = ('is_correct', 'question')
    search_fields = ('question__text', 'selected_answer__option_text')
    ordering = ('question',)

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(ClassLevel)
class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ('level',)
    list_filter = ('level',)