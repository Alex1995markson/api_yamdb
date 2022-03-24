import uuid

from django.core import exceptions
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
# from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import filters, viewsets, status
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.tokens import AccessToken

from reviews.models import Category, Genre, Title, Review, User
from api_yamdb.settings import DEFAULT_FROM_EMAIL
from .mixins import CreateListViewSet
from .permissions import (IsAdminOrReadOnly,
                          AuthorOrAdminOrModeratorReadOnly,
                          IsAdmin)
from .filters import TitlesFilter
from .serializers import (CategorySerializer,
                          GenreSerializer,
                          TitlePostSerializer,
                          TitleGetSerializer,
                          CommentSerializer,
                          ReviewSerializer,
                          UserSerializer,
                          TokenSerializer,
                          SignupSerializer)


class CategoryViewSet(CreateListViewSet):
    queryset = Category.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = CategorySerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class GenreViewSet(CreateListViewSet):
    queryset = Genre.objects.all()
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = GenreSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
    lookup_field = ('slug')


class TitleViewSet(ModelViewSet):
    queryset = Title.objects.all()
    # rating=Avg("reviews__score")).order_by('category')
    # queryset = Title.objects.annotate(rating=Avg("reviews__score")).all()
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = TitlesFilter
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ["category", "genre", "year", "name"]

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return TitlePostSerializer
        return TitleGetSerializer


# class ReviewViewSet(ModelViewSet):
#     serializer_class = ReviewSerializer
#     permission_classes = (IsAdminOrAuthorOrReadOnly,)

#     def perform_create(self, serializer):
#         title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
#         if Review.objects.filter(
#                 title=title, author=self.request.user
#         ).exists():
#             raise ValidationError('Можно оставить только один отзыв')
#         serializer.save(author=self.request.user, title=title)

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (AuthorOrAdminOrModeratorReadOnly,)

    @staticmethod
    def rating_calculation(title):
        int_rating = title.review.all().aggregate(Avg('score'))
        title.rating = int_rating['score__avg']
        title.save(update_fields=['rating'])

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        self.rating_calculation(title)
        return title.review.all()

    def perform_create(self, serializer):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        if Review.objects.filter(
                title=title, author=self.request.user
        ).exists():
            raise ValidationError('Можно оставить только один отзыв')
        self.rating_calculation(title)
        serializer.save(author=self.request.user, title=title)

    def perform_update(self, serializer):
        serializer.save()
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        self.rating_calculation(title)


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (AuthorOrAdminOrModeratorReadOnly,)

    def get_queryset(self):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        return review.comments.all()

    def perform_create(self, serializer):
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, pk=review_id)
        serializer.save(author=self.request.user, review=review)


class APISignup(APIView):
    """View для регистрации и создания пользователя
    с последующей отсылкой confirmation code на email этого пользователя."""

    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        email = serializer.validated_data['email']

        username_exists = User.objects.filter(username=username).exists()
        email_exists = User.objects.filter(email=email).exists()

        if not username_exists and not email_exists:
            user = User.objects.create(username=username, email=email)
        else:
            if not username_exists:
                return Response(
                    "Ошибка, email занят, просьба выбрать другой email.",
                    status=status.HTTP_400_BAD_REQUEST
                )
            user = get_object_or_404(User, username=username)
            if user.email != email:
                return Response(
                    "Ошибка, у пользователя другой email.",
                    status=status.HTTP_400_BAD_REQUEST
                )
        token = default_token_generator.make_token(user)
        send_mail(
            subject='Ваш код для получения api-токена.',
            message=f'Код: {token}',
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


class CreateToken(APIView):
    """Создание токена."""
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        confirmation_code = serializer.validated_data['confirmation_code']
        username = serializer.validated_data['username']
        user = get_object_or_404(User, username=username)
        print(user)
        if default_token_generator.check_token(
            user,
            confirmation_code
        ):
            token = AccessToken.for_user(user)
            return Response(
                {"token": f"{token}"},
                status=status.HTTP_200_OK
            )
        return Response(
            "Confirm code invalid",
            status=status.HTTP_404_NOT_FOUND
        )
