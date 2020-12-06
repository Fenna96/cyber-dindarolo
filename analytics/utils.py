"""
MANAGER: utility functions for views
"""
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractWeek
from manager import models
from common import utils
from datetime import datetime
from user.models import User
"""
Per gestire tutte le varie analisi dell'app che si suddividono per intervalli di date
Per una gestione più compatta, in questa classe si mantengono tutte le possibilità supportate dall'app, con possibilità di ampliarle direttamente qui
"""

opt = ['anno','mese','settimana']

def possibilities():
    return opt

def retrieve_history(request, model, option = 'default'):
    # the user is always defined if i get here, cause of the login_require decorator!
    user = request.user
    #initialising the desc option
    desc = False
    transactions = None
    # case-insensitive comparisons
    option = option.lower()
    if option.lower() == 'anno':
        #obtaining all records, with their year
        ordered_records = model.annotate(anno=ExtractYear('date'))
        #earlier years have higher values
        desc = True
    elif option.lower() == 'mese':
        #obtaining all records, with their month
        ordered_records = model.annotate(mese=ExtractMonth('date'))
    elif option.lower() == 'settimana':
        #obtaining all records, with their day
        ordered_records = model.annotate(settimana=ExtractWeek('date'))
    #extraction keys
    keys = set(key[option] for key in ordered_records.values(option))
    #generate ordered groups from keys and values with utility function
    transactions = utils.group_by_key(ordered_records,keys,option, desc = desc)
    return transactions

# ---------------------------------------------------------------------#
"""
Funzioni per ottenere dati dei grafici di history
"""
def sum_dict(ordered_transaction:None):
    summed = []
    for dict in ordered_transaction:
        counter = 0
        for item in dict['group']:
            counter += item.amount
        new_dict = {}
        new_dict['key'] = dict['key']
        new_dict['sum'] = counter
        summed.append(new_dict)
    return summed

def sum_category(group, categories):
    group.sort(key=lambda x: str(x.product.category))
    new_dict = {}
    for category in categories:
        new_dict[category.name] = 0
    for x in group:
        cat = str(x.product.category)
        new_dict[cat] += x.amount
    return new_dict

# ---------------------------------------------------------------------#
"""
Funzioni per i grafici di price tracker
"""
def group_by_user(request, model, item):
    #annotate transaction with year and month
    ordered_records = model.annotate(anno=ExtractYear('date'),mese=ExtractMonth('date'))

    #selecting current year
    today = datetime.today()
    last_year = ordered_records.filter(anno=today.year).order_by('seller')

    grouped = {}
    #group by seller
    for record in last_year:
        if record.seller in grouped.keys():
            grouped[str(record.seller)].append(record)
        else:
            grouped[str(record.seller)] = [record]

    #group by month, calculating media
    for key, value in grouped.items():
        new_dict = {}
        #scorro ogni mese
        for i in range(12):
            #contatori
            counter = 0
            sum = 0
            #per ogni mese, guardo i record con quel mese e calcolo la somma
            for record in value:
                if record.mese == i+1:
                    counter += 1
                    sum += record.price    #positivo perchè ho preso le vendite
            if counter:
                media = sum/counter
            else:
                #se il tuo counter è nullo, voglio salvare la media del mese precedente perchè il prezzo non è variato
                if i:
                    media = new_dict[i] #i mesi sono i+1, quindi il precedente è i
                else:
                    media = 0   #se mi trovo nel mese 0 non ha senso cercare il mese prima, quindi metto 0

            new_dict[i+1] = media

        grouped[key] = new_dict
    return grouped
