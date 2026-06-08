from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.utils.text import slugify

from .models import Comment, Discussion, Tag


class ForbiddenWordsValidator:
    forbidden_words = ("spam", "спам", "реклама")
    code = "forbidden_words"

    def __call__(self, value):
        title = value.lower()
        for word in self.forbidden_words:
            if word in title:
                raise ValidationError(
                    "Заголовок содержит запрещенные слова.",
                    code=self.code,
                )


class DiscussionValidationMixin:
    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) > 50:
            raise ValidationError("Длина заголовка превышает 50 символов.")
        return title

    def clean_slug(self):
        slug = slugify(self.cleaned_data.get("slug", ""), allow_unicode=True)
        if slug:
            slug_qs = Discussion.objects.filter(slug=slug)
            instance = getattr(self, "instance", None)
            if instance is not None and getattr(instance, "pk", None):
                slug_qs = slug_qs.exclude(pk=instance.pk)

            if slug_qs.exists():
                raise ValidationError("Тема с таким слагом уже существует.")
        return slug


class DiscussionSimpleForm(DiscussionValidationMixin, forms.Form):
    title = forms.CharField(
        label="Название темы",
        min_length=5,
        max_length=255,
        validators=[ForbiddenWordsValidator()],
    )
    slug = forms.SlugField(
        label="Слаг",
        required=False,
        allow_unicode=True,
        validators=[MinLengthValidator(5), MaxLengthValidator(100)],
        help_text="Если оставить поле пустым, слаг создастся автоматически.",
    )
    category = forms.ChoiceField(label="Категория", choices=Discussion.Category.choices)
    status = forms.ChoiceField(label="Статус", choices=Discussion.get_status_options())
    content = forms.CharField(label="Текст сообщения", widget=forms.Textarea(attrs={"rows": 8}))
    photo = forms.ImageField(label="Фото", required=False)
    tags = forms.ModelMultipleChoiceField(
        label="Теги",
        queryset=Tag.objects.order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )


class DiscussionModelForm(DiscussionValidationMixin, forms.ModelForm):
    title = forms.CharField(
        label="Название темы",
        min_length=5,
        max_length=255,
        validators=[ForbiddenWordsValidator()],
    )
    slug = forms.SlugField(
        label="Слаг",
        required=False,
        allow_unicode=True,
        validators=[MinLengthValidator(5), MaxLengthValidator(100)],
        help_text="Если оставить поле пустым, слаг создастся автоматически.",
    )
    tags = forms.ModelMultipleChoiceField(
        label="Теги",
        queryset=Tag.objects.order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Discussion
        fields = ["title", "slug", "category", "status", "content", "photo", "tags"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 8}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 4, "placeholder": "Напишите комментарий..."}),
        }
        labels = {
            "text": "Комментарий",
        }

    def clean_text(self):
        text = self.cleaned_data["text"].strip()
        if len(text) < 5:
            raise ValidationError("Комментарий должен быть не короче 5 символов.")
        return text


class UploadFileForm(forms.Form):
    file = forms.FileField(label="Файл")
