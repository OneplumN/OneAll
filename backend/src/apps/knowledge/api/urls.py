from django.urls import path

from .knowledge_views import (
    KnowledgeArticleDetailView,
    KnowledgeArticleListCreateView,
    KnowledgeArticleVersionListView,
    KnowledgeCategoryDetailView,
    KnowledgeCategoryListCreateView,
    KnowledgeCategoryOrderView,
)

urlpatterns = [
    path('knowledge/articles', KnowledgeArticleListCreateView.as_view(), name='knowledge-articles'),
    path('knowledge/articles/<slug:slug>', KnowledgeArticleDetailView.as_view(), name='knowledge-article-detail'),
    path('knowledge/articles/<slug:slug>/versions', KnowledgeArticleVersionListView.as_view(), name='knowledge-article-versions'),
    path('knowledge/categories', KnowledgeCategoryListCreateView.as_view(), name='knowledge-categories'),
    path('knowledge/categories/<slug:key>', KnowledgeCategoryDetailView.as_view(), name='knowledge-category-detail'),
    path('knowledge/categories/order', KnowledgeCategoryOrderView.as_view(), name='knowledge-category-order'),
]
