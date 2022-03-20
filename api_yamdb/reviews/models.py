from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from .validators import validation_of_the_year, validate_score


class User(AbstractUser):
    bio = models.TextField(
        max_length=500,
        blank=True,
    )
    email = models.EmailField(
        help_text="email address",
        unique=True,
    )

    class UserRole:
        USER = "user"
        ADMIN = "admin"
        MODERATOR = "moderator"
        choices = [
            (USER, "user"),
            (ADMIN, "admin"),
            (MODERATOR, "moderator"),
        ]

    role = models.CharField(
        max_length=25,
        choices=UserRole.choices,
        default=UserRole.USER,
    )
    confirmation_code = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]


class Category(models.Model):
    name = models.CharField(verbose_name="Категория", max_length=64)
    slug = models.SlugField(verbose_name="Адрес категории", unique=True)

    class Meta:
        verbose_name = "Категория"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(verbose_name="Жанр", max_length=64)
    slug = models.SlugField(verbose_name="Адрес жанра", unique=True)

    class Meta:
        verbose_name = "Жанр"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Title(models.Model):
    name = models.CharField(verbose_name="Произведение", max_length=64)
    description = models.TextField(
        verbose_name="Описание", blank=True, null=True
    )
    year = models.IntegerField(
        verbose_name="Дата выхода произведения",
        validators=[validation_of_the_year],
    )
    genre = models.ManyToManyField(
        Genre,
        verbose_name='Жанр',
        related_name='titles_as_genre',
        blank=True,
        null=True,
    )
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        related_name='titles_as_category',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        # on_delete=models.SET_NULL так как строка повторяеться
    )
    # добавил в модель рейтинг
    rating = models.PositiveSmallIntegerField(
        verbose_name='Рейтинг',
        help_text='Рейтинг произведения',
        null=True,
        validators=(validate_score,),
        blank=True,
    )

    class Meta:
        verbose_name = "Произведение"
        ordering = ["name"]

    def __str__(self):
        return self.name


# создание модели ревью
class Review(models.Model):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        help_text='Произведение к которому относится отзыв',
        related_name='review',
        verbose_name='Произведение'
    )
    score = models.PositiveSmallIntegerField(
        help_text='Новая оценка',
        verbose_name='Оценка произведения',
        validators=(validate_score,),
    )
    author = models.ForeignKey(
        User, #юзер не создан, автор ссылается на юзера
        on_delete=models.CASCADE,
        related_name='review'
    )
    text = models.TextField(
        help_text='Текст нового отзывы',
        verbose_name='Текст отзыва'
    )
    pub_date = models.DateTimeField(
        'Дата добавления', auto_now_add=True, db_index=True
    )

# создание сортировки по рейтингу
    class Meta:
        ordering = ('score',)
        # создание уникальных полей что б один юзер не оставлял 2 отзыва
        constraints = (
            models.UniqueConstraint(
                fields=('title', 'author'),
                name='uniq_author',
            ),
        )

    def __str__(self):
        return self.text[:15]


# создание модели коммент
class Comment(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        help_text='Произведение к которому относится коментарий',
        related_name='comments',
        verbose_name='Произведение'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
        help_text='Автор который оставил коментарий',
    )
    text = models.TextField(
        help_text='Текст нового коментария',
        verbose_name='Коментарий'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text='Дата добавления нового коментария',
        verbose_name='Дата'
    )

    class Meta:
        ordering = ('pub_date',)

    def __str__(self):
        return self.text[:15]
