from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.urls import reverse

from manager import models
from user.models import Profile, User, DEFAULT_PIC_FILE
from user.forms import ProfileForm
from common import utils

# Create your views here.
@login_required
def index(request):
    template = loader.get_template("community/index.html")
    context = {"balance": utils.get_balance(request)}
    if request.method == "GET":
        return HttpResponse(template.render(context, request))
    return HttpResponse(template.render(context, request), status=HTTPStatus.FOUND)


@login_required
def leaderboard(request):
    leaderboard = models.Balance.objects.filter().order_by("-balance")

    top10 = leaderboard[:10]
    worse10 = leaderboard.reverse()[:10]

    template = loader.get_template("community/leaderboard.html")
    context = {
        "balance": utils.get_balance(request),
        "leaderboard": leaderboard,
        "top10": top10,
        "worse10": worse10,
    }
    if request.method == "GET":
        return HttpResponse(template.render(context, request))
    return HttpResponse(template.render(context, request), status=HTTPStatus.FOUND)


@login_required
def community_profile(request, username):
    template = loader.get_template("community/profile.html")
    if request.method == "GET":
        try:
            user = User.objects.get(username=username)
            profile = Profile.objects.get(user=user)
            balance = models.Balance.objects.get(user=user)
        except:
            return HttpResponseRedirect(
                reverse("community:search", args=("User not found",))
            )
        context = {
            "balance": utils.get_balance(request),
            "user": user,
            "profile": profile,
            "profile_balance": balance,
        }

        # your profile page
        if user == request.user:
            context["yourself"] = True
        return HttpResponse(template.render(context, request))
    return HttpResponse("Request not valid", status=HTTPStatus.FOUND)


@login_required
def modify(request, email_error: str = None):
    profile = Profile.objects.get(user=request.user)
    balance = models.Balance.objects.get(user=request.user)
    template = loader.get_template("community/modify.html")
    context = {
        "balance": utils.get_balance(request),
        "profile": profile,
        "form": ProfileForm,
        "profile_balance": balance,
        "email_error": email_error,
    }
    if request.method == "GET":
        return HttpResponse(template.render(context, request))
    return HttpResponse(template.render(context, request), status=HTTPStatus.FOUND)


@login_required
def change_profile(request):
    if request.method == "POST":
        form = ProfileForm(data=request.POST)
        if form.is_valid():
            # obtaining arguments
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            name = form.cleaned_data["name"]
            surname = form.cleaned_data["surname"]
            mobile = form.cleaned_data["mobile"]
            biography = form.cleaned_data["biography"]
            user = request.user

            # create new profile associated to the logged
            profile = Profile.objects.get(user=user)
            profile.name = name
            profile.surname = surname
            profile.mobile = mobile
            profile.biography = biography
            user.email = email

            # controlla che tu non abbia inserito la mail di un altro
            try:
                yep = User.objects.get(email=email)
                if yep.username != user.username:
                    print(yep.username != user.username)
                    error = "Email taken by another user, we're sorry"
                    return HttpResponseRedirect(
                        reverse("community:modify", args=(error,))
                    )
                user.save()
                profile.save()  # salvataggio in BACKEND
                return HttpResponseRedirect(
                    reverse("community:community_profile", args=(user.username,))
                )
            except:
                user.save()
                profile.save()  # salvataggio in BACKEND
                return HttpResponseRedirect(
                    reverse("community:community_profile", args=(user.username,))
                )
        else:
            """
            Render ricarica la pagina, ma con gli errori
            """
        profile = Profile.objects.get(user=request.user)
        balance = models.Balance.objects.get(user=request.user)
        template = loader.get_template("community/modify.html")

        context = {
            "balance": utils.get_balance(request),
            "profile": profile,
            "form": form,
            "profile_balance": balance,
        }
        return HttpResponse(template.render(context, request), status=HTTPStatus.FOUND)

    """
    Probabilmente errore nello scrivere, quindi vieni reindirizzato alla pagina giusta
    """
    return HttpResponseRedirect(reverse("community:modify"))


@login_required
def change_pic(request):
    if request.method == "POST":
        try:
            profile_image = request.FILES["profile_image"]
        except:
            profile_image = None

        # create new profile associated to the logged
        profile = Profile.objects.get(user=request.user)
        if profile_image:
            profile.profile_image = profile_image
        else:
            profile.profile_image = DEFAULT_PIC_FILE
        profile.save()  # salvataggio in BACKEND
        return HttpResponseRedirect(
            reverse("community:community_profile", args=(request.user.username,))
        )
    """
    Probabilmente errore nello scrivere, quindi vieni reindirizzato alla pagina giusta
    """
    return HttpResponseRedirect(reverse("community:modify"))


@login_required
def search_page(request, error: str = None):
    template = loader.get_template("community/search.html")
    context = {"balance": utils.get_balance(request), "error": error}
    if request.method == "GET":
        return HttpResponse(template.render(context, request))
    return HttpResponse(template.render(context, request), status=HTTPStatus.FOUND)


@login_required
def search_user(request):
    if request.method == "POST":
        try:
            username = request.POST["username"]
            if username:
                try:
                    user = User.objects.get(username=username)
                    return HttpResponseRedirect(
                        reverse("community:community_profile", args=(username,))
                    )
                except:
                    error = "User not found"
                    return HttpResponseRedirect(
                        reverse("community:search", args=(error,))
                    )
            error = "You have to type something"
            return HttpResponseRedirect(reverse("community:search", args=(error,)))
        except:
            error = "No username given"
            return HttpResponseRedirect(reverse("community:search", args=(error,)))
    """
    Probabilmente errore nello scrivere, quindi vieni reindirizzato alla pagina giusta
    """
    return HttpResponseRedirect(reverse("community:search"))
