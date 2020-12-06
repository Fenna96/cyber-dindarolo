from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
# verrò cambiato se definisco un profilo utente
from django.contrib.auth.models import User
from django.db.models import Q
from http import HTTPStatus
from manager import forms, models
from common import utils

# Create your views here.
from martistupe import settings


@login_required
def index(request):
    template = loader.get_template('market/index.html')
    context = {'balance': utils.get_balance(request), }
    if request.method == 'GET':
        return HttpResponse(template.render(context, request))
    return HttpResponse(template.render(context, request), status=HTTPStatus.FOUND)


@login_required
def insert(request):
    template = loader.get_template('market/insert.html')
    context = {'balance': utils.get_balance(request), 'catalog_form': forms.InsertCatalogForm(prefix='catalog'),
               'product_form': forms.ProductForm(prefix='product')}
    if request.method == 'GET':
        return HttpResponse(template.render(context, request))
    return HttpResponse(template.render(context, request), status=HTTPStatus.FOUND)


@login_required
def catalog(request, error: str = None):
    template = loader.get_template('market/catalog.html')

    user = request.user
    catalog = models.Catalog.objects.filter(~Q(user=user))  # mostra solo ciò che vendono gli altri!
    """
    A partire dalla lista di elementi del catalogo, genero un insieme di gruppi:
    - la "key" di ogni gruppo è il nome del prodotto
    - il "items" di ogni gruppo è la lista di "vendite" di quel prodotto
    - "count" è un conteggio di quanti item ci sono
    
    ATTENZIONE: si parte dal presupposto che non ci siano prodotti con lo stesso nome
    """

    # GENERO LE CHIAVI, non duplicate e ordinate
    keys = {item.product.name for item in catalog}  # un set rimuove i duplicati da solo
    keys = sorted(keys)  # ordino
    # Trasformo il catalogo in una lista da QuerySet
    values = [item for item in catalog]

    # Genero l'insieme di "gruppi", come indicato sopra
    groups = []
    for key in keys:
        new_dict = {}
        new_dict['key'] = key
        new_dict['items'] = []
        for item in values:
            # add value if key correspond
            if item.product.name == key:
                new_dict['items'].append(item)
        new_dict['items'] = sorted(new_dict['items'], key=lambda item: (item.price, item.quantity))
        new_dict['count'] = len(new_dict['items'])
        groups.append(new_dict)

    context = {'balance': utils.get_balance(request), 'groups': groups, 'error': error, 'product_number': len(catalog)}
    if request.method == 'GET':
        return HttpResponse(template.render(context, request))
    return HttpResponse(template.render(context, request), status=HTTPStatus.FOUND)


@login_required
def user_items(request, error: str = None):
    """
    Stampa i tuoi annunci attualmente attivi (la roba che hai venduto non ancora comprata)
    :param request:
    :return:
    """
    template = loader.get_template('market/user_items.html')

    catalog = models.Catalog.objects.filter(user=request.user)  # mostra solo ciò che vendono gli altri!
    # BACKEND ^

    context = {'balance': utils.get_balance(request), 'catalog': catalog, 'error': error}
    if request.method == 'GET':
        return HttpResponse(template.render(context, request))
    return HttpResponse(template.render(context, request), status=HTTPStatus.FOUND)


@login_required
def add_item(request):
    if request.method == 'POST':
        product_form = forms.ProductForm(request.POST, prefix='product')
        catalog_form = forms.InsertCatalogForm(request.POST, prefix='catalog')
        if product_form.is_valid() and catalog_form.is_valid():
            # recovering parameters, after validation
            name = product_form.cleaned_data['name']
            price = catalog_form.cleaned_data['price']
            category = product_form.cleaned_data['category']
            quantity = catalog_form.cleaned_data['quantity']
            # search an object from exsisting ones (can't create new category for now) to be assigned to your new product
            try:
                category_obj = models.Category.objects.get(name=category)
            except:
                return HttpResponseRedirect(reverse('market:insert'))

            # capitalize all name to avoid duplicates
            name = name.capitalize()
            # search for the product
            product = models.Product.objects.filter(name=name).first()
            if (not product):
                # create new product if it doesn't exists
                product = models.Product(name=name, category=category_obj)
                product.save()
            # CONTROLLO SE L'UTENTE HA GIà INSERITO LO STESSO PRODOTTO IN PASSATO: nel caso aggiorno quantitò e prezzo
            item = models.Catalog.objects.filter(user=request.user, product=product).first()
            if (item):
                item.price = float(price)  # aggiorno il prezzo prendendo quello nuovo
                item.quantity = int(quantity) + item.quantity  # aggiorno la quantità sommandole
                item.save()
            else:
                print(product)
                # create a new entry in the catalog associated to that product, and to the current logged user
                new_item = models.Catalog(quantity=quantity, product=product, user=request.user, price=price)
                new_item.save()

            return HttpResponseRedirect(reverse('market:user_items'))
        else:
            """
            Printa la pagina con gli errori del form
            """
            return render(request, 'market/insert.html',
                          {'balance': utils.get_balance(request), 'product_form': product_form,
                           'catalog_form': catalog_form}, status=HTTPStatus.FOUND)
    """
    Se il metodo con cui è stata chiamata questa funzione non è post, qualcosa non è andato correttamente
    Si ritorna quindi alla schermata di registrazione
    """
    return HttpResponseRedirect(reverse('market:insert'))


@login_required
def buy_item(request):
    """
    This page receive a post request from "catalog" and after processing it, redirect into your index
    :return: redirect in index page (can be changed into a catalog)
    """
    if request.method == 'POST':
        # Recupero la quantità in input e l'id dell'item del catalogo
        try:
            quantity = request.POST['quantity']
            item_id = request.POST['item_id']
        except:
            error = "Something wrong with your request."
            return HttpResponseRedirect(reverse('market:catalog', args=(error,)))
        try:
            item = models.Catalog.objects.get(id=item_id)
        except:
            error = "Couldn't find the item requested in catalog."
            return HttpResponseRedirect(reverse('market:catalog', args=(error,)))

        # se funzia, recupero i vari campi dell'item
        product_name = item.product.name
        product_category = item.product.category
        seller = item.user
        price = item.price
        max_quantity = item.quantity

        # ERRORS!
        # controllo che esistano prodotto e venditore
        if (int(quantity) > int(max_quantity)):
            error = "You tried to buy, but we don't have that much!"
            return HttpResponseRedirect(reverse('market:catalog', args=(error,)))
        seller = User.objects.get(username=seller)
        if (not seller):  # se è a null qualcosa è andato male
            error = "Couldn't find user associated with this item in the catalog, try again or buy from someone else."
            return HttpResponseRedirect(reverse('market:catalog', args=(error,)))
        product = models.Product.objects.get(name=product_name, category=product_category)
        if (not product):  # se è a null vuol dire che qualcosa è andato male
            error = "Couldn't find the product associated with your request, try again or try to buy something else."
            return HttpResponseRedirect(reverse('market:catalog', args=(error,)))

        # define what i spent with this trade
        amount = float(quantity) * float(price)

        """
        Operazione di acquisto
        - recupero l'utente acquirente
        - recupero il suo balance, e lo aggiorno
        - aggiungo una nuova transizione per l'utente, con ammontare negativo
        """
        buyer = request.user  # save current user
        # non controllo se esiste, perchè qui ci arrivo solo se ho fatto il login!
        buyer_balance = models.Balance.objects.get(user=buyer)  # find his balance

        # CONTROLLO BUDGET UTENTE
        if float(buyer_balance.balance) - amount < (-1) * (models.BALANCE_LIMIT):
            error = "You don't have enough credits (limit reached)."
            return HttpResponseRedirect(reverse('market:catalog', args=(error,)))

        # non controllo se l'ha trovato o meno: ogni utente registrato ha un suo balance, se non ce l'avesse non troverei neanche l'utente!
        buyer_balance.balance = float(buyer_balance.balance) - amount  # update his balance
        buyer_balance.save()

        # save the transaction, price is negative cause it's a buy and not a sell
        new_entry = models.Transaction(product=product, user=buyer, amount=-amount)
        new_entry.save()

        """
        Operazione di vendita
        - recupero dalla post l'utente venditore
        - recupero il suo balance, e lo aggiorno
        - aggiungo una transazione per chi compra
        """
        seller_balance = models.Balance.objects.get(user=seller)  # find his balance
        # non controllo se l'ha trovato o meno: ogni utente registrato ha un suo balance, se non ce l'avesse non troverei neanche l'utente!
        seller_balance.balance = float(seller_balance.balance) + amount  # update his balance
        # SE IL BUDJET SFORA I 500, LO RIMETTE A 500
        if (seller_balance.balance > models.BALANCE_LIMIT):
            seller_balance.balance = models.BALANCE_LIMIT
        seller_balance.save()

        # save the transaction, price is negative cause it's a buy and not a sell
        new_entry = models.Transaction(product=product, user=seller, amount=amount)
        new_entry.save()

        """
        Qui si dovrebbe controllare se hai comprato tutto o ancora no. Per ora si compra sempre tutto
        Quando si compra anche l'ultimo item, bisogna togliere l'entry dal catalogo
        Si aggiunge inoltre una nuova entry nel pricetracker per analisi
        Tenere presente che forse bisognerebbe gestire l'accesso concorrente, nel senso che se due comprano simultaneamente ci possono essere casini grossi!
        """
        # che non superi la quantità massima è già controllato dal javascript, non serve qua
        if (int(quantity) == int(max_quantity)):
            item.delete()
        else:
            item.quantity = int(max_quantity) - int(quantity)
            item.save()
        # add element in the tracker
        tracking = models.Product_pricetracker(seller=seller, product=product, price=price)
        tracking.save()

        # Notify seller and buyer!
        # BUYER
        utils.send_html_mail(
            subject='Item bought',
            recipient_list=[buyer.email],
            html_content=f"""
                        <html>
                            <head></head>
                          <body>
                            <p>
                               Congratulation {buyer.username}, you just bought the following products:<br> 
                               <b>Product</b>: {product_name}<br>
                               <b>Quantity</b>: {quantity}<br>
                               <b>Price</b>: {price}<br>
                               <b>Total</b>: {-amount}<br>
                               <br>Your credit is now: {buyer_balance.balance}!<br> 
                               <a href="http://{request.get_host()}/market">Go back to market!</a>
                            </p>
                          </body>
                        </html>
                        """,
            fail_silently=True
        )
        # SELLER
        residual = int(max_quantity) - int(quantity)
        utils.send_html_mail(
            subject='Item sold',
            recipient_list=[seller.email],
            html_content=f"""
                                <html>
                                    <head></head>
                                  <body>
                                    <p>
                                       Congratulation {seller.username}, somebody just bought the following products:<br> 
                                       <b>Product</b>: {product_name}<br>
                                       <b>Quantity</b>: {quantity}<br>
                                       <b>Price</b>: {price}<br>
                                        <b>Total</b>: {amount}<br>
                                       <br>Your credit is now: {seller_balance.balance}!<br> 
                                        There are still {residual} of your "{product_name}" in the catalog!
                                       <a href="http://{request.get_host()}/market">Go back to market!</a>
                                    </p>
                                  </body>
                                </html>
                                """,
            fail_silently=True
        )
        return render(request, 'market/success.html', {'balance': utils.get_balance(request),
                                                       'product': product_name,
                                                       'quantity': quantity,
                                                       'price': price,
                                                       'amount': -(int(quantity) * int(price))
                                                       })
    """
    Se il metodo con cui è stata chiamata questa funzione non è post, qualcosa non è andato correttamente
    Si ritorna quindi alla schermata di registrazione
    """
    return HttpResponseRedirect(reverse('market:catalog'))


@login_required
def remove_item(request):
    """
    This page receive a post request from "user_items" and after processing it, redirect into your index
    :return: redirect in index page (can be changed into a catalog)
    """
    if request.method == 'POST':
        # Cerco di recuperare l'id dell'item associato
        try:
            item_id = request.POST['item_id']
        except:
            error = "Something wrong with your request."
            return HttpResponseRedirect(reverse('market:user_items', args=(error,)))
        try:
            item = models.Catalog.objects.get(id=item_id)
        except:
            error = "Couldn't find the item requested in catalog."
            return HttpResponseRedirect(reverse('market:user_items', args=(error,)))

        # product informations
        product_name = item.product.name
        product_category = item.product.category
        quantity = item.quantity
        price = item.price

        # controllo che il prodotto esista
        product = models.Product.objects.get(name=product_name, category=product_category)
        if (not product):  # se è a null vuol dire che qualcosa è andato male
            error = "Couldn't find the product associated with your request, try again."
            return HttpResponseRedirect(reverse('market:user_items', args=(error,)))

        """
        Operazione di rimozione
        - elimino dal catalogo l'oggetto
        suppongo che l'oggetto sia sempre singolo, perchè controllo nella fase di inserimento
        (da valutare accesso concorrente)
        """
        item.delete()

        return HttpResponseRedirect(reverse('market:user_items'))
    """
    Se il metodo con cui è stata chiamata questa funzione non è post, qualcosa non è andato correttamente
    Si ritorna quindi alla schermata di registrazione
    """
    return HttpResponseRedirect(reverse('market:user_items'))
