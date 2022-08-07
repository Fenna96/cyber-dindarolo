from typing import Optional, Type

from django.http import HttpRequest
from rest_framework import serializers, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class BaseView(APIView):
    def _error(self, msg: str, status: Optional[int] = status.HTTP_400_BAD_REQUEST):
        return Response({"error": msg}, status=status)

    def _serialize(self, cls: Type[serializers.Serializer], request: HttpRequest):
        serializer = cls(data=request.data)
        if serializer.is_valid():
            return serializer.data
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BaseAuthView(BaseView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
