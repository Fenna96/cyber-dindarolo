import django
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from common import utils
from analytics.utils import retrieve_history, group_by_user, sum_dict, sum_category, possibilities

# REST IMPORTS
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

# importing models
from manager.models import BALANCE_LIMIT
from martistupe import settings
from .serializers import User, Profile
from .serializers import Balance, Category, Product, Transaction, Catalog, Product_pricetracker
from user.models import PROFILE_PIC, DEFAULT_PIC
# importing serializers
from .serializers import UserSerializer, ProfileSerializer
from .serializers import BalanceSerializer, CategorySerializer, ProductSerializer, TransactionSerializer, \
    CatalogSerializer, PricetrackerSerializer
# importing forms serializers
from .forms import LoginSerializer, RegistrationSerializer, insertSerializer, buySerializer, removeSerializer, \
    searchSerializer, modifySerializer


class indexAPI(APIView):

    def get(self, request):
        return Response('hello', status=status.HTTP_200_OK)


"""
###USER API###
"""


class loginAPI(APIView):
    def post(self, request):
        if request.user.is_authenticated:
            return Response({"your_token": django.middleware.csrf.get_token(request)}, status=status.HTTP_302_FOUND)
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            print(serializer.data)
            username = serializer.data['username']
            password = serializer.data['password']
            # authenticate
            user = authenticate(username=username, password=password)
            if user and user.is_active:
                # log the user in!
                login(request, user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            error = 'Wrong username or password.'
            return Response({'error': error}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class logoutAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logout(request)
        return Response(None, status=status.HTTP_200_OK)


class registrationAPI(APIView):
    def post(self, request):
        if request.user.is_authenticated:
            return Response({"your_token": django.middleware.csrf.get_token(request)}, status=status.HTTP_302_FOUND)
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # obtaining arguments
            username = serializer.data['username']
            email = serializer.data['email']
            password = serializer.data['password']
            name = serializer.data['name']
            surname = serializer.data['surname']
            mobile = serializer.data['mobile']
            biography = serializer.data['biography']
            # UPLOADED IMAGE
            profile_image = serializer.data['profile_image']
            if profile_image:  # if inserted, add default folder
                profile_image = PROFILE_PIC + profile_image
            else:  # else, equal to default pic
                profile_image = DEFAULT_PIC
            if User.objects.filter(Q(username=username) | Q(email=email)):
                error = 'Username or email already in use.'
                return Response({'error': error}, status=status.HTTP_409_CONFLICT)

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
                fail_silently=True,
            )

            # create new user
            user = User.objects.create_user(username, email)
            user.set_password(password)
            user.save()  # salvataggio in BACKEND

            # create new profile associated with that user
            profile = Profile(user=user, name=name, surname=surname, mobile=mobile, biography=biography,
                              profile_image=profile_image)
            profile.save()  # salvataggio in BACKEND

            balance = Balance(user=user, balance=0)
            balance.save()

            # log the new user in!
            login(request, authenticate(username=username, password=password))
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class tokenAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        context = {
            'token': django.middleware.csrf.get_token(request)
        }
        return Response(context, status=200)


"""
###NAVBAR API###
"""


class navbarAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # the user is always defined if i get here, cause of the login_required decorator!
        balance = BalanceSerializer(utils.get_balance(request)).data
        balance['user'] = User.objects.get(id=balance['user']).username
        context = {
            'balance': balance
        }
        return Response(context, status=200)


"""
###MANAGER API###
"""


class managerAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # the user is always defined if i get here, cause of the login_required decorator!
        context = {
            'profile': ProfileSerializer(Profile.objects.get(user=request.user)).data,
            'balance': BalanceSerializer(utils.get_balance(request)).data
        }
        return Response(context, status=200)


"""
###MARKET API###
"""


class insertAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = insertSerializer(data=request.data)
        if serializer.is_valid():
            name = serializer.data['name']
            price = serializer.data['price']
            category = serializer.data['category']
            quantity = serializer.data['quantity']

            # search an object from exsisting ones (can't create new category for now) to be assigned to your new product
            category_obj = Category.objects.get(name=category)

            # capitalize all name to avoid duplicates
            name = name.capitalize()
            # search for the product
            product = Product.objects.filter(name=name).first()
            if (not product):
                # create new product if it doesn't exists
                product = Product(name=name, category=category_obj)
                product.save()
            # CONTROLLO SE L'UTENTE HA GIà INSERITO LO STESSO PRODOTTO IN PASSATO: nel caso aggiorno quantitò e prezzo
            item = Catalog.objects.filter(user=request.user, product=product).first()
            if (item):
                item.price = float(price)  # aggiorno il prezzo prendendo quello nuovo
                item.quantity = int(quantity) + item.quantity  # aggiorno la quantità sommandole
                item.save()
            else:
                print(product)
                # create a new entry in the catalog associated to that product, and to the current logged user
                new_item = Catalog(quantity=quantity, product=product, user=request.user, price=price)
                new_item.save()

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class catalogAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        ##need to serialize
        catalog = CatalogSerializer(Catalog.objects.filter(~Q(user=user)),
                                    many=True).data  # mostra solo ciò che vendono gli altri!
        for item in catalog:
            username = User.objects.get(id=item['user']).username
            item['user'] = username
        """
        A partire dalla lista di elementi del catalogo, genero un insieme di gruppi:
        - la "key" di ogni gruppo è il nome del prodotto
        - il "items" di ogni gruppo è la lista di "vendite" di quel prodotto
        - "count" è un conteggio di quanti item ci sono

        ATTENZIONE: si parte dal presupposto che non ci siano prodotti con lo stesso nome
        """

        # GENERO LE CHIAVI, non duplicate e ordinate
        keys = {item.get("product", None) for item in catalog}  # un set rimuove i duplicati da solo
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
                if item.get("product", None) == key:
                    new_dict['items'].append(item)
            new_dict['items'] = sorted(new_dict['items'],
                                       key=lambda item: (item.get("price", None), item.get("quantity", None)))
            new_dict['count'] = len(new_dict['items'])
            groups.append(new_dict)
        context = {
            'groups': groups,
            'product_number': len(catalog),
            'balance': BalanceSerializer(utils.get_balance(request)).data
        }
        return Response(context, status=200)


class user_itemsAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        ##need to serialize
        catalog = CatalogSerializer(Catalog.objects.filter(user=request.user),
                                    many=True).data  # mostra solo ciò che vendono gli altri!

        context = {
            'catalog': catalog,
            'balance': BalanceSerializer(utils.get_balance(request)).data
        }
        return Response(context, status=200)


class buyAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = buySerializer(data=request.data)
        if serializer.is_valid():
            quantity = serializer.data['quantity']
            item_id = serializer.data['id']
            try:
                item = Catalog.objects.get(id=item_id)
            except:
                error = "Couldn't find the item requested in catalog."
                return Response({'error': error}, status=status.HTTP_404_NOT_FOUND)

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
                return Response({'error': error}, status=status.HTTP_404_NOT_FOUND)
            seller = User.objects.get(username=seller)
            if (not seller):  # se è a null qualcosa è andato male
                error = "Couldn't find user associated with this item in the catalog, try again or buy from someone else."
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            product = Product.objects.get(name=product_name, category=product_category)
            if (not product):  # se è a null vuol dire che qualcosa è andato male
                error = "Couldn't find the product associated with your request, try again or try to buy something else."
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

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
            buyer_balance = Balance.objects.get(user=buyer)  # find his balance

            # CONTROLLO BUDJET UTENTE
            if (float(buyer_balance.balance) - amount < (-1) * (BALANCE_LIMIT)):
                error = "You don't have enough credits (limit reached)."
                return Response({'error': error}, status=status.HTTP_403_FORBIDDEN)

            # non controllo se l'ha trovato o meno: ogni utente registrato ha un suo balance, se non ce l'avesse non troverei neanche l'utente!
            buyer_balance.balance = float(buyer_balance.balance) - amount  # update his balance
            buyer_balance.save()

            # save the transaction, price is negative cause it's a buy and not a sell
            new_entry = Transaction(product=product, user=buyer, amount=-amount)
            new_entry.save()

            """
            Operazione di vendita
            - recupero dalla post l'utente venditore
            - recupero il suo balance, e lo aggiorno
            - aggiungo una transazione per chi compra
            """
            seller_balance = Balance.objects.get(user=seller)  # find his balance
            # non controllo se l'ha trovato o meno: ogni utente registrato ha un suo balance, se non ce l'avesse non troverei neanche l'utente!
            seller_balance.balance = float(seller_balance.balance) + amount  # update his balance
            # SE IL BUDJET SFORA I 500, LO RIMETTE A 500
            if (seller_balance.balance > BALANCE_LIMIT):
                seller_balance.balance = BALANCE_LIMIT
            seller_balance.save()

            # save the transaction, price is negative cause it's a buy and not a sell
            new_entry = Transaction(product=product, user=seller, amount=amount)
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
            tracking = Product_pricetracker(seller=seller, product=product, price=price)
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
                fail_silently=True,
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
                fail_silently=True,
            )

            return Response({
                'product': product_name,
                'quantity': quantity,
                'price': price,
                'amount': -amount
            }, status=200)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class removeAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = removeSerializer(data=request.data)
        if serializer.is_valid():
            # Cerco di recuperare l'id dell'item associato
            item_id = serializer.data['id']
            try:
                item = Catalog.objects.get(id=item_id)
            except:
                error = "Couldn't find the item requested in catalog."
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

            # product informations
            product_name = item.product.name
            product_category = item.product.category
            quantity = item.quantity
            price = item.price
            user = item.user

            if user != request.user:
                error = "You're trying to remove an item that's not yours!"
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

            # controllo che il prodotto esista
            product = Product.objects.get(name=product_name, category=product_category)
            if (not product):  # se è a null vuol dire che qualcosa è andato male
                error = "Couldn't find the product associated with your request, try again."
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

            """
            Operazione di rimozione
            - elimino dal catalogo l'oggetto
            suppongo che l'oggetto sia sempre singolo, perchè controllo nella fase di inserimento
            (da valutare accesso concorrente)
            """
            item.delete()

            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""
###COMMUNITY API###
"""


class leaderboardAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        leaderboardserializer = BalanceSerializer(Balance.objects.filter().order_by('-balance'), many=True)
        for item in leaderboardserializer.data:
            username = User.objects.get(id=item['user']).username
            item['user'] = username
        top10serializer = BalanceSerializer(Balance.objects.filter().order_by('-balance')[:10], many=True)
        for item in top10serializer.data:
            username = User.objects.get(id=item['user']).username
            item['user'] = username
        worse10serializer = BalanceSerializer(Balance.objects.filter().order_by('-balance').reverse()[:10], many=True)
        for item in worse10serializer.data:
            username = User.objects.get(id=item['user']).username
            item['user'] = username

        context = {'balance': BalanceSerializer(utils.get_balance(request)).data,
                   'leaderboard': leaderboardserializer.data, 'top10': top10serializer.data,
                   'worse10': worse10serializer.data}
        return Response(context, status=status.HTTP_200_OK)


class profileAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        profile = None
        balance = None
        if user:
            """
            Diamo per scontato ci sia sempre un profilo per ogni utente
            """
            profile = Profile.objects.get(user=user)
            balance = Balance.objects.get(user=user)
        context = {'balance': BalanceSerializer(utils.get_balance(request)).data, 'user': UserSerializer(user).data,
                   'profile': ProfileSerializer(profile).data, 'profile_balance': BalanceSerializer(balance).data}

        # your profile page
        if user == request.user:
            context['yourself'] = True
        return Response(context, status=status.HTTP_200_OK)


class searchUserAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = searchSerializer(data=request.data)
        print(request.data)
        if serializer.is_valid():
            username = serializer.data['typed']
            if (username):
                try:
                    user = User.objects.get(username=username)
                    # qui dovresti reindirizzare, guardati i router
                    return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
                except:
                    error = 'User not found'
                    return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            error = 'You have to type something'
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        error = 'You have to type something valid'
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)


class modifyAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = modifySerializer(data=request.data)
        if serializer.is_valid():
            # obtaining arguments
            username = serializer.data['username']
            email = serializer.data['email']
            name = serializer.data['name']
            surname = serializer.data['surname']
            mobile = serializer.data['mobile']
            biography = serializer.data['biography']

            # create new user
            user = User.objects.get(username=username)

            # controlla che tu non abbia inserito la mail di un altro
            try:
                yep = User.objects.get(email=email)
                if (yep.username != username):
                    return Response({'error': 'email already present'}, status=status.HTTP_409_CONFLICT)
            except:
                print('no prob')

            user.email = email
            user.save()  # salvataggio in BACKEND

            # create new profile associated with that user
            profile = Profile.objects.get(user=user)
            profile.name = name
            profile.surname = surname
            profile.mobile = mobile
            profile.biography = biography
            profile.save()  # salvataggio in BACKEND

            response_serializer = ProfileSerializer(profile).data
            response_serializer['user'] = user.username

            return Response(response_serializer, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


"""
###ANALYTICS API####
"""


class historyAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        options = possibilities()
        your_history = Transaction.objects.filter(user=request.user)
        if your_history:
            transactions = {}
            lineChart = {}
            pieChart = {}
            for opt in options:
                ordered_transaction = retrieve_history(request, your_history, opt)
                lineChart[opt] = sum_dict(ordered_transaction)
                if opt != "settimana":
                    pieChart[opt] = sum_category(ordered_transaction[-1]['group'], Category.objects.all())
                # MODIFICATA RISPETTO ALL'ORIGINALE PER SERIALIZZARE I DATI
                # serializing (cause Transactions) - Recupera lista di dizionari, crea nuovi dizionari con key la nuova key e transaction serializzata
                ordered_transaction = [{key: (
                    [TransactionSerializer(transaction).data for transaction in values] if key == 'group' else values)
                                        for (key, values) in dictionaries.items()} for dictionaries in
                                       ordered_transaction]

                transactions[opt] = ordered_transaction
            context = {'balance': BalanceSerializer(utils.get_balance(request)).data, 'transactions': transactions,
                       'history': TransactionSerializer(your_history.order_by('-date'), many=True).data,
                       'lineChart': lineChart, 'pieChart': pieChart}
            return Response(context, status=status.HTTP_200_OK)
        else:
            error = 'No data found. Try our market!'
            return Response({'error': error}, status=status.HTTP_200_OK)


class priceTrackerAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, item):
        product = Product.objects.filter(name=item).first()
        if (product):
            lineChart = group_by_user(request, Product_pricetracker.objects.filter(product=product), item)
            context = {'balance': BalanceSerializer(utils.get_balance(request)).data, 'lineChart': lineChart,
                       'item': item}
            return Response(context, status=status.HTTP_200_OK)
        else:
            error = 'Product not found'
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)


class searchProductAPI(APIView):
    def post(self, request):
        serializer = searchSerializer(data=request.data)
        print(request.data)
        if serializer.is_valid():
            item = serializer.data['typed']
            if (item):
                item = item.capitalize()
                try:
                    product = Product.objects.get(name=item)
                    # qui dovresti reindirizzare, guardati i router
                    return Response(ProductSerializer(product).data, status=status.HTTP_200_OK)
                except:
                    error = 'Product not found'
                    return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            error = 'You have to type something'
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        error = 'You have to type something valid'
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
