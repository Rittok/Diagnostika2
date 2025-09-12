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
            request.session['current_block'] = 1
            return redirect('primary_test:block1_test', page=1)
        else:
            return render(request, 'registration/register.html', {'reg_form': reg_form})
    else:
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
                return redirect('primary_test:block1_test', page=1)
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