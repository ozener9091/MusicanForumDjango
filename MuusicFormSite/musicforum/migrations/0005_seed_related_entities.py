from django.db import migrations


def seed_related_entities(apps, schema_editor):
    Discussion = apps.get_model("musicforum", "Discussion")
    DiscussionPassport = apps.get_model("musicforum", "DiscussionPassport")
    Comment = apps.get_model("musicforum", "Comment")
    Tag = apps.get_model("musicforum", "Tag")

    tags_data = [
        ("Советы", "sovety"),
        ("Оборудование", "oborudovanie"),
        ("Практика", "praktika"),
        ("Запись", "zapis"),
    ]
    created_tags = {}
    for name, slug in tags_data:
        tag, _ = Tag.objects.get_or_create(name=name, defaults={"slug": slug})
        created_tags[name] = tag

    tag_map = {
        "vybor-pervoj-elektrogitary": ["Советы", "Оборудование"],
        "razminka-pered-repeticiej": ["Практика"],
        "byudzhetnyj-audiointerfejs": ["Оборудование", "Запись"],
        "domashnyaya-praktika-na-elektronnyh-barabanah": ["Практика", "Советы"],
    }
    passport_map = {
        "vybor-pervoj-elektrogitary": (125, 18),
        "razminka-pered-repeticiej": (84, 9),
        "byudzhetnyj-audiointerfejs": (173, 27),
        "domashnyaya-praktika-na-elektronnyh-barabanah": (61, 7),
    }
    comments_map = {
        "vybor-pervoj-elektrogitary": [
            ("Сергей", "Для первого инструмента лучше смотреть на удобство грифа и стабильность строя."),
            ("Анна", "Еще полезно сразу проверить, насколько удобно менять звукосниматели и струны."),
        ],
        "razminka-pered-repeticiej": [
            ("Елена", "Мне помогают короткие дыхательные упражнения и спокойное легато перед репетицией."),
        ],
        "byudzhetnyj-audiointerfejs": [
            ("Дмитрий", "Смотри на стабильные драйверы и наличие прямого мониторинга."),
            ("Никита", "Если планируешь писать вокал, не экономь на предусилителях."),
        ],
    }

    for discussion in Discussion.objects.all():
        views_count, bookmarks_count = passport_map.get(discussion.slug, (0, 0))
        DiscussionPassport.objects.get_or_create(
            discussion=discussion,
            defaults={
                "views_count": views_count,
                "bookmarks_count": bookmarks_count,
            },
        )

        if discussion.slug in tag_map:
            discussion.tags.set(created_tags[name] for name in tag_map[discussion.slug])

        if discussion.slug in comments_map:
            for author, text in comments_map[discussion.slug]:
                Comment.objects.get_or_create(
                    discussion=discussion,
                    author=author,
                    text=text,
                )


def remove_related_entities(apps, schema_editor):
    Discussion = apps.get_model("musicforum", "Discussion")
    DiscussionPassport = apps.get_model("musicforum", "DiscussionPassport")
    Comment = apps.get_model("musicforum", "Comment")
    Tag = apps.get_model("musicforum", "Tag")

    slugs = [
        "vybor-pervoj-elektrogitary",
        "razminka-pered-repeticiej",
        "byudzhetnyj-audiointerfejs",
        "domashnyaya-praktika-na-elektronnyh-barabanah",
    ]
    tag_names = ["Советы", "Оборудование", "Практика", "Запись"]

    Comment.objects.filter(discussion__slug__in=slugs).delete()
    DiscussionPassport.objects.filter(discussion__slug__in=slugs).delete()
    discussions = Discussion.objects.filter(slug__in=slugs)
    for discussion in discussions:
        discussion.tags.clear()
    Tag.objects.filter(name__in=tag_names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("musicforum", "0004_tag_comment_discussionpassport_discussion_tags"),
    ]

    operations = [
        migrations.RunPython(seed_related_entities, remove_related_entities),
    ]
