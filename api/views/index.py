from rest_framework import status

from rest_framework.response import Response
from rest_framework.views import APIView


class Index(APIView):
    def get(self, _):
        return Response("hello", status=status.HTTP_200_OK)
