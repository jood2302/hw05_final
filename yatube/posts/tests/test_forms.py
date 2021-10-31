import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.form = PostForm()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тест группа',
            slug='testgroup',
            description='Тест описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.form_data = {
            'text': cls.post.text,
            'group': cls.group.id,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTest.user)
        self.guest_client = Client()

    def test_create_post(self):
        post_count = Post.objects.count()
        context = {
            'text': 'Текстовый текст',
            'group': PostFormTest.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=context,
            follow=True
        )
        post_last = Post.objects.order_by('-id')[0]
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={
                                         'username': PostFormTest.user}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(post_last.text, context['text'])
        self.assertEqual(post_last.group.id, context['group'])
        self.assertEqual(response.status_code, 200)

    def test_edit_post(self):
        post_count = Post.objects.count()
        context = {
            'text': 'Изменения в посте',
            'group': ''
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': PostFormTest.post.id}),
            data=context,
            follow=True
        )
        PostFormTest.post.refresh_from_db()
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': PostFormTest.post.id}))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(PostFormTest.post.text, context['text'])
        self.assertEqual(PostFormTest.post.group, None)

    def test_anonim_client_create_post(self):
        post_count = Post.objects.count()
        response = self.client.post(
            reverse('posts:post_create'),
            data=PostFormTest.form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response,
                             reverse('users:login') + '?next=' + reverse(
                                 'posts:post_create'))
        self.assertEqual(Post.objects.count(), post_count)

    def test_anonim_edit_post(self):
        context = {
            'text': 'Попытка изменить пост',
            'group': ''
        }
        response = self.client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': PostFormTest.post.id}),
            data=context,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + reverse(
                'posts:post_edit', kwargs={'post_id': PostFormTest.post.id}))
        self.assertNotEqual(PostFormTest.post.text, context['text'])
        self.assertNotEqual(PostFormTest.post.group.title, None)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormImageTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_create_post_with_image(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:profile', args=[self.user.username])
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                image='posts/small.gif'
            ).exists()
        )


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовый тайтл',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый текст',
            post=cls.post
        )
        cls.form = CommentForm()

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_add_comment(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.author_client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=[self.post.id]))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
            ).exists()
        )
