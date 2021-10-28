from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)

    def test_urls_exists(self):
        open_urls_names = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.author.username}/',
            f'/posts/{self.post.pk}/',
        ]
        for address in open_urls_names:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_user.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_author.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_404(self):
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_redirect(self):
        urls_names = [
            '/create/',
            f'/posts/{self.post.pk}/edit/',
        ]
        for address in urls_names:
            with self.subTest(address=address):
                response = self.client.get(address, follow=True)
                self.assertRedirects(
                    response, (
                        f'/auth/login/?next={address}'
                    )
                )
        response = self.authorized_user.get(
            f'/posts/{self.post.pk}/edit/', follow=True
        )
        self.assertRedirects(
            response, (
                f'/posts/{self.post.pk}/'
            )
        )

    def test_correct_template(self):
        url_templates_names = {
            '/': 'posts/index.html',
            f'/profile/{self.author.username}/':
                'posts/profile.html',
            f'/posts/{self.post.pk}/edit/':
                'posts/create_post.html',
            f'/posts/{self.post.pk}/':
                'posts/post_detail.html',
            f'/group/{self.group.slug}/':
                'posts/group_list.html',
            '/create/': 'posts/create_post.html',
        }
        for reverse_name, template in url_templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_add_comment_url_exists_at_desired_location_anonymous(self):
        response = self.client.get(
            reverse('posts:add_comment', args=[self.post.id]), follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/comment')
