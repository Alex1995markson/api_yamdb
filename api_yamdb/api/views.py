from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import filters
from rest_framework.viewsets import ModelViewSet

from reviews.models import Category, Genre, Title
from .mixins import CreateListViewSet
from .permissions import IsAdminOrReadOnly
from .filters import TitlesFilter
from .serializers import (CategorySerializer, GenreSerializer,
                          TitlePostSerializer, TitleGetSerializer)


class CategoryViewSet(CreateListViewSet):
    queryset = Category.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = CategorySerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class GenreViewSet(CreateListViewSet):
    queryset = Genre.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = GenreSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class TitleViewSet(ModelViewSet):
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
