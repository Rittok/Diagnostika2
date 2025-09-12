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

QUESTIONS_PER_PAGE = 5  # Количество вопросов на одной странице

@login_required
def block1_test_view(request, page=1):
    block_obj = get_object_or_404(Block, number=1)  # Первый блок
    all_questions = Question.objects.filter(block=block_obj)
    random.shuffle(list(all_questions))
    
    # Всего 15 вопросов, показываем по 5 на страницу
    QUESTIONS_PER_PAGE = 5
    total_questions = len(all_questions)
    pages = math.ceil(total_questions / QUESTIONS_PER_PAGE)
    
    # Текущие вопросы
    start_question = (page - 1) * QUESTIONS_PER_PAGE
    end_question = min(start_question + QUESTIONS_PER_PAGE, total_questions)
    displayed_questions = all_questions[start_question:end_question]
    
    # Формируем форму
    form = PrimaryDiagnosticForm(questions=displayed_questions)
    
    if request.method == 'POST':
        form = PrimaryDiagnosticForm(request.POST, questions=displayed_questions)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            process_block_answers(cleaned_data, block_obj)
            
            # Переход на следующую страницу
            next_page = page + 1
            if next_page <= pages:
                return redirect(reverse('primary_test:block1_test', kwargs={'page': next_page}))
            else:
                return redirect(reverse('primary_test:block2_test'))  # Переход ко второму блоку
    
    context = {
        'form': form,
        'page': page,
        'pages': pages,
        'displayed_questions': displayed_questions
    }
    return render(request, 'primary_test/block1_test.html', context)

@login_required
def block2_test_view(request):
    block_obj = get_object_or_404(Block, number=2)  # Второй блок
    all_questions = Question.objects.filter(block=block_obj)
    random.shuffle(all_questions)
    
    # Всё разом, ведь вопросов всего пять
    displayed_questions = all_questions
    
    form = PrimaryDiagnosticForm(questions=displayed_questions)
    
    if request.method == 'POST':
        form = PrimaryDiagnosticForm(request.POST, questions=displayed_questions)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            process_block_answers(cleaned_data, block_obj)
            return redirect(reverse('primary_test:diagnostic_results'))  # Переход к результатам
    
    context = {
        'form': form,
        'displayed_questions': displayed_questions
    }
    return render(request, 'block2_test.html', context)
    
def process_block_answers(cleaned_data, block_obj, user):
    """
    Обработка ответов пользователя и сохранение результатов.
    """
    if block_obj.number == 1:
        # Обработка первого блока (оценка знаний)
        results = {}
        for key, val in cleaned_data.items():
            question_id = int(key.split('_')[-1])
            option_id = int(val)
            answer_option = AnswerOption.objects.get(pk=option_id)
            results[question_id] = {
                'selected_answer': answer_option,
                'is_correct': answer_option.is_correct
            }
        save_progress(user, block_obj.number, results)
    elif block_obj.number == 2:
        # Обработка второго блока (выбор предпочтений)
        responses = [
            {'choice': cleaned_data[key].split('_')[-1]} 
            for key in cleaned_data.keys()
        ]
        preference, counts = determine_preferences(responses)
        save_progress(user, block_obj.number, (preference, counts))

def determine_preferences(responses):
    """
    Определение предпочитаемых направлений.
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