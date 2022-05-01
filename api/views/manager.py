from common import utils
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework.views import APIView
from api.serializers.model_serializers import (
    BalanceSerializer,
    Profile,
    ProfileSerializer,
)


class Manager(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        context = {
            "profile": ProfileSerializer(Profile.objects.get(user=request.user)).data,
            "balance": BalanceSerializer(utils.get_balance(request)).data,
        }
        return Response(context, status=200)
