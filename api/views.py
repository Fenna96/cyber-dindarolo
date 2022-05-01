import django
from analytics.utils import (
    group_by_user,
    possibilities,
    retrieve_history,
    sum_category,
    sum_dict,
)
from common import utils
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q

from manager.models import BALANCE_LIMIT
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework.views import APIView
from user.models import DEFAULT_PIC_FILE, PROFILE_PIC_FOLDER

from api.serializers.form_serializers import (
    BuySerializer,
    InsertSerializer,
    LoginSerializer,
    ModifySerializer,
    RegistrationSerializer,
    RemoveSerializer,
    SearchSerializer,
)

from api.serializers.model_serializers import (
    Balance,
    BalanceSerializer,
    CatalogItem,
    CatalogItemSerializer,
    Category,
    Product,
    Product_pricetracker,
    ProductSerializer,
    Profile,
    ProfileSerializer,
    Transaction,
    TransactionSerializer,
    User,
    UserSerializer,
)


class Index(APIView):
    def get(self, _):
        return Response("hello", status=status.HTTP_200_OK)


"""
###MARKET API###
"""


class catalogAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        ##need to serialize
        catalog = CatalogItemSerializer(
            CatalogItem.objects.filter(~Q(user=user)), many=True
        ).data  # mostra solo ciò che vendono gli altri!
        for item in catalog:
            username = User.objects.get(id=item["user"]).username
            item["user"] = username
        """
        A partire dalla lista di elementi del catalogo, genero un insieme di gruppi:
        - la "key" di ogni gruppo è il nome del prodotto
        - il "items" di ogni gruppo è la lista di "vendite" di quel prodotto
        - "count" è un conteggio di quanti item ci sono

        ATTENZIONE: si parte dal presupposto che non ci siano prodotti con lo stesso nome
        """

        # GENERO LE CHIAVI, non duplicate e ordinate
        keys = {
            item.get("product", None) for item in catalog
        }  # un set rimuove i duplicati da solo
        keys = sorted(keys)  # ordino
        # Trasformo il catalogo in una lista da QuerySet
        values = [item for item in catalog]

        # Genero l'insieme di "gruppi", come indicato sopra
        groups = []
        for key in keys:
            new_dict = {}
            new_dict["key"] = key
            new_dict["items"] = []
            for item in values:
                # add value if key correspond
                if item.get("product", None) == key:
                    new_dict["items"].append(item)
            new_dict["items"] = sorted(
                new_dict["items"],
                key=lambda item: (item.get("price", None), item.get("quantity", None)),
            )
            new_dict["count"] = len(new_dict["items"])
            groups.append(new_dict)
        context = {
            "groups": groups,
            "product_number": len(catalog),
            "balance": BalanceSerializer(utils.get_balance(request)).data,
        }
        return Response(context, status=200)


class user_itemsAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        ##need to serialize
        catalog = CatalogItemSerializer(
            CatalogItem.objects.filter(user=request.user), many=True
        ).data  # mostra solo ciò che vendono gli altri!

        context = {
            "catalog": catalog,
            "balance": BalanceSerializer(utils.get_balance(request)).data,
        }
        return Response(context, status=200)


class buyAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BuySerializer(data=request.data)
        if serializer.is_valid():
            quantity = serializer.data["quantity"]
            item_id = serializer.data["id"]
            try:
                item = CatalogItem.objects.get(id=item_id)
            except:
                error = "Couldn't find the item requested in catalog."
                return Response({"error": error}, status=status.HTTP_404_NOT_FOUND)

            # se funzia, recupero i vari campi dell'item
            product_name = item.product.name
            product_category = item.product.category
            seller = item.user
            price = item.price
            max_quantity = item.quantity

            # ERRORS!
            # controllo che esistano prodotto e venditore
            if int(quantity) > int(max_quantity):
                error = "You tried to buy, but we don't have that much!"
                return Response({"error": error}, status=status.HTTP_404_NOT_FOUND)
            seller = User.objects.get(username=seller)
            if not seller:  # se è a null qualcosa è andato male
                error = "Couldn't find user associated with this item in the catalog, try again or buy from someone else."
                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
            product = Product.objects.get(name=product_name, category=product_category)
            if not product:  # se è a null vuol dire che qualcosa è andato male
                error = "Couldn't find the product associated with your request, try again or try to buy something else."
                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

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
            if float(buyer_balance.balance) - amount < (-1) * (BALANCE_LIMIT):
                error = "You don't have enough credits (limit reached)."
                return Response({"error": error}, status=status.HTTP_403_FORBIDDEN)

            # non controllo se l'ha trovato o meno: ogni utente registrato ha un suo balance, se non ce l'avesse non troverei neanche l'utente!
            buyer_balance.balance = (
                float(buyer_balance.balance) - amount
            )  # update his balance
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
            seller_balance.balance = (
                float(seller_balance.balance) + amount
            )  # update his balance
            # SE IL BUDJET SFORA I 500, LO RIMETTE A 500
            if seller_balance.balance > BALANCE_LIMIT:
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
            if int(quantity) == int(max_quantity):
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
                subject="Item bought",
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
                subject="Item sold",
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

            return Response(
                {
                    "product": product_name,
                    "quantity": quantity,
                    "price": price,
                    "amount": -amount,
                },
                status=200,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class removeAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RemoveSerializer(data=request.data)
        if serializer.is_valid():
            # Cerco di recuperare l'id dell'item associato
            item_id = serializer.data["id"]
            try:
                item = CatalogItem.objects.get(id=item_id)
            except:
                error = "Couldn't find the item requested in catalog."
                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

            # product informations
            product_name = item.product.name
            product_category = item.product.category
            quantity = item.quantity
            price = item.price
            user = item.user

            if user != request.user:
                error = "You're trying to remove an item that's not yours!"
                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

            # controllo che il prodotto esista
            product = Product.objects.get(name=product_name, category=product_category)
            if not product:  # se è a null vuol dire che qualcosa è andato male
                error = (
                    "Couldn't find the product associated with your request, try again."
                )
                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

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
        leaderboardserializer = BalanceSerializer(
            Balance.objects.filter().order_by("-balance"), many=True
        )
        for item in leaderboardserializer.data:
            username = User.objects.get(id=item["user"]).username
            item["user"] = username
        top10serializer = BalanceSerializer(
            Balance.objects.filter().order_by("-balance")[:10], many=True
        )
        for item in top10serializer.data:
            username = User.objects.get(id=item["user"]).username
            item["user"] = username
        worse10serializer = BalanceSerializer(
            Balance.objects.filter().order_by("-balance").reverse()[:10], many=True
        )
        for item in worse10serializer.data:
            username = User.objects.get(id=item["user"]).username
            item["user"] = username

        context = {
            "balance": BalanceSerializer(utils.get_balance(request)).data,
            "leaderboard": leaderboardserializer.data,
            "top10": top10serializer.data,
            "worse10": worse10serializer.data,
        }
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
        context = {
            "balance": BalanceSerializer(utils.get_balance(request)).data,
            "user": UserSerializer(user).data,
            "profile": ProfileSerializer(profile).data,
            "profile_balance": BalanceSerializer(balance).data,
        }

        # your profile page
        if user == request.user:
            context["yourself"] = True
        return Response(context, status=status.HTTP_200_OK)


class searchUserAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SearchSerializer(data=request.data)
        print(request.data)
        if serializer.is_valid():
            username = serializer.data["typed"]
            if username:
                try:
                    user = User.objects.get(username=username)
                    # qui dovresti reindirizzare, guardati i router
                    return Response(
                        UserSerializer(user).data, status=status.HTTP_200_OK
                    )
                except:
                    error = "User not found"
                    return Response(
                        {"error": error}, status=status.HTTP_400_BAD_REQUEST
                    )
            error = "You have to type something"
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
        error = "You have to type something valid"
        return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)


class modifyAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ModifySerializer(data=request.data)
        if serializer.is_valid():
            # obtaining arguments
            username = serializer.data["username"]
            email = serializer.data["email"]
            name = serializer.data["name"]
            surname = serializer.data["surname"]
            mobile = serializer.data["mobile"]
            biography = serializer.data["biography"]

            # create new user
            user = User.objects.get(username=username)

            # controlla che tu non abbia inserito la mail di un altro
            try:
                yep = User.objects.get(email=email)
                if yep.username != username:
                    return Response(
                        {"error": "email already present"},
                        status=status.HTTP_409_CONFLICT,
                    )
            except:
                print("no prob")

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
            response_serializer["user"] = user.username

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
                    pieChart[opt] = sum_category(
                        ordered_transaction[-1]["group"], Category.objects.all()
                    )
                # MODIFICATA RISPETTO ALL'ORIGINALE PER SERIALIZZARE I DATI
                # serializing (cause Transactions) - Recupera lista di dizionari, crea nuovi dizionari con key la nuova key e transaction serializzata
                ordered_transaction = [
                    {
                        key: (
                            [
                                TransactionSerializer(transaction).data
                                for transaction in values
                            ]
                            if key == "group"
                            else values
                        )
                        for (key, values) in dictionaries.items()
                    }
                    for dictionaries in ordered_transaction
                ]

                transactions[opt] = ordered_transaction
            context = {
                "balance": BalanceSerializer(utils.get_balance(request)).data,
                "transactions": transactions,
                "history": TransactionSerializer(
                    your_history.order_by("-date"), many=True
                ).data,
                "lineChart": lineChart,
                "pieChart": pieChart,
            }
            return Response(context, status=status.HTTP_200_OK)
        else:
            error = "No data found. Try our market!"
            return Response({"error": error}, status=status.HTTP_200_OK)


class priceTrackerAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, item):
        product = Product.objects.filter(name=item).first()
        if product:
            lineChart = group_by_user(
                request, Product_pricetracker.objects.filter(product=product), item
            )
            context = {
                "balance": BalanceSerializer(utils.get_balance(request)).data,
                "lineChart": lineChart,
                "item": item,
            }
            return Response(context, status=status.HTTP_200_OK)
        else:
            error = "Product not found"
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)


class searchProductAPI(APIView):
    def post(self, request):
        serializer = SearchSerializer(data=request.data)
        print(request.data)
        if serializer.is_valid():
            item = serializer.data["typed"]
            if item:
                item = item.capitalize()
                try:
                    product = Product.objects.get(name=item)
                    # qui dovresti reindirizzare, guardati i router
                    return Response(
                        ProductSerializer(product).data, status=status.HTTP_200_OK
                    )
                except:
                    error = "Product not found"
                    return Response(
                        {"error": error}, status=status.HTTP_400_BAD_REQUEST
                    )
            error = "You have to type something"
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
        error = "You have to type something valid"
        return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
