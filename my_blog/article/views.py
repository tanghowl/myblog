from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpResponse
from .models import ArticlePost, ArticleColumn
from .forms import ArticlePostForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from comment.models import Comment
import markdown


def article_list(request):
    search = request.GET.get('search')
    order = request.GET.get('order')
    if search:
        if order == 'total_views':
            article_lst = ArticlePost.objects.filter(
                Q(title__icontains=search) |
                Q(body__icontains=search)
            ).order_by('-total_views')
        else:
            article_lst = ArticlePost.objects.filter(
                Q(title__icontains=search) |
                Q(body__icontains=search)
            )
    else:
        search = ''
        if order == 'total_views':
            article_lst = ArticlePost.objects.all().order_by('-total_views')
        else:
            article_lst = ArticlePost.objects.all()

    paginator = Paginator(article_lst, 3)
    page = request.GET.get('page')
    articles = paginator.get_page(page)

    context = {'articles': articles, 'order': order}

    return render(request, 'article/list.html', context)


def article_detail(request, id):
    article = ArticlePost.objects.get(id=id)
    article.total_views += 1
    article.save(update_fields=['total_views'])
    md = markdown.Markdown(extensions=[
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
    ])
    pre_article = ArticlePost.objects.filter(id__lt=article.id).order_by('-id')
    next_article = ArticlePost.objects.filter(id__gt=article.id).order_by('id')

    if pre_article.count() > 0:
        pre_article = pre_article[0]
    else:
        pre_article = None

    if next_article.count() > 0:
        next_article = next_article[0]
    else:
        next_article = None

    article.body = md.convert(article.body)
    comments = Comment.objects.filter(article=id)
    context = {'article': article,
               'toc': md.toc,
               'comments': comments,
               'pre_article': pre_article,
               'next_article': next_article}
    return render(request, 'article/detail.html', context)


@login_required(login_url='/userprofile/login/')
def article_create(request):
    if request.method == 'POST':
        article_post_form = ArticlePostForm(data=request.POST)
        if article_post_form.is_valid():
            new_article = article_post_form.save(commit=False)
            new_article.author = User.objects.get(id=request.user.id)
            if request.POST['column'] != 'none':
                new_article.column = ArticleColumn.objects.get(id=request.POST['column'])
            new_article.save()
            return redirect('article:article_list')
        else:
            return HttpResponse('There is something wrong with the form. Please fill it again')
    else:
        article_post_form = ArticlePostForm()
        columns = ArticleColumn.objects.all()
        context = {'article_post_form': article_post_form, 'columns': columns}
        return render(request, 'article/create.html', context)


def article_delete(request, id):
    article = ArticlePost.objects.get(id=id)
    article.delete()
    return redirect("article:article_list")


@login_required(login_url='/userprofile/login/')
def article_update(request, id):
    article = ArticlePost.objects.get(id=id)
    if request.user != article.author:
        return HttpResponse('sorry, you have no right to modify the article')

    if request.method == 'POST':
        article_post_form = ArticlePostForm(data=request.POST)
        if article_post_form.is_valid():
            article.title = request.POST['title']
            article.body = request.POST['body']
            if request.POST['column'] != 'none':
                article.column = ArticleColumn.objects.get(id=request.POST['column'])
            else:
                article.column = None
            article.save()
            return redirect('article:article_detail', id=id)
        else:
            return HttpResponse('the form context is error, please fill again')
    else:
        article_post_form = ArticlePostForm()
        columns = ArticleColumn.objects.all()
        context = {'article': article, 'article_post_form': article_post_form, 'columns': columns}
        return render(request, 'article/update.html', context)
