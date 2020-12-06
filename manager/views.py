from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from . import models, forms
from common import utils
from user.models import Profile

# Create your views here.
@login_required
def index(request):
    template = loader.get_template('manager/index.html')
    #the user is always defined if i get here, cause of the login_required decorator!
    current_balance = utils.get_balance(request)
    credit = current_balance.balance
    stars = round(current_balance.user_stars,1)

    profile = Profile.objects.get(user=request.user)
    context = {'profile':profile,'balance':current_balance,'credit': credit, 'stars':stars}
    return HttpResponse(template.render(context,request))
