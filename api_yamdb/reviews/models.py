from django.db import models

from .validators import validation_of_the_year


class Category(models.Model):
    name = models.CharField(
        verbose_name='Категория',
        max_length=64,
    )
    slug = models.SlugField(
        verbose_name='Адрес категории',
        unique=True,
    )

    class Meta:
        verbose_name = 'Категория'
        ordering = ['name']

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(
        verbose_name='Жанр',
        max_length=64
    )
    slug = models.SlugField(
        verbose_name='Адрес жанра',
        unique=True
    )

    class Meta:
        verbose_name = 'Жанр'
        ordering = ['name']

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(
        verbose_name='Произведение',
        max_length=64
    )
    description = models.TextField(
        verbose_name='Описание',
        blank=True,
        null=True
    )
    year = models.IntegerField(
        verbose_name='Дата выхода произведения',
        validators=[validation_of_the_year]
    )
    genre = models.ManyToManyField(
        Genre,
        verbose_name='Жанр',
        related_name='titles',
        blank=True,
        null=True
    )
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        related_name='titles',
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = 'Произведение'
        ordering = ['name']

    def __str__(self):
        return self.name
