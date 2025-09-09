from random import sample
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.conf import settings
from .forms import *
from .models import *
BLOCK_SIZE = 5  # Количество вопросов в одном блоке

def start_primary_diagnostic(request):    
    """    Начало первичного диагностического теста.    """    
    total_questions = Question.objects.count()    
    num_blocks = total_questions // BLOCK_SIZE + bool(total_questions % BLOCK_SIZE)    
    first_block_questions = _get_random_questions(BLOCK_SIZE)    
    current_block = 1    
    request.session['block'] = current_block    
    request.session['num_blocks'] = num_blocks    
    return redirect('block_test', block_num=current_block)
def get_random_questions(num_questions):    
    """    Возвращает список случайных вопросов заданного размера.    """    
    all_questions = list(Question.objects.all())    
    return sample(all_questions, min(len(all_questions), num_questions))
def block_test_view(request, block_num):    
    """    Представление для конкретного блока теста.    """    
    try:        
        current_block = int(block_num)        
        session_block = request.session.get('block', None)        
        num_blocks = request.session.get('num_blocks', None)        
        if not session_block or session_block != current_block:            
            raise ValidationError("Invalid access")        
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
            form = BlockTestForm(request.POST)            
            if form.is_valid():                
                results = process_block_answers(form.cleaned_data)                
                save_progress(request.user, current_block, results)                
                return HttpResponseRedirect(next_url)        
            else:            
                questions = _get_random_questions(BLOCK_SIZE)           
                form = BlockTestForm(questions=questions)        
            context = {            
                    'form': form,            
                    'prev_block': prev_block if prev_block > 0 else None,            
                    'next_block': next_block if next_block <= num_blocks else None,            
                    'last_block': last_block,            
                    'current_block': current_block,            
                    'num_blocks': num_blocks        }        
            return render(request, 'block_test.html', context)    
    except Exception as e:        
        print(e)        
        return HttpResponseRedirect('/')
    
def process_block_answers(cleaned_data):    
    """    Обрабатывает ответы блока и возвращает словарь с результатами.    """  
    answers = {}    
    for key, val in cleaned_data.items():        
        question_id = int(key.split('')[1])        
        option_id = int(val)        
        answer_option = AnswerOption.objects.get(pk=option_id)        
        answers[question_id] = {            
            'selected_answer': answer_option,            
            'is_correct': answer_option.is_correct        }    
        return answers
    
def save_progress(user, block_number, results):    
    """    Сохраняет результаты текущего блока.    """    
    diagnostic_result = DiagnosticResult.objects.create(        
        user=user,        
        block_number=block_number    )    
    for qid, data in results.items():        
        AnswerRecord.objects.create(            
            question_id=qid,            
            selected_answer=data['selected_answer'],            
            is_correct=data['is_correct'],            
            diagnostic_result=diagnostic_result        )
        
def diagnostic_results(request):    
    """    Показывает общие результаты диагностики.    """    
    results = DiagnosticResult.objects.filter(user=request.user)\
                                  .annotate(score_percentage=Count('answers', filter=models.Q(answers__is_correct=True)))\
                                  .order_by('-completed_at')
    final_score = round((sum(r.score_percentage for r in results) / len(results)) * 100)    
    context = {        
        'final_score': final_score,     
        'results': results    }   
    return render(request, 'results.html', context)

def test_page_view(request):
    # Получаем все вопросы из базы данных
    questions = list(Question.objects.all())

    # Определяем количество блоков (каждый блок содержит 5 вопросов)
    num_blocks = len(questions) // BLOCK_SIZE + bool(len(questions) % BLOCK_SIZE)

    # Текущий блок берем из сессии или начинаем с первого
    current_block = request.session.get('current_block', 1)

    # Определяем индекс начала и конца для текущего блока
    start_idx = (current_block - 1) * BLOCK_SIZE
    end_idx = start_idx + BLOCK_SIZE
    block_questions = questions[start_idx:end_idx]

    if request.method == 'POST':
        form = BlockTestForm(questions=block_questions, data=request.POST)
        if form.is_valid():
            # Обработать форму и перейти к следующему блоку
            current_block += 1
            request.session['current_block'] = current_block
            if current_block > num_blocks:
                # Переходим к результатам
                return redirect('results')
            else:
                # Продолжаем тестирование
                return redirect('primary_test:test')
    else:
        form = BlockTestForm(questions=block_questions)

    context = {
        'form': form,
        'current_block': current_block,
        'num_blocks': num_blocks
    }
    return render(request, 'primary_test/test_page.html', context)

def determine_preferences(responses):
    counts = {"a": 0, "б": 0, "в": 0, "г": 0, "д": 0}
    for resp in responses:
        counts[resp["choice"]] += 1
    max_choice = max(counts, key=lambda k: counts[k])
    preferences_map = {
        "a": "Кибербезопасность",
        "б": "Компьютерная графика и дизайн",
        "в": "Игровая разработка",
        "г": "Программирование",
        "д": "Инженерия в IT"
    }
    return preferences_map[max_choice], counts

def calculate_percent_correct(answers):
    total = len(answers)
    correct_count = sum([1 for ans in answers if ans['is_correct']])
    return (correct_count / total) * 100