from typing import Callable
from django.http import HttpRequest
from common import utils
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.middleware.csrf import get_token

from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework.views import APIView
from user.models import DEFAULT_PIC_FILE, PROFILE_PIC_FOLDER

from api.serializers.form_serializers import (
    LoginSerializer,
    RegistrationSerializer,
)

from api.serializers.model_serializers import (
    Balance,
    Profile,
    User,
)


def registered(func: Callable):
    def check(self: APIView, request: HttpRequest):
        if request.user.is_authenticated:
            return Response(
                {"token": get_token(request)},
                status=status.HTTP_302_FOUND,
            )
        return func(self, request)

    return check


class Login(APIView):
    """
    Defines a POST method that logs the user in.

    Data are validated through the LoginSerializer. Not only the data
    must be valid, but it's mandatory that an User with the provided
    username and password already exists in the DB, and is active.

    If an user was already logged in before the request, nothing is done
    """

    @registered
    def post(self, request: HttpRequest) -> Response:
        "Log the user in"
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.data["username"]
            password = serializer.data["password"]
            user = authenticate(username=username, password=password)
            if user and user.is_active:
                login(request, user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(
                {"error": "Wrong username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Logout(APIView):
    """
    Defines a GET method that logs the user out.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        logout(request)
        return Response(None, status=status.HTTP_200_OK)


class Registration(APIView):
    """
    Defines a POST method to register a new user.

    All data received are parsed using the RegistrationSerializer. The whole process creates:
    -   A new User object with email, username and password provided
    -   A Profile connected to the user with the remaining data of the serializer
    -   An empty balance connected to the user

    The process can fail only in three cases:
    -   There's a currently logged user
    -   Serializer validation fails
    -   Another user with the same username and email is found in DB
    """

    def sendRegistrationEmail(self, username: str, email: str, request: HttpRequest):
        """
        Send a completed registration email to the registrant. No error is thrown if something goes wrong
        """
        utils.send_html_mail(
            subject="Welcome to our community!",
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

    def createUser(self, username: str, password: str, email: str) -> User:
        "Create a new user object starting from the data provided"
        user: User = User.objects.create_user(username, email)
        user.set_password(password)
        user.save()
        return user

    def createProfile(
        self,
        user: User,
        name: str,
        surname: str,
        mobile: str,
        biography: str,
        profile_image: str,
    ):
        "Create a new profile object for a user starting from the data provided"
        profile = Profile(
            user=user,
            name=name,
            surname=surname,
            mobile=mobile,
            biography=biography,
            profile_image=profile_image,
        )
        profile.save()

    def createBalance(user: User):
        "Create a new balance object for a user starting from the data provided"
        balance = Balance(user=user, balance=0)
        balance.save()

    @registered
    def post(self, request: HttpRequest):
        "Register a new user"
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.data["username"]
            email = serializer.data["email"]

            if User.objects.filter(Q(username=username) | Q(email=email)):
                error = "Username or email already in use."
                return Response({"error": error}, status=status.HTTP_409_CONFLICT)

            password = serializer.data["password"]
            name = serializer.data["name"]
            surname = serializer.data["surname"]
            mobile = serializer.data["mobile"]
            biography = serializer.data["biography"]
            profile_image = serializer.data["profile_image"]

            profile_image = (
                f"{PROFILE_PIC_FOLDER}{profile_image}"
                if profile_image
                else DEFAULT_PIC_FILE
            )

            self.sendRegistrationEmail(username, email, request)
            user = self.createUser(username, password, email)
            self.createProfile(user, name, surname, mobile, biography, profile_image)
            self.createBalance(user)

            login(request, authenticate(username=username, password=password))
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Token(APIView):
    """
    Defines a GET method to retrieve the currently logged user token-
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        "Get the token of the currently logged user"
        context = {"token": get_token(request)}
        return Response(context, status=200)
