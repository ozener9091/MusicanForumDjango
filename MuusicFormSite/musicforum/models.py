from django.db import models
from django.db.models import Count, Q
from django.utils.text import slugify


class DiscussionStatus(models.TextChoices):
    DRAFT = "draft", "Черновик"
    PUBLISHED = "published", "Опубликовано"
    ARCHIVED = "archived", "В архиве"


class MusicCategory(models.TextChoices):
    GUITAR = "guitar", "Гитара"
    VOCALS = "vocals", "Вокал"
    PRODUCTION = "production", "Продакшн"
    DRUMS = "drums", "Ударные"


class DiscussionQuerySet(models.QuerySet):
    ORDERING_MAP = {
        "-created_at": ("-created_at", "-id"),
        "created_at": ("created_at", "id"),
        "title": ("title", "id"),
        "-title": ("-title", "-id"),
        "author": ("author", "title"),
    }

    def search(self, query):
        if not query:
            return self
        return self.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(author__icontains=query)
            | Q(tags__name__icontains=query)
            | Q(comments__text__icontains=query)
        ).distinct()

    def for_category(self, category_slug):
        if not category_slug:
            return self
        return self.filter(category=category_slug)

    def with_status(self, status):
        if not status:
            return self
        return self.filter(status=status)

    def published(self):
        return self.with_status(DiscussionStatus.PUBLISHED)

    def ordered(self, ordering):
        return self.order_by(*self.ORDERING_MAP.get(ordering, self.ORDERING_MAP["-created_at"]))


class DiscussionManager(models.Manager.from_queryset(DiscussionQuerySet)):
    def category_totals(self):
        return dict(
            self.get_queryset()
            .values("category")
            .annotate(total=Count("id"))
            .values_list("category", "total")
        )


class Tag(models.Model):
    name = models.CharField("Название тега", max_length=100, unique=True)
    slug = models.SlugField("Слаг", max_length=100, unique=True, allow_unicode=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "тег"
        verbose_name_plural = "теги"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = self._build_unique_slug()
        super().save(*args, **kwargs)

    def _build_unique_slug(self):
        base_slug = slugify(self.slug or self.name, allow_unicode=True) or "tag"
        slug = base_slug
        counter = 2

        while self.__class__.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug


class Discussion(models.Model):
    Category = MusicCategory
    Status = DiscussionStatus

    CATEGORY_DESCRIPTIONS = {
        MusicCategory.GUITAR: "Выбор инструментов, усилителей, педалей и техники игры.",
        MusicCategory.VOCALS: "Постановка голоса, дыхание и сценическая подача.",
        MusicCategory.PRODUCTION: "Запись, сведение, плагины и домашние студии.",
        MusicCategory.DRUMS: "Установки, пэды, ритм и упражнения для барабанщиков.",
    }
    ORDERING_OPTIONS = [
        ("-created_at", "Сначала новые"),
        ("created_at", "Сначала старые"),
        ("title", "Название: А-Я"),
        ("-title", "Название: Я-А"),
        ("author", "Автор: А-Я"),
    ]

    title = models.CharField("Название темы", max_length=255)
    slug = models.SlugField("Слаг", max_length=255, unique=True, blank=True, allow_unicode=True)
    author = models.CharField("Автор", max_length=100)
    category = models.CharField(
        "Категория",
        max_length=20,
        choices=MusicCategory.choices,
        default=MusicCategory.GUITAR,
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=DiscussionStatus.choices,
        default=DiscussionStatus.PUBLISHED,
    )
    content = models.TextField("Содержание")
    photo = models.ImageField(
        "Фото",
        upload_to="photos/%Y/%m/%d/",
        default=None,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now=True)
    tags = models.ManyToManyField(Tag, verbose_name="Теги", related_name="discussions", blank=True)

    objects = DiscussionManager()

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "обсуждение"
        verbose_name_plural = "обсуждения"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("musicforum:discussion", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        self.slug = self._build_unique_slug()
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating:
            DiscussionPassport.objects.get_or_create(discussion=self)

    def _build_unique_slug(self):
        base_slug = slugify(self.slug or self.title, allow_unicode=True) or "discussion"
        slug = base_slug
        counter = 2

        while self.__class__.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    @classmethod
    def get_category_catalog(cls):
        totals = cls.objects.category_totals()
        return [
            {
                "slug": value,
                "title": label,
                "description": cls.CATEGORY_DESCRIPTIONS.get(value, ""),
                "count": totals.get(value, 0),
            }
            for value, label in cls.Category.choices
        ]

    @classmethod
    def get_category_data(cls, slug):
        for item in cls.get_category_catalog():
            if item["slug"] == slug:
                return item
        return None

    @classmethod
    def get_status_options(cls):
        return list(cls.Status.choices)

    @classmethod
    def get_ordering_options(cls):
        return cls.ORDERING_OPTIONS


class DiscussionPassport(models.Model):
    discussion = models.OneToOneField(
        Discussion,
        verbose_name="Обсуждение",
        related_name="passport",
        on_delete=models.CASCADE,
    )
    views_count = models.PositiveIntegerField("Количество просмотров", default=0)
    bookmarks_count = models.PositiveIntegerField("Количество закладок", default=0)

    class Meta:
        verbose_name = "паспорт обсуждения"
        verbose_name_plural = "паспорта обсуждений"

    def __str__(self):
        return f"Паспорт: {self.discussion}"


class Comment(models.Model):
    discussion = models.ForeignKey(
        Discussion,
        verbose_name="Обсуждение",
        related_name="comments",
        on_delete=models.CASCADE,
    )
    author = models.CharField("Автор комментария", max_length=100)
    text = models.TextField("Текст комментария")
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
        verbose_name = "комментарий"
        verbose_name_plural = "комментарии"

    def __str__(self):
        return f"{self.author}: {self.text[:40]}"
