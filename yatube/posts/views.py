from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.POST_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    page_number = request.GET.get('page')
    post_list = Post.objects.filter(group=group)
    paginator = Paginator(post_list, settings.POST_COUNT)
    page_obj = paginator.get_page(page_number)
    context = {
        'title': f'Записи сообщества {slug}',
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    user_posts = Post.objects.filter(author=user_profile)
    posts_count = user_posts.count()
    paginator = Paginator(user_posts, settings.POST_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'author': user_profile,
        'page_obj': page_obj,
        'count': posts_count,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    user_post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = user_post.comments.all()
    posts = Post.objects.filter(author_id=user_post.author_id)
    posts_count = posts.count()
    context = {
        'post': user_post,
        'posts_count': posts_count,
        'form': form,   
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.pk)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }

    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post.pk)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, settings.POST_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    unfollowing = get_object_or_404(Follow, user=request.user, author=author)
    if request.method != 'POST':
        unfollowing.delete()
    return redirect('posts:profile', author)
