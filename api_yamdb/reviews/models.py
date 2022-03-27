from django.db import models
from django.contrib.auth.models import AbstractUser
from .validators import validation_of_the_year, validate_score
from django.db.models import UniqueConstraint


class UserRoles:
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    USER_ROLES = (
        (USER, USER),
        (MODERATOR, MODERATOR),
        (ADMIN, ADMIN),
    )


class User(AbstractUser):

    email = models.EmailField(
        unique=True,
        blank=False,
        verbose_name='Электронная почта',
    )
    role = models.CharField(
        max_length=100,
        choices=UserRoles.USER_ROLES,
        default=UserRoles.USER,
        blank=False,
        verbose_name='Права доступа',
    )
    confirmation_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Код подтверждения',
    )
    username = models.CharField(
        blank=False,
        unique=True,
        max_length=150,
        verbose_name='Никнейм пользователя',
    )
    bio = models.TextField(
        blank=True,
        max_length=500,
        verbose_name='Биография',
    )
    first_name = models.CharField(
        blank=True,
        max_length=150,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        blank=True,
        max_length=150,
        verbose_name='Фамилия',
    )

    class Meta:
        verbose_name = 'Пользователь',
        verbose_name_plural = 'Пользователи',
        constraints = [
            UniqueConstraint(fields=['email', ], name='email'),
            UniqueConstraint(fields=['username', ], name='username')
        ]

    @property
    def is_admin(self):
        return self.role == UserRoles.ADMIN

    @property
    def is_moderator(self):
        return self.role == UserRoles.MODERATOR

    @property
    def is_user(self):
        return self.role == UserRoles.USER


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
        related_name='titles',
        blank=True,
        null=True,
    )
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        related_name='titles',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
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
        User,
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

    class Meta:
        ordering = ('score', 'pub_date')
        constraints = (
            models.UniqueConstraint(
                fields=('title', 'author'),
                name='uniq_author',
            ),
        )

    def __str__(self):
        return self.text[:15]


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
