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
import math, random
from django.db.models import Subquery, OuterRef
from django.shortcuts import get_object_or_404

# Константа: количество вопросов на одну страницу
QUESTIONS_PER_PAGE = 5

@login_required
def block1_test_view(request, page=1):
    block_obj = get_object_or_404(Block, number=1)  # Получаем объект первого блока
    session_key = f"questions_order_{block_obj.number}_{request.user.id}"

    # Если порядок вопросов ещё не зафиксирован, перемешиваем и сохраняем
    if session_key not in request.session:
        all_questions = list(Question.objects.filter(block=block_obj))
        random.shuffle(all_questions)
        request.session[session_key] = [q.id for q in all_questions]  # Сохраняем только идентификаторы

    # Забираем упорядоченные вопросы из сессии
    ordered_questions_ids = request.session[session_key]

    # Создаем запрос с предварительным упорядочиванием
    ordered_questions = Question.objects.filter(id__in=ordered_questions_ids).order_by()

    # Вычисляем общее число страниц
    total_pages = math.ceil(len(ordered_questions) / QUESTIONS_PER_PAGE)

    # Определяем диапазон текущих вопросов
    start_idx = (page - 1) * QUESTIONS_PER_PAGE
    end_idx = min(start_idx + QUESTIONS_PER_PAGE, len(ordered_questions))
    current_questions = ordered_questions[start_idx:end_idx]

    # Получаем выбранные ответы из сессии
    saved_answers = request.session.get(f'saved_answers_{block_obj.number}', {})

    # Подготовим готовые данные для шаблона
    prepared_questions = []
    for question in current_questions:
        options = []
        for option in question.answeroption_set.all():
            checked = str(saved_answers.get(str(question.id), '')) == str(option.id)
            options.append((option, checked))
        prepared_questions.append((question, options))

    # Обрабатываем форму
    if request.method == 'POST':
        cleaned_data = {}  # Сбор данных из формы
        for key, value in request.POST.items():
            if key.startswith('question_'):
                question_id = int(key.split('_')[1])
                cleaned_data[f'question_{question_id}'] = value

        # Сохраняем результаты
        process_block_answers(cleaned_data, block_obj, request.user)

        # Завершаем первый блок и переходим на второй
        if page == total_pages:
            return redirect(reverse('primary_test:block2_test'))
        else:
            next_page = page + 1
            return redirect(reverse('primary_test:block1_test', args=(next_page,)))

    context = {
        'prepared_questions': prepared_questions,
        'page': page,
        'total_pages': total_pages
    }
    return render(request, 'primary_test/block1_test.html', context)

@login_required
def block2_test_view(request):
    block_obj = get_object_or_404(Block, number=2)  # Получаем объект второго блока
    session_key = f"saved_answers_{block_obj.number}_{request.user.id}"

    # Получаем все вопросы второго блока
    all_questions = list(Question.objects.filter(block=block_obj))

    # Получаем выбранные ответы из сессии
    saved_answers = request.session.get(session_key, {})

    # Подготовим готовые данные для шаблона
    prepared_questions = []
    for question in all_questions:
        options = []
        for option in question.answeroption_set.all():
            checked = str(saved_answers.get(str(question.id), '')) == str(option.id)
            options.append((option, checked))
        prepared_questions.append((question, options))

    # Обрабатываем форму
    if request.method == 'POST':
        cleaned_data = {}  # Сбор данных из формы
        for key, value in request.POST.items():
            if key.startswith('question_'):
                question_id = int(key.split('_')[1])
                cleaned_data[f'question_{question_id}'] = value

        # Сохраняем результаты
        process_block_answers(cleaned_data, block_obj, request.user)

        # Переходим на страницу результатов
        return redirect(reverse('primary_test:diagnostic_results'))

    context = {
        'prepared_questions': prepared_questions
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
            {'choice': cleaned_data[key].split('_')[-1]}  # получаем ID выбранного варианта
            for key in cleaned_data.keys() if key.startswith('question_')
        ]
        recommendation, counts = determine_preferences(responses)
        diagnostic_result = DiagnosticResult.objects.create(
            user=user,
            block_number=block_obj.number,
            preference=recommendation
        )
        diagnostic_result.save()

def determine_preferences(responses):
    """
    Анализируем предпочтения пользователя.
    """
    # Собираем ID популярных вариантов ответов
    popular_options = {}
    for resp in responses:
        choice = resp["choice"]  # ID варианта ответа
        if choice in popular_options:
            popular_options[choice] += 1
        else:
            popular_options[choice] = 1

    # Найдем самый популярный вариант
    most_popular_option_id = max(popular_options, key=popular_options.get)

    # Определим категорию на основе популярного варианта
    categories = {
        1: "Кибербезопасность",
        2: "Компьютерная графика и дизайн",
        3: "Игровая разработка",
        4: "Программирование",
        5: "Инженерия в IT"
    }

    recommendation = categories.get(int(most_popular_option_id), "Неопределенно")
    return recommendation, popular_options

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

@login_required
def diagnostic_results(request):
    """
    Итоговая страница диагностики.
    """
    results = DiagnosticResult.objects.filter(user=request.user).order_by('-created_at')
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

    # Расчёт общего среднего балла для блока 1
    percent_scores = [score for score in scores if 'percent_correct' in score]
    if percent_scores:
        overall_score = sum(score['percent_correct'] for score in percent_scores) / len(percent_scores)
    else:
        overall_score = 0  # Если нет оценок, средний балл считаем нулевым

    # Расчёт предпочтения для блока 2
    second_block_results = [score for score in scores if 'preference' in score]
    if second_block_results:
        second_block_preference = second_block_results[0]['preference']
    else:
        second_block_preference = ""

    # Проверяем, есть ли результаты тестирования
    has_results = bool(scores)

    context = {
        'scores': scores,
        'overall_score': overall_score,
        'second_block_preference': second_block_preference,
        'has_results': has_results
    }
    return render(request, 'primary_test/results.html', context)

def calculate_percent_correct(answers):
    """Расчёт процентного соотношения правильных ответов."""
    total = len(answers)
    correct_count = sum([1 for ans in answers if ans.is_correct])
    return (correct_count / total) * 100 if total > 0 else 0


def calculate_percent_correct(answers):
    """Расчёт процентного соотношения правильных ответов."""
    total = len(answers)
    correct_count = sum([1 for ans in answers if ans.is_correct])
    return (correct_count / total) * 100 if total > 0 else 0

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

@login_required
def reset_session(request):
    """
    Очищает сессию перед началом нового теста.
    """
    request.session.clear()
    return redirect(reverse('primary_test:block1_test', args=(1,)))