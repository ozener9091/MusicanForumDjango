from django.db import migrations


def seed_discussions(apps, schema_editor):
    Discussion = apps.get_model("musicforum", "Discussion")
    Discussion.objects.create(
        title="Выбор первой электрогитары",
        slug="vybor-pervoj-elektrogitary",
        author="Илья",
        category="guitar",
        status="published",
        content="Хочу подобрать универсальную гитару для рока и блюза. Какие модели посмотреть в первую очередь?",
    )
    Discussion.objects.create(
        title="Разминка перед репетицией",
        slug="razminka-pered-repeticiej",
        author="Марина",
        category="vocals",
        status="draft",
        content="Какие упражнения лучше делать за 10-15 минут до репетиции, чтобы голос не уставал?",
    )
    Discussion.objects.create(
        title="Бюджетный аудиоинтерфейс",
        slug="byudzhetnyj-audiointerfejs",
        author="Артем",
        category="production",
        status="published",
        content="Нужен интерфейс до 20 тысяч рублей для записи вокала и гитары. Какие варианты сейчас самые надежные?",
    )
    Discussion.objects.create(
        title="Домашняя практика на электронных барабанах",
        slug="domashnyaya-praktika-na-elektronnyh-barabanah",
        author="Олег",
        category="drums",
        status="archived",
        content="Какие настройки модуля и какие пэды удобнее всего для тихих вечерних занятий?",
    )


def remove_discussions(apps, schema_editor):
    Discussion = apps.get_model("musicforum", "Discussion")
    Discussion.objects.filter(
        slug__in=[
            "vybor-pervoj-elektrogitary",
            "razminka-pered-repeticiej",
            "byudzhetnyj-audiointerfejs",
            "domashnyaya-praktika-na-elektronnyh-barabanah",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('musicforum', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_discussions, remove_discussions),
    ]
