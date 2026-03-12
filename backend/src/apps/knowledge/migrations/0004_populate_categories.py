from django.db import migrations
from django.utils.text import slugify


def create_categories(apps, schema_editor):
    Category = apps.get_model("knowledge", "KnowledgeCategory")
    Article = apps.get_model("knowledge", "KnowledgeArticle")

    order = Category.objects.count()
    seen_titles = {}

    for article in Article.objects.all():
        raw_title = (article.category or "").strip() or "未分类"
        base_slug = slugify(raw_title) or "category"
        slug = base_slug
        suffix = 2
        while True:
            existing = Category.objects.filter(key=slug).first()
            if not existing:
                break
            if existing.title == raw_title:
                break
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        category, created = Category.objects.get_or_create(
            key=slug,
            defaults={
                "title": raw_title,
                "description": "",
                "display_order": order,
            },
        )
        if created:
            order += 1
        else:
            # ensure title sync if previously placeholder
            if not category.title:
                category.title = raw_title
                category.save(update_fields=["title"])

        if article.category != category.key:
            article.category = category.key
            article.save(update_fields=["category"])


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge", "0003_knowledgecategory"),
    ]

    operations = [
        migrations.RunPython(create_categories, migrations.RunPython.noop),
    ]
