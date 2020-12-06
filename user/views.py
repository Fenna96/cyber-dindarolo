from http import HTTPStatus

from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from . import forms
from cyberdindarolo.user import welcome_email


@require_http_methods(["GET"])
@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('user:login'))


@require_http_methods(["GET"])
def user_login(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('manager:index'))
    template = loader.get_template('user/login.html')
    context = {'form': forms.LoginForm}
    return HttpResponse(template.render(context, request))


@require_http_methods(["POST"])
def execute_login(request):
    form = forms.LoginForm(request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        if user and user.is_active:
            login(request, user)
            return HttpResponseRedirect(reverse('manager:index'))
        error = 'Wrong username or password.'
        return render(request, 'user/login.html', {'form': form, 'error': error}, status=HTTPStatus.FOUND)
    error = 'Invalid data.'
    return render(request, 'user/login.html', {'form': form, 'error': error}, status=HTTPStatus.FOUND)


@require_http_methods(["GET"])
def registration(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('manager:index'))
    template = loader.get_template('user/register.html')
    context = {'form': forms.ProfileForm}
    return HttpResponse(template.render(context, request))


@require_http_methods(["POST"])
def execute_registration(request):
    form = forms.ProfileForm(data=request.POST)
    if form.is_valid():
        p = form.save()
        profile_image = request.FILES.get('profile_image') if request.get('FILES') else None
        if profile_image:
            p.profile_image = profile_image
            p.save()

        if User.objects.filter(Q(username=p.username) | Q(email=p.email)):
            error = 'Username or email already in use.'
            return render(request, 'user/register.html', {'form': form, 'error': error}, status=HTTPStatus.FOUND)

        login(request, authenticate(username=p.username, password=p.password))
        welcome_email(username=p.username, email=p.email, request=request)

        return HttpResponseRedirect(reverse('manager:index'))
    return render(request, 'user/register.html', {'form': form}, status=HTTPStatus.FOUND)
