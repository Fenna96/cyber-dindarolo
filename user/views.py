from http import HTTPStatus

from django.core import mail
from django.core.mail import send_mail
from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.db.models import Q

from martistupe import settings
from . import forms, models
from common import utils

def user_logout(request):
    logout(request)
    if request.method == 'GET':
        return HttpResponseRedirect(reverse('user:login'))
    return HttpResponseRedirect(reverse('user:login'), status=HTTPStatus.FOUND)

def user_login(request):
    #if user is authenticated he can't possibly acces this page!
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('manager:index'))
    template = loader.get_template('user/login.html')
    context = {'form': forms.LoginForm}
    if request.method == 'GET':
        return HttpResponse(template.render(context, request))
    return HttpResponse(template.render(context, request), status=HTTPStatus.FOUND)

def execute_login(request):
    # if user is authenticated he can't possibly acces this page!
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('manager:index'))
    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            #obtaining arguments
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            #authenticate
            user = authenticate(username=username, password=password)
            if user and user.is_active:
                # log the user in!
                login(request,user)
                return HttpResponseRedirect(reverse('manager:index'))
            error = 'Wrong username or password.'
            return render(request, 'user/login.html', {'form': form, 'error':error}, status=HTTPStatus.FOUND)
        """
        Se qualche dato è stato inserito in maniera non corretta, si ritorna alla schermata di login
        """
        error = 'Invalid data.'
        return render(request, 'user/login.html', {'form': form, 'error':error}, status=HTTPStatus.FOUND)
    """
    Se il metodo con cui è stata chiamata questa funzione non è post, qualcosa non è andato correttamente
    Si ritorna quindi alla schermata di login
    """
    return HttpResponseRedirect(reverse('user:login'), status=HTTPStatus.FOUND)

def registration(request):
    # if user is authenticated he can't possibly acces this page!
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('manager:index'))
    template = loader.get_template('user/register.html')
    context = {'form': forms.ProfileForm}
    if request.method == 'GET':
        return HttpResponse(template.render(context, request))
    return HttpResponse(template.render(context, request), status=HTTPStatus.FOUND)

def execute_registration(request):
    # if user is authenticated he can't possibly acces this page!
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('manager:index'))
    if request.method == 'POST':
        form = forms.ProfileForm(data=request.POST)
        if form.is_valid():
            #obtaining arguments
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            name =  form.cleaned_data['name']
            surname = form.cleaned_data['surname']
            mobile = form.cleaned_data['mobile']
            biography = form.cleaned_data['biography']
            #UPLOADED IMAGE
            try:
                profile_image = request.FILES['profile_image']
            except:
                profile_image = None
            """if profile_image: #if inserted, add default folder
                profile_image = models.PROFILE_PIC + profile_image
            if not profile_image: #else, equal to default pic
                profile_image = models.DEFAULT_PIC"""
            """
            Controlla se le informazioni inserite sono già occupate
            - se email e username sono già in uso
            - se o username o email sono già in uso
            nel caso stampa l'errore
            """
            if User.objects.filter(Q(username = username) | Q(email = email)):
                error = 'Username or email already in use.'
                return render(request, 'user/register.html', {'form': form, 'error':error}, status=HTTPStatus.FOUND)

            utils.send_html_mail(
                subject='Welcome to our community!',
                recipient_list=[email],
                html_content=f"""
                <html>
                    <head></head>
                  <body>
                    <p>
                       Congratulation {username}, the registration was successful. Go visit our market!<br> 
                       <a href="http://{request.get_host()}/market">Click here</a>
                    </p>
                  </body>
                </html>
                """,
                fail_silently=True
            )

            #create new user
            user = User.objects.create_user(username, email)
            user.set_password(password)

            user.save() #salvataggio in BACKEND

            #create new profile associated with that user
            if profile_image:
                profile = models.Profile(user=user,name=name,surname=surname,mobile=mobile,biography=biography,profile_image=profile_image)
            else:
                profile = models.Profile(user=user,name=name,surname=surname,mobile=mobile,biography=biography)
            profile.save() #salvataggio in BACKEND

            # log the new user in!
            login(request, authenticate(username=username, password=password))

            return HttpResponseRedirect(reverse('manager:index'))
        else:
            """
            Render ricarica la pagina, ma con gli errori
            """
            return render(request, 'user/register.html', {'form': form}, status=HTTPStatus.FOUND)
    """
      Se il metodo con cui è stata chiamata questa funzione non è post, qualcosa non è andato correttamente
      Si ritorna quindi alla schermata di registrazione
    """
    return HttpResponseRedirect(reverse('user:registration'))