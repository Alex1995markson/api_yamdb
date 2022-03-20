from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from reviews.models import Category, Genre, Title, Review
from .mixins import CreateListViewSet
from .permissions import IsAdminOrReadOnly, IsAdminOrAuthorOrReadOnly
from .filters import TitlesFilter
from .serializers import (CategorySerializer, GenreSerializer,
                          TitlePostSerializer, TitleGetSerializer,
                          CommentSerializer, ReviewSerializer)


class CategoryViewSet(CreateListViewSet):
    """
    Создание и удаление категории
    Получение списка категорий
    """
    queryset = Category.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = CategorySerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class GenreViewSet(CreateListViewSet):
    """
    Создание и удаление жанра
    Получение списка жанров
    """
    queryset = Genre.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = GenreSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class TitleViewSet(ModelViewSet):
    """
    Добавление нового произведения
    Обновление и удаление произведения
    Возврат информации о произведение
    Возврат списка произведений
    """
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')
    ).all()
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = TitlesFilter
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['category', 'genre', 'year', 'name']

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return TitlePostSerializer
        return TitleGetSerializer


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (IsAdminOrAuthorOrReadOnly,)

    def perform_create(self, serializer):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        if Review.objects.filter(
                title=title, author=self.request.user
        ).exists():
            raise ValidationError('Можно оставить только один отзыв')
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (IsAdminOrAuthorOrReadOnly,)

    def get_queryset(self):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        return review.comments.all()

    def perform_create(self, serializer):
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, pk=review_id)
        serializer.save(author=self.request.user, review=review)
