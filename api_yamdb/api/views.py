import uuid

from django.core import exceptions
from django.core.mail import send_mail
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import filters, viewsets, status
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from reviews.models import Category, Genre, Title, User
from api_yamdb.settings import DEFAULT_FROM_EMAIL
from .mixins import CreateListViewSet
from .permissions import IsAdminOrReadOnly
from .filters import TitlesFilter
from .serializers import (
    CategorySerializer,
    GenreSerializer,
    TitlePostSerializer,
    TitleGetSerializer,
    UserSerializer,
    TokenSerializer,
    SignUpSerializer,
)


class CategoryViewSet(CreateListViewSet):
    queryset = Category.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = CategorySerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class GenreViewSet(CreateListViewSet):
    queryset = Genre.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = GenreSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class TitleViewSet(ModelViewSet):
    queryset = Title.objects.annotate(rating=Avg("reviews__score")).all()
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = TitlesFilter
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ["category", "genre", "year", "name"]

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return TitlePostSerializer
        return TitleGetSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = UserSerializer
    lookup_field = "username"
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "username",
    ]

    @action(
        methods=["patch", "get"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="me",
        url_name="me",
    )
    def me(self, request, *args, **kwargs):
        instance = self.request.user
        serializer = self.get_serializer(instance)
        if self.request.method == "PATCH":
            serializer = self.get_serializer(
                instance, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(email=instance.email, role=instance.role)
        return Response(serializer.data)


class EmailSignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get("email")
            confirmation_code = uuid.uuid4()
            User.objects.create(
                email=email,
                username=str(email),
                confirmation_code=confirmation_code,
                is_active=False,
            )
            send_mail(
                "Account verification",
                "Your activation key {}".format(confirmation_code),
                DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
            return Response(
                {"result": "A confirmation code has been sent to your email"},
                status=200,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CodeConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, *args, **kwargs):
        serializer = TokenSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(
                email=serializer.data["email"],
                confirmation_code=serializer.data["confirmation_code"],
            )
        except exceptions.ValidationError:
            return Response(
                data={"detail": "Invalid email or code"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            user.is_active = True
            user.save()
            refresh_token = RefreshToken.for_user(user)
            return Response({"token": str(refresh_token.access_token)})
