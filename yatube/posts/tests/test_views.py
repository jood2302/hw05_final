import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Comment, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


class TaskPagesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тест',
            slug='12',
        )
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group
        )
        self.form_data = {
            'text': self.post.text,
            'group': self.group.id,
        }
        self.new_post = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.public_index_template = 'posts/index.html'
        self.public_group_page_template = 'posts/group_list.html'
        self.private_create_post_template = 'posts/create_post.html'
        self.private_edit_post_template = 'posts/create_post.html'
        self.public_profile = 'posts/profile.html'
        self.public_post = 'posts/post_detail.html'

    def test_pages_use_correct_template(self):
        cache.clear()
        templates_pages_names = {
            self.public_index_template: reverse('posts:index'),
            self.public_profile: reverse('posts:profile',
                                         kwargs={'username': self.user}),
            self.public_post: reverse('posts:post_detail',
                                      kwargs={'post_id': self.post.id}),
            self.private_edit_post_template: reverse('posts:post_edit',
                                                     kwargs={'post_id':
                                                             self.post.id}),
            self.private_create_post_template: reverse('posts:post_create'),
            self.public_group_page_template: (
                reverse('posts:group_list', kwargs={'slug': self.group.slug})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertTemplateUsed(response, self.private_create_post_template)

    def test_context(self):
        cache.clear()
        url_names = [reverse('posts:index'),
                     reverse('posts:post_detail',
                             kwargs={'post_id': self.post.id}),
                     reverse('posts:post_edit',
                             kwargs={'post_id': self.post.id}),
                     reverse('posts:group_list',
                             kwargs={'slug': self.group.slug}),
                     reverse('posts:profile',
                             kwargs={'username': self.user.username})]
        for url in url_names:
            response = self.authorized_client.get(url)
            self.assertContains(response, self.form_data['text'])
            self.assertContains(response, self.user)
            self.assertContains(response, self.group.id)
            self.assertContains(response, self.post.id)

    def test_check_post_in_group(self):
        t_group = Group.objects.create(
            title='Заголовок',
            slug='test',
            description='Текст',
        )
        Group.objects.create(
            title='Заголовок1',
            slug='test1',
            description='Текст1',
        )
        Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=t_group,
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertEqual(response.context['group'].title, self.group.title)
        self.assertEqual(response.context['group'].slug, self.group.slug)
        self.assertEqual(response.context['group'].description,
                         self.group.description)
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_group = first_object.group
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_group.title, self.group.title)
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertFalse(response.context['page_obj'].has_next())

    def test_chech_post_in_index_and_profile(self):
        cache.clear()
        templates_pages_names = {reverse('posts:index'),
                                 reverse('posts:profile',
                                 kwargs={'username': self.user.username})}
        for reverse_name in templates_pages_names:
            response = self.authorized_client.get(
                reverse_name)
            first_object = response.context['page_obj'][0]
            post_text = first_object.text
            self.assertEqual(post_text, self.post.text)
            first_object = response.context['page_obj'][0]
            post_text = first_object.text
            self.assertFalse(response.context['page_obj'].has_next())


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовая группа',
        )
        cls.post = settings.POST_COUNT + 3
        for cls.post in range(settings.POST_COUNT + 3):
            cls.post = Post.objects.create(
                text='Тестовый текст',
                author=cls.user,
                group=cls.group
            )

    def test_first_page_contains_ten_records(self):
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         settings.POST_COUNT)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_first_page_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={
                'slug': PaginatorTests.group.slug
            })
        )
        self.assertEqual(len(response.context['page_obj']),
                         settings.POST_COUNT)

    def test_group_second_page_contains_three_records(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={
                'slug': PaginatorTests.group.slug
            }) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_profile_first_page_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={
                'username': PaginatorTests.user.username,
            })
        )
        self.assertEqual(len(response.context['page_obj']),
                         settings.POST_COUNT)

    def test_profile_second_page_contains_three_records(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={
                'username': PaginatorTests.user.username,
            }) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostImageExistTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовый тайтл',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_post_with_image_exist(self):
        self.assertTrue(Post.objects.filter(image='posts/small.gif'))

    def test_index_show_correct_image_in_context(self):
        cache.clear()
        response = self.author_client.get(reverse('posts:index'))
        test_object = response.context['page_obj'][0]
        post_image = test_object.image
        self.assertEqual(post_image, 'posts/small.gif')

    def test_post_detail_image_exist(self):
        response = self.author_client.get(
            reverse('posts:post_detail', args=[self.post.id])
        )
        test_object = response.context['post']
        post_image = test_object.image
        self.assertEqual(post_image, 'posts/small.gif')

    def test_group_and_profile_image_exist(self):
        templates_pages_name = {
            'posts:group_list': self.group.slug,
            'posts:profile': self.user.username,
        }
        for names, args in templates_pages_name.items():
            with self.subTest(names=names):
                response = self.author_client.get(reverse(names, args=[args]))
                test_object = response.context['page_obj'][0]
                post_image = test_object.image
                self.assertEqual(post_image, 'posts/small.gif')


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create_user(username='follower')
        cls.follower_client = Client()
        cls.follower_client.force_login(cls.follower)
        cls.author = User.objects.create_user(username='author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
        )

    def setUp(self):
        self.follow = Follow.objects.get_or_create(
            user=self.follower,
            author=self.author
        )

    def test_user_can_unfollow(self):
        count_before_unfollow = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author.username}))
        count_after_unfollow = Follow.objects.count()
        self.assertNotEqual(count_before_unfollow, count_after_unfollow)
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower,
                author=self.author
            ).exists()
        )

    def test_user_can_follow(self):
        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author.username}))
        count_before_follow = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username}))
        count_after_follow = Follow.objects.count()
        self.assertNotEqual(count_before_follow, count_after_follow)
        self.assertTrue(
            Follow.objects.filter(
                user=self.follower,
                author=self.author
            ).exists()
        )

    def test_follow_index_context(self):
        response = self.follower_client.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author.username
        self.assertEqual = (post_author_0, 'author')
        post_text_0 = first_object.text
        self.assertEqual = (post_text_0, 'Тестовый текст')

    def test_follow_index_context_wo_author(self):
        Follow.objects.filter(
            user=self.follower.is_authenticated, author=self.author,
        ).delete()
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual = (len(response.context['page_obj']), 0)


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.commentator = User.objects.create_user(username='commentator')
        cls.commentator_client = Client()
        cls.commentator_client.force_login(cls.commentator)
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.author
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.commentator,
            text='Тестовый текст комментария'
        )

    def test_comment(self):
        self.assertTrue(
            Comment.objects.filter(
                post=self.post,
                author=self.commentator,
                text='Тестовый текст комментария'
            ).exists
        )
        response = Comment.objects.filter(
            post=self.post,
            author=self.commentator,
            text='Тестовый текст комментария'
        ).count()
        self.assertEqual(response, 1)

    def test_comment_context(self):
        response = self.commentator_client.get(
            reverse('posts:post_detail', args=[self.post.id]))
        comments = response.context['comments'][0]
        expected_fields = {
            comments.author.username: 'commentator',
            comments.post.id: self.post.id,
            comments.text: 'Тестовый текст комментария'
        }
        for fields, values in expected_fields.items():
            with self.subTest(expected_fields=expected_fields):
                self.assertEqual(fields, values)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.author_client = Client()
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
        )

    def test_caching(self):
        cache.clear()
        response = self.author_client.get(reverse('posts:index'))
        posts_count = Post.objects.count()
        self.post.delete
        self.assertEqual(len(response.context['page_obj']), posts_count)
        cache.clear()
        posts_count = Post.objects.count()
        self.assertEqual(len(response.context['page_obj']), posts_count)
