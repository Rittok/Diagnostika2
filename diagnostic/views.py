from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import *
from .models import UserProfile

# View для регистрации пользователя
def registration_view(request):
    if request.user.is_authenticated:
        return redirect('home')  # перенаправляет зарегистрированных пользователей на главную страницу
    
    if request.method == 'POST':
        reg_form = RegistrationForm(request.POST)
        if reg_form.is_valid():
            # Сохраняем пользователя и профиль
            user = reg_form.save(commit=False)
            user.set_password(reg_form.cleaned_data['password'])
            user.save()
            
            # Создаем профиль пользователя
            profile = UserProfile(user=user)
            profile.save()
            
            # Авторизуем пользователя после регистрации
            auth_login(request, user)
            return redirect('home')  # перенаправляем на домашнюю страницу
    else:
        reg_form = RegistrationForm()
    
    return render(request, 'registration/register.html', {'reg_form': reg_form})

# View для входа пользователя
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')  # перенаправляет уже залогиненных пользователей
    
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('home')  # перенаправляем на домашнюю страницу
    else:
        login_form = LoginForm()
    
    return render(request, 'registration/login.html', {'login_form': login_form})

# View для выхода пользователя
@login_required(login_url='/accounts/login/')
def logout_view(request):
    auth_logout(request)
    return redirect('home')  # перенаправляем обратно на главную страницу

# View для редактирования профиля
@login_required(login_url='/accounts/login/')
def edit_profile_view(request):
    if request.method == 'POST':
        profile_edit_form = ProfileEditForm(instance=request.user.profile, data=request.POST)
        if profile_edit_form.is_valid():
            profile_edit_form.save()
            return redirect('edit-profile-success')  # перенаправляем на успешную страницу редактирования
    else:
        profile_edit_form = ProfileEditForm(instance=request.user.profile)
    
    return render(request, 'profiles/edit_profile.html', {'profile_edit_form': profile_edit_form})