from random import sample
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponseRedirect
from django.urls import reverse
from reportlab.pdfgen import canvas
from io import BytesIO
from django.core.files.base import ContentFile
from django.db.models import Sum
from django.views.generic import ListView
from diagnostic.models import *
from .models import *
from .forms import *
import math, random
from collections import Counter

BLOCK_SIZE = 5
@login_required
def primary_diagnostic(request):
    """
    Начальная точка прохождения теста.
    Отправляет пользователя на первый блок.
    """
    total_questions = Question.objects.count()
    num_blocks = math.ceil(total_questions / BLOCK_SIZE)
    first_block_questions = _get_random_questions(BLOCK_SIZE)
    request.session['current_block'] = 1
    request.session['num_blocks'] = num_blocks
    return redirect('block_test', block_num=1)

def _get_random_questions(block_size):
    """
    Возвращает список случайных вопросов из указанного блока.
    """
    # Предположим, что текущий блок хранится в сессии
    current_block = request.session.get('current_block', 1)
    block = Block.objects.get(number=current_block)
    questions = list(block.questions.all())  # Берём вопросы только из нужного блока
    return random.sample(questions, min(len(questions), block_size))  # Выбор случайных вопросов

def block_test_view(request, block_num):
    """
    Страница для отдельных блоков теста.
    """
    try:
        current_block = int(block_num)
        session_block = request.session.get('current_block', None)
        num_blocks = request.session.get('num_blocks', None)

        if num_blocks is None:
            raise ValueError("Количество блоков не задано!")

        if not session_block or session_block != current_block:
            raise ValueError("Неверная попытка доступа.")

        next_block = current_block + 1
        prev_block = current_block - 1
        last_block = current_block == num_blocks

        if last_block:
            next_url = 'diagnostic_results'
        elif next_block <= num_blocks:
            next_url = reverse('block_test', args=(next_block,))
        else:
            next_url = None

        if request.method == 'POST':
            form = PrimaryDiagnosticForm(request.POST)
            if form.is_valid():
                results = process_block_answers(form.cleaned_data, current_block)
                save_progress(request.user, current_block, results)
                return HttpResponseRedirect(next_url)
        else:
            questions = _get_random_questions(BLOCK_SIZE)
            form = PrimaryDiagnosticForm(questions=questions)

        context = {
            'form': form,
            'prev_block': prev_block if prev_block > 0 else None,
            'next_block': next_block if next_block <= num_blocks else None,
            'last_block': last_block,
            'current_block': current_block,
            'num_blocks': num_blocks
        }
        return render(request, 'block_test.html', context)
    except Exception as e:
        print(e)
        return HttpResponseRedirect('/diagnostic/login')
def process_block_answers(cleaned_data, block_number):
    """
    Обработка ответов в зависимости от номера блока.
    """
    if block_number == 1:
        answers = {}
        for key, val in cleaned_data.items():
            question_id = int(key.split('_')[-1])
            option_id = int(val)
            answer_option = AnswerOption.objects.get(pk=option_id)
            answers[question_id] = {
                'selected_answer': answer_option,
                'is_correct': answer_option.is_correct
            }
        return answers
    elif block_number == 2:
        responses = [
            {'choice': cleaned_data[key].split('_')[-1]}
            for key in cleaned_data.keys()
        ]
        return
    

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
    """
    Сохранение результатов в БД и формирование отчета.
    """
    diagnostic_result = DiagnosticResult.objects.create(
        user=user,
        block_number=block_number
    )
    if isinstance(results, dict):
        # Блок 1 (стандартная обработка)
        for qid, data in results.items():
            AnswerRecord.objects.create(
                question_id=qid,
                selected_answer=data['selected_answer'],
                is_correct=data['is_correct'],
                diagnostic_result=diagnostic_result
            )
    else:
        # Блок 2 (определение предпочтений)
        preference, counts = results
        diagnostic_result.preference = preference
        diagnostic_result.save()

    # Формирование файла отчёта
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
    """
    Расчёт процентов верных ответов.
    """
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