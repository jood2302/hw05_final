from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Post, Group, Comment, Follow

User = get_user_model()


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def test_models_have_correct_object_names(self):
        group = PostModelTest.group
        expected_title = group.title
        self.assertEqual(expected_title, str(group))
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый текст комментария',
        )

    def test_comment_models_have_correct_object_names(self):
        """Проверяем, что у моделей comment корректно работает __str__."""
        comment = CommentModelTest.comment
        expected_comment_text = comment.text[:15]
        self.assertEqual(expected_comment_text, str(comment))


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='follower')
        cls.follow = Follow.objects.create(user=cls.user, author=cls.author)

    def test_follow_models_have_correct_object_names(self):
        follow = FollowModelTest.follow
        expected_user_username = follow.user.username
        self.assertEqual(expected_user_username, str(follow.user.username))
        expected_author_username = follow.author.username
        self.assertEqual(expected_author_username, str(follow.author.username))
