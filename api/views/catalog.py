from api.serializers.form_serializers import (
    BuySerializer,
    InsertSerializer,
    RemoveSerializer,
)
from api.serializers.model_serializers import (
    BalanceSerializer,
    CatalogItem,
    CatalogItemSerializer,
    Category,
    Product,
    User,
)
from common import utils
from django.db.models import Q
from django.http import HttpRequest
from rest_framework import status
from rest_framework.response import Response

from manager.models import BALANCE_LIMIT, Balance, Product_pricetracker, Transaction

from . import BaseAuthView


class Insert(BaseAuthView):
    def post(self, request: HttpRequest) -> Response:
        data = self._serialize(InsertSerializer, request)
        name: str = data["name"]
        price = float(data["price"])
        category: str = data["category"]
        quantity = int(data["quantity"])

        name = name.capitalize()
        if not (product := Product.objects.filter(name=name).first()):
            category_obj = Category.objects.get(name=category)
            product = Product(name=name, category=category_obj)
            product.save()

        item: CatalogItem
        if item := CatalogItem.objects.filter(
            user=request.user, product=product
        ).first():
            # If a product was already inserted in the catalog by the same user, update price and quantity
            item.price = price
            item.quantity = quantity + item.quantity
            item.save()
        else:
            # Create a new item in the catalog associated to that product, and to the current logged user
            new_item = CatalogItem(
                quantity=quantity, product=product, user=request.user, price=price
            )
            new_item.save()

        return Response(data, status=status.HTTP_200_OK)


class Catalog(BaseAuthView):
    def get(self, request: HttpRequest):
        """
        A partire dalla lista di elementi del catalogo, genero un insieme di gruppi:
        - la "key" di ogni gruppo è il nome del prodotto
        - il "items" di ogni gruppo è la lista di "vendite" di quel prodotto
        - "count" è un conteggio di quanti item ci sono
        """
        filtered = CatalogItem.objects.filter(~Q(user=request.user))
        catalog = CatalogItemSerializer(filtered, many=True).data
        groups = sorted(catalog, key=lambda item: item.product.name)
        context = {
            "groups": groups,
            "product_number": len(catalog),
            "balance": BalanceSerializer(utils.get_balance(request)).data,
        }
        return Response(context, status=200)


class UserItems(BaseAuthView):
    def get(self, request: HttpRequest):
        filtered = CatalogItem.objects.filter(user=request.user)
        catalog = CatalogItemSerializer(filtered, many=True).data
        context = {
            "catalog": catalog,
            "balance": BalanceSerializer(utils.get_balance(request)).data,
        }
        return Response(context, status=200)


class Buy(BaseAuthView):
    def _handleBuyer(
        self,
        item: CatalogItem,
        product: Product,
        amount: int,
        quantity: str,
        request: HttpRequest,
    ):
        """
        Operazione di acquisto
        - recupero l'utente acquirente
        - recupero il suo balance, e lo aggiorno
        - aggiungo una nuova transizione per l'utente, con ammontare negativo
        """
        buyer = request.user  # save current user
        buyer_balance: Balance = Balance.objects.get(user=buyer)  # find his balance
        buyer_balance.balance -= amount
        if buyer_balance.balance < -BALANCE_LIMIT:
            self._error("You don't have enough credits (limit reached).")
        buyer_balance.save()

        # TODO automatic?
        new_entry = Transaction(product=product, user=buyer, amount=-amount)
        new_entry.save()

        utils.send_html_mail(
            subject="Item bought",
            recipient_list=[buyer.email],
            html_content=f"""
            <html>
                <head></head>
            <body>
                <p>
                    Congratulation {buyer.username}, you just bought the following products:<br> 
                    <b>Product</b>: {product.name}<br>
                    <b>Quantity</b>: {quantity}<br>
                    <b>Price</b>: {item.price}<br>
                    <b>Total</b>: {-amount}<br>
                    <br>Your credit is now: {buyer_balance.balance}!<br> 
                    <a href="http://{request.get_host()}/market">Go back to market!</a>
                </p>
            </body>
            </html>
            """,
            fail_silently=True,
        )

    def _handleSeller(
        self,
        item: CatalogItem,
        product: Product,
        amount: int,
        quantity: str,
        request: HttpRequest,
    ):
        """
        Operazione di vendita
        - recupero dalla post l'utente venditore
        - recupero il suo balance, e lo aggiorno
        - aggiungo una transazione per chi compra
        """
        seller_balance: Balance = Balance.objects.get(user=item.user)
        # non controllo se l'ha trovato o meno: ogni utente registrato ha un suo balance, se non ce l'avesse non troverei neanche l'utente!
        seller_balance.balance += amount
        # SE IL BUDJET SFORA I 500, LO RIMETTE A 500
        if seller_balance.balance > BALANCE_LIMIT:
            seller_balance.balance = BALANCE_LIMIT
        seller_balance.save()

        # save the transaction, price is negative cause it's a buy and not a sell
        new_entry = Transaction(product=product, user=item.user, amount=amount)
        new_entry.save()

        residual = item.quantity - int(quantity)
        utils.send_html_mail(
            subject="Item sold",
            recipient_list=[item.user.email],
            html_content=f"""
            <html>
                <head></head>
            <body>
                <p>
                Congratulation {item.user.username}, somebody just bought the following products:<br> 
                <b>Product</b>: {product.name}<br>
                <b>Quantity</b>: {quantity}<br>
                <b>Price</b>: {item.price}<br>
                <b>Total</b>: {amount}<br>
                <br>Your credit is now: {seller_balance.balance}!<br> 
                    There are still {residual} of your "{product.name}" in the catalog!
                <a href="http://{request.get_host()}/market">Go back to market!</a>
                </p>
            </body>
            </html>
            """,
            fail_silently=True,
        )

    def _handleProduct(self, item: CatalogItem, product: Product, quantity: int, **_):
        """
        Qui si dovrebbe controllare se hai comprato tutto o ancora no. Per ora si compra sempre tutto
        Quando si compra anche l'ultimo item, bisogna togliere l'entry dal catalogo
        Si aggiunge inoltre una nuova entry nel pricetracker per analisi
        Tenere presente che forse bisognerebbe gestire l'accesso concorrente, nel senso che se due comprano simultaneamente ci possono essere casini grossi!
        """
        item.quantity -= quantity
        if item.quantity:
            item.save()
        else:
            item.delete()
        # add element in the tracker
        tracking = Product_pricetracker(
            seller=item.user, product=product, price=item.price
        )
        tracking.save()

    def _check(self, data: dict):
        quantity = int(data["quantity"])
        item_id = data["id"]
        try:
            item: CatalogItem = CatalogItem.objects.get(id=item_id)
        except Exception as _:
            status_code = status.HTTP_404_NOT_FOUND
            self._error("Couldn't find the item requested in catalog.", status_code)
        if quantity > item.quantity:
            self._error("You tried to buy, but we don't have that much!")
        return item, quantity

    def post(self, request: HttpRequest):
        data = self._serialize(InsertSerializer, request)
        item, quantity = self._check(data)

        product: Product = item.product
        amount = quantity * item.price
        params = {
            "product": product,
            "amount": amount,
            "quantity": quantity,
            "reqeust": request,
            "item": item,
        }
        self._handleProduct(**params)
        self._handleBuyer(**params)
        self._handleSeller(**params)

        return Response(
            {
                "product": product.name,
                "quantity": quantity,
                "price": item.price,
                "amount": -amount,
            },
            status=200,
        )


class Remove(BaseAuthView):
    def _check(self, data: dict):
        item_id = data["id"]
        try:
            item: CatalogItem = CatalogItem.objects.get(id=item_id)
        except:
            status_code = status.HTTP_404_NOT_FOUND
            self._error("Couldn't find the item requested in catalog.", status_code)
        return item

    def post(self, request):
        data = self._serialize(RemoveSerializer)
        item = self._check(data)
        if item.user != request.user:
            error = "You're trying to remove an item that's not yours!"
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
        item.delete()
        return Response(data, status=200)
