from api.serializers.model_serializers import Balance, BalanceSerializer
from common import utils
from django.http import HttpRequest
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class Navbar(APIView):
    """
    Defines a GET method that provides some usefull info about the
    currently logged user and its balance.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest):
        "Get user and balance info"
        balance: Balance = utils.get_balance(request)
        balance_data = BalanceSerializer(balance).data
        balance_data["user"] = request.user.username
        context = {"balance": balance_data}
        return Response(context, status=200)
