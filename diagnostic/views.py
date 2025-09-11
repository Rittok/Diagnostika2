from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from .forms import *
from .authentication_backends import EmailAuthBackend

def registration_view(request):
    if request.method == 'POST':
        reg_form = RegistrationForm(request.POST)
        if reg_form.is_valid():
            email = reg_form.cleaned_data['email']
            user = User.objects.create_user(username=email, email=email)
            user.save()
            # Автоматически авторизуем пользователя
            auth_login(request, user, backend='diagnostic.authentication_backends.EmailAuthBackend')
            # Устанавливаем номер текущего блока
            request.session['current_block'] = 1
            # Переадресация на первую страницу тестирования
            return render(request,'primary_test/block_test.html',{'current_block': 1})
        else:
            # Форма неверна, возвращаем страницу с ошибками
            return render(request, 'registration/register.html', {'reg_form': reg_form})
    else:
        # Показываем пустую форму регистрации
        reg_form = RegistrationForm()
        return render(request, 'registration/register.html', {'reg_form': reg_form})

def login_view(request):
    if request.method == 'POST':
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                auth_login(request, user, backend='diagnostic.authentication_backends.EmailAuthBackend')
                return render(request,'primary_test/block_test.html',{'current_block': 1})
            except User.DoesNotExist:
                form.add_error(None, "Пользователь с такой почтой не найден!")
    else:
        form = EmailLoginForm()
    
    return render(request, 'registration/login.html', {'form': form})

@login_required(login_url='/registration/login/')
def logout_view(request):
    auth_logout(request)
    return redirect('login')

def handler404(request, exception):
    return render(request, '404.html', status=404)