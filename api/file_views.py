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
    ModifySerializer,
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
