import uuid

from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.tokens import default_token_generator
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import filters, viewsets, status
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from reviews.models import Category, Genre, Title, Review, User
from api_yamdb.settings import DEFAULT_FROM_EMAIL
from .mixins import CreateListViewSet
from .permissions import (
    IsAdminOrReadOnly,
    AuthorOrAdminOrModeratorReadOnly,
    IsAdmin,
)
from .filters import TitlesFilter
from .serializers import (
    CategorySerializer,
    GenreSerializer,
    TitlePostSerializer,
    TitleGetSerializer,
    CommentSerializer,
    ReviewSerializer,
    UserSerializer,
    TokenSerializer,
    SignupSerializer,
)


class CategoryViewSet(CreateListViewSet):
    queryset = Category.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = CategorySerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
    lookup_field = "slug"


class GenreViewSet(CreateListViewSet):
    queryset = Genre.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = GenreSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
    lookup_field = "slug"


class TitleViewSet(ModelViewSet):
    queryset = (Title.objects.annotate(rating=Avg('reviews__score'))
                .order_by('category'))
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = TitlesFilter
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ["category", "genre", "year", "name"]

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return TitlePostSerializer
        return TitleGetSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (AuthorOrAdminOrModeratorReadOnly,)

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, id=title_id)
        return title.reviews.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, id=title_id)
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (AuthorOrAdminOrModeratorReadOnly,)

    def get_queryset(self):
        review = get_object_or_404(Review, id=self.kwargs.get("review_id"))
        return review.comments.all()

    def perform_create(self, serializer):
        review_id = self.kwargs.get("review_id")
        review = get_object_or_404(Review, pk=review_id)
        serializer.save(author=self.request.user, review=review)


class APISignup(APIView):
    """View для регистрации и создания пользователя
    с последующей отсылкой confirmation code на email этого пользователя."""

    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        email = serializer.validated_data["email"]

        username_exists = User.objects.filter(username=username).exists()
        email_exists = User.objects.filter(email=email).exists()

        if not username_exists and not email_exists:
            user = User.objects.create(username=username, email=email)
        else:
            if not username_exists:
                return Response(
                    "Ошибка, email занят, просьба выбрать другой email.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = get_object_or_404(User, username=username)
            if user.email != email:
                return Response(
                    "Ошибка, у пользователя другой email.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
        token = default_token_generator.make_token(user)
        send_mail(
            subject="Ваш код для получения api-токена.",
            message=f"Код: {token}",
            from_email=DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAdmin,)
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
        serializer = SignupSerializer(data=request.data)
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

    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User, username=serializer.validated_data.get("username")
        )
        token = AccessToken.for_user(user)
        return Response(data={"token": str(token)}, status=status.HTTP_200_OK)
