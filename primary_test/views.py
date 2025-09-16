from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.urls import reverse
from reportlab.pdfgen import canvas
from io import BytesIO
from django.core.files.base import ContentFile
from django.db.models import Sum
from diagnostic.models import *
from .models import *
from .forms import *
import math, random
from collections import Counter
from django.shortcuts import get_object_or_404

# Константа: количество вопросов на одну страницу
QUESTIONS_PER_PAGE = 5

@login_required
def block1_test_view(request, page=1):
    block_obj = get_object_or_404(Block, number=1)  # Получаем объект первого блока
    all_questions = list(Question.objects.filter(block=block_obj))  # Все вопросы первого блока
    random.shuffle(all_questions)  # Перемешиваем вопросы

    # Вычисляем общее число страниц
    total_pages = math.ceil(len(all_questions) / QUESTIONS_PER_PAGE)

    # Определяем диапазон текущих вопросов
    start_idx = (page - 1) * QUESTIONS_PER_PAGE
    end_idx = min(start_idx + QUESTIONS_PER_PAGE, len(all_questions))
    current_questions = all_questions[start_idx:end_idx]

    # Создаем форму для текущего набора вопросов
    form = PrimaryDiagnosticForm(questions=current_questions)

    if request.method == 'POST':
        form = PrimaryDiagnosticForm(request.POST, questions=current_questions)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            process_block_answers(cleaned_data, block_obj, request.user)

            # Проверяем, можем ли перейти дальше
            next_page = page + 1
            if next_page <= total_pages:
                return redirect(reverse('primary_test:block1_test', args=(next_page,)))
            else:
                return redirect(reverse('primary_test:block2_test'))

    context = {
        'form': form,
        'page': page,
        'total_pages': total_pages,
        'current_questions': current_questions
    }
    return render(request, 'primary_test/block1_test.html', context)

@login_required
def block2_test_view(request):
    block_obj = get_object_or_404(Block, number=2)  # Получаем объект второго блока
    all_questions = list(Question.objects.filter(block=block_obj))  # Все вопросы второго блока
    random.shuffle(all_questions)  # Перемешиваем вопросы

    # Формируем форму сразу для всех вопросов
    form = PrimaryDiagnosticForm(questions=all_questions)

    if request.method == 'POST':
        form = PrimaryDiagnosticForm(request.POST, questions=all_questions)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            process_block_answers(cleaned_data, block_obj, request.user)
            return redirect(reverse('primary_test:diagnostic_results'))

    context = {
        'form': form,
        'questions': all_questions
    }
    return render(request, 'primary_test/block2_test.html', context)

def process_block_answers(cleaned_data, block_obj, user):
    """
    Сохранение результатов тестирования.
    """
    if block_obj.number == 1:
        # Обрабатываем результаты первого блока (оценка знаний)
        results = {}
        for key, val in cleaned_data.items():
            question_id = int(key.split('_')[-1])
            option_id = int(val)
            answer_option = AnswerOption.objects.get(pk=option_id)
            results[question_id] = {
                'selected_answer': answer_option,
                'is_correct': answer_option.is_correct
            }
        
        # Сохраняем результаты
        diagnostic_result = DiagnosticResult.objects.create(
            user=user,
            block_number=block_obj.number
        )
        for qid, data in results.items():
            AnswerRecord.objects.create(
                question_id=qid,
                selected_answer=data['selected_answer'],
                is_correct=data['is_correct'],
                diagnostic_result=diagnostic_result
            )
    elif block_obj.number == 2:
        # Обрабатываем результаты второго блока (предпочтения)
        responses = [
            {'choice': cleaned_data[key].split('_')[-1]}
            for key in cleaned_data.keys()
        ]
        preference, counts = determine_preferences(responses)
        diagnostic_result = DiagnosticResult.objects.create(
            user=user,
            block_number=block_obj.number,
            preference=preference
        )
        diagnostic_result.save()

def determine_preferences(responses):
    """
    Анализируем предпочтения пользователя.
    """
    counts = {"a": 0, "б": 0, "в": 0, "г": 0, "д": 0}
    for resp in responses:
        choice = resp["choice"]
        counts[choice] += 1
    max_choice = max(counts, key=lambda k: counts[k])
    preferences_map = {
        "a": "Кибербезопасность",
        "б": "Компьютерная графика и дизайн",
        "в": "Игровая разработка",
        "г": "Программирование",
        "д": "Инженерия в IT"
    }
    return preferences_map[max_choice], counts

def save_progress(user, block_number, results):
    """Сохранение результатов в БД и формирование отчета."""
    diagnostic_result = DiagnosticResult.objects.create(
        user=user,
        block_number=block_number
    )
    if isinstance(results, dict):
        # Первая часть (блок оценки знаний)
        for qid, data in results.items():
            AnswerRecord.objects.create(
                question_id=qid,
                selected_answer=data['selected_answer'],
                is_correct=data['is_correct'],
                diagnostic_result=diagnostic_result
            )
    else:
        # Вторая часть (выбор предпочтений)
        preference, counts = results
        diagnostic_result.preference = preference
        diagnostic_result.save()

    # Генерация отчёта
    generate_pdf_report(user)

def diagnostic_results(request):
    """
    Итоговая страница диагностики.
    """
    results = DiagnosticResult.objects.filter(user=request.user).order_by('-completed_at')
    scores = []
    for result in results:
        if hasattr(result, 'preference'):
            scores.append({
                'block_number': result.block_number,
                'preference': result.preference
            })
        else:
            answers = result.answers.all()
            percent_correct = calculate_percent_correct(answers)
            scores.append({
                'block_number': result.block_number,
                'percent_correct': percent_correct
            })
    overall_score = sum([score['percent_correct'] for score in scores if 'percent_correct' in score]) / len([score for score in scores if 'percent_correct' in score])
    context = {
        'scores': scores,
        'overall_score': overall_score
    }
    return render(request, 'results.html', context)

def calculate_percent_correct(answers):
    """Расчёт процентного соотношения правильных ответов."""
    total = len(answers)
    correct_count = sum([1 for ans in answers if ans.is_correct])
    return (correct_count / total) * 100

def generate_pdf_report(user):
    """
    Создаем отчёт в формате PDF для пользователя.
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica", 12)
    p.drawString(100, 800, f"Отчет для пользователя: {user.username}")
    p.showPage()
    p.save()
    filename = f'{user.username}_report.pdf'
    user.profile.report_file.save(filename, ContentFile(buffer.getvalue()))
    buffer.close()

@login_required
def download_report(request, username):
    """
    Скачивание PDF-отчета.
    """
    profile = UserProfile.objects.get(user__username=username)
    response = FileResponse(profile.report_file.open(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename={profile.report_file.name}'
    return response

def select_answers(request, question_id):
    question = Question.objects.get(id=question_id)
    if request.method == 'POST':
        form = MultiAnswerForm(question, request.POST)
        if form.is_valid():
            selected_options = form.cleaned_data['options']
            # Обработаем полученные данные (например, сохраним отметки)
            for option in selected_options:
                # Логика сохранения отметок
                pass
            return redirect('/success/')
    else:
        form = MultiAnswerForm(question)
    return render(request, 'select_answers.html', {'form': form})