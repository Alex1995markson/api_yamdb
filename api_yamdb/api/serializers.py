from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from reviews.models import Category, Genre, Title, User, Comment, Review

SIGNUP_ERROR_MESSAGE = "Ошибка, имя me зарезервировано системой."
USERNAME_REGEX = r"^[\w.@+-]+$"


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        exclude = ["id"]


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        exclude = ["id"]


class TitlePostSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field="slug", queryset=Category.objects.all()
    )
    genre = serializers.SlugRelatedField(
        slug_field="slug", queryset=Genre.objects.all(), many=True
    )

    class Meta:
        fields = "__all__"
        model = Title


class TitleGetSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    genre = GenreSerializer(many=True)
    #rating = serializers.IntegerField(read_only=True)

    class Meta:
        fields = "__all__"
        model = Title


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field="username",
        default=serializers.CurrentUserDefault(),
    )
    title = serializers.SlugRelatedField(
        slug_field="id", many=False, read_only=True
    )

    def validate(self, data):
        request = self.context["request"]
        title_id = self.context.get("view").kwargs.get("title_id")
        title = get_object_or_404(Title, pk=title_id)
        if (
            request.method == "POST"
            and Review.objects.filter(
                title=title, author=request.user
            ).exists()
        ):
            raise ValidationError("Можно оставить только один отзыв")
        return data

    class Meta:
        fields = "__all__"
        model = Review

    def validate_score(self, value):
        if value > 10 or value < 1:
            raise serializers.ValidationError("Не коректно указанный рейтинг!")
        return value


class CommentSerializer(serializers.ModelSerializer):
    review = serializers.SlugRelatedField(slug_field="text", read_only=True)
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field="username",
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Comment
        fields = ("id", "text", "author", "pub_date", "review")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "bio",
        )
        model = User


class SignupSerializer(serializers.Serializer):
    """Сериалазер без модели, для полей username и email."""

    username = serializers.RegexField(regex=USERNAME_REGEX, max_length=150)
    email = serializers.EmailField()

    def validate_username(self, value):
        if value == "me":
            raise serializers.ValidationError(SIGNUP_ERROR_MESSAGE)
        return value


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100, required=True)
    confirmation_code = serializers.CharField(max_length=20, required=True)

    def validate(self, data):
        user = get_object_or_404(User, username=data["username"])
        if user.confirmation_code != data["confirmation_code"]:
            raise serializers.ValidationError(
                "Не совпадает код подтверждения!"
            )
        return data

    class Meta:
        fields = (
            "username",
            "confirmation_code",
        )
        model = User
