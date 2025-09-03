from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
from .forms import *
from .authentication_backends import EmailAuthBackend

test = 'primary_test:test_page'
# View для регистрации пользователя
def registration_view(request):
    if request.user.is_authenticated:
        return redirect('home')  # перенаправляет зарегистрированных пользователей на главную страницу
    
    if request.method == 'POST':
        reg_form = RegistrationForm(request.POST)
        if reg_form.is_valid():
            # Регистрируем пользователя без пароля и создаем активный аккаунт
            new_user = reg_form.save()
            auth_login(request, new_user)
            return redirect(reverse(test))  # Автоматически переходим на страницу теста
    else:
        reg_form = RegistrationForm()
    
    return render(request, 'registration/register.html', {'reg_form': reg_form})

def test_page_view(request):
    return render(request, reverse('primary_test/test_page.html'))

def login_view(request):
    if request.method == 'POST':
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                auth_login(request, user, backend='diagnostic.authentication_backends.EmailAuthBackend')
                return redirect(reverse(test))
            except User.DoesNotExist:
                form.add_error(None, "Пользователь с такой почтой не найден!")
    else:
        form = EmailLoginForm()
    
    return render(request, 'registration/login.html', {'form': form})

# View для выхода пользователя
@login_required(login_url='/registration/login/')
def logout_view(request):
    auth_logout(request)
    return redirect('home')

