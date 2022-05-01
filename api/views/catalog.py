import django
from django.http import HttpRequest
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


class Insert(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: HttpRequest) -> Response:
        serializer = InsertSerializer(data=request.data)
        if serializer.is_valid():
            name: str = serializer.data["name"]
            price = float(serializer.data["price"])
            category: str = serializer.data["category"]
            quantity = int(serializer.data["quantity"])

            # Reduce duplication
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

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class catalogAPI(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest):
        user = request.user
        catalog = CatalogItemSerializer(
            CatalogItem.objects.filter(~Q(user=user)), many=True
        ).data
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
        groups = {
            item.get("product", None): [
                i
                for i in catalog
                if i.get("product", None) == item.get("product", None)
            ]
            for item in catalog
        }  # un set rimuove i duplicati da solo
        keys = sorted(keys)  # ordino
        # Trasformo il catalogo in una lista da QuerySet
        values = list(catalog)

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
