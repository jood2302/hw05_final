from django.db import models
from django.db.models import constraints
from django.contrib.auth import get_user_model

from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name="Текст сообщения",
                            help_text="Обязательное поле,\
                             не должно быть пустым")
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True, related_name="posts",
        verbose_name="Автор",
        help_text="Выберите имя автора"
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        blank=True,
        null=True, related_name="posts",
        verbose_name="Группа",
        help_text="Выберите название группы"
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        default_related_name = 'posts'

    def __str__(self) -> str:
        return self.text


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост, к которому прикрепляется комментарий',
        help_text='Укажите пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        help_text='Введите автора',
    )
    text = models.TextField(
        verbose_name='Текст',
        help_text='Введите текст'
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь',
        help_text='Укажите подписчика'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
        help_text='Укажите автора'
    )

    class Meta:
        constraints = (
            constraints.UniqueConstraint(
                fields=('user', 'author'), name='follow_unique'),
        )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return self.user.username, self.author.username
