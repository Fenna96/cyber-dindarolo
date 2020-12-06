from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from http import HTTPStatus

from analytics.utils import retrieve_history, possibilities, sum_dict, sum_category, group_by_user
from api.serializers import TransactionSerializer
from manager import models
from common import utils


@login_required
def index(request):
    template = loader.get_template('analytics/index.html')
    context = {'balance': utils.get_balance(request),}
    if request.method == 'GET':
        return HttpResponse(template.render(context,request))
    return HttpResponse(template.render(context,request), status=HTTPStatus.FOUND)



@login_required
def history(request):
    #recupera le possibili opzioni
    if request.method == 'GET':
        options = possibilities()
        your_history = models.Transaction.objects.filter(user=request.user)
        if your_history:
            transactions = {}
            lineChart = {}
            pieChart = {}
            for opt in options:
                ordered_transaction = retrieve_history(request,your_history,opt)
                transactions[opt] = ordered_transaction
                lineChart[opt] = sum_dict(ordered_transaction)
                if opt != "settimana":
                    pieChart[opt] = sum_category(ordered_transaction[-1]['group'], models.Category.objects.all())

            context = {'balance': utils.get_balance(request),'transactions':transactions,'history':your_history.order_by('-date'), 'lineChart': lineChart, 'pieChart': pieChart}
            template = loader.get_template('analytics/history.html')
            return HttpResponse(template.render(context, request))
        else:
            error = 'No data found. Try our market!'
            return render(request, 'analytics/history.html', {'error': error, 'balance': utils.get_balance(request)})
    return HttpResponse('Not allowed', status=HTTPStatus.FOUND)


@login_required
def price_tracker(request,item):
    if request.method == 'GET':
        #recupera le possibili opzioni
        product = models.Product.objects.filter(name=item).first()
        if (product):
            lineChart= group_by_user(request, models.Product_pricetracker.objects.filter(product=product), item)
            context = {'balance': utils.get_balance(request),'lineChart':lineChart, 'item':item}
            template = loader.get_template('analytics/price_tracker.html')
            return HttpResponse(template.render(context, request))
        else:
            error = 'Product not found'
            return HttpResponseRedirect(reverse('analytics:search', args=(error,)))
    return HttpResponse('Not allowed', status=HTTPStatus.FOUND)


@login_required
def search_page(request,error:str=None):
    template = loader.get_template('analytics/search.html')
    context = {'balance': utils.get_balance(request), 'error':error}
    if request.method == 'GET':
        return HttpResponse(template.render(context, request))
    return HttpResponse(template.render(context, request), status=HTTPStatus.FOUND)

@login_required
def search_product(request):
    if request.method == 'POST':
        try:
            item = request.POST['item']
            if(item):
                item = item.capitalize()
                try:
                    user = models.Product.objects.get(name=item)
                    return HttpResponseRedirect(reverse('analytics:price_tracker', args=(item,)))
                except:
                    error = 'Product not found'
                    return HttpResponseRedirect(reverse('analytics:search', args=(error,)))
            error = 'You have to type something'
            return HttpResponseRedirect(reverse('analytics:search', args=(error,)))
        except:
            error = 'Need an item in request'
            return HttpResponseRedirect(reverse('analytics:search', args=(error,)))
    """
    Probabilmente errore nello scrivere, quindi vieni reindirizzato alla pagina giusta
    """
    return HttpResponseRedirect(reverse('analytics:search'))
