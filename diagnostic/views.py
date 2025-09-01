from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.conf import settings
from .forms import *
from .models import *

def start_primary_diagnostic(request):
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST)
        if profile_form.is_valid():
            email = profile_form.cleaned_data['email']
            first_name = profile_form.cleaned_data['first_name']
            last_name = profile_form.cleaned_data['last_name']
            school = profile_form.cleaned_data['school']  
            class_level_pk = profile_form.cleaned_data['class_level']
            class_letter = profile_form.cleaned_data['class_letter']


            # Генерация уникального имени пользователя (можно использовать ФИО или другое правило)
            username = f"{first_name}_{last_name}".lower()

            # Создаем пользователя без пароля и email
            new_user = User.objects.create_user(username=email, email=email, password=None)
            school = School.objects.get(name=school)
            school_id = school.pk

            class_level = ClassLevel.objects.get(pk=class_level)
            # Создаем профиль пользователя
            profile = UserProfile(user=new_user, first_name=first_name, last_name=last_name,  school_id=school_id, class_level_id=class_level_pk, class_letter=class_letter)
            profile.save()

            return redirect('registration_success')
        else:
            context = {'profile_form': profile_form}
            return render(request, 'start.html', context)
    else:
        profile_form = UserProfileForm()
        context = {'profile_form': profile_form}
        return render(request, 'start.html', context)

def primary_diagnostic_view(request):
    questions = Question.objects.filter(test_type='primary')[:5]
    
    if request.method == 'POST':
        form = TestForm(request.POST, questions=questions)
        if form.is_valid():
            result = {}
            for key, value in form.cleaned_data.items():
                answer_id = int(value)
                result[key.split('_')[1]] = AnswerOption.objects.get(id=answer_id).is_correct
            
            # Сохранение результатов в БД
            # Переход на следующую страницу или завершение теста
    else:
        form = TestForm(questions=questions)
        
    context = {
        'form': form,
        'current_question_number': len(form.fields),
        'total_questions': 15
    }
    return render(request, 'test_page.html', context)