from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.utils.text import slugify

from .models import Discussion, Tag


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


class DiscussionSimpleForm(forms.Form):
    title = forms.CharField(
        label="Название темы",
        min_length=5,
        max_length=255,
        validators=[ForbiddenWordsValidator()],
    )
    slug = forms.SlugField(
        label="Слаг",
        required=False,
        validators=[MinLengthValidator(5), MaxLengthValidator(100)],
        help_text="Если оставить поле пустым, слаг создастся автоматически.",
    )
    author = forms.CharField(label="Автор", max_length=100)
    category = forms.ChoiceField(label="Категория", choices=Discussion.Category.choices)
    status = forms.ChoiceField(label="Статус", choices=Discussion.get_status_options())
    content = forms.CharField(label="Текст сообщения", widget=forms.Textarea(attrs={"rows": 8}))
    tags = forms.ModelMultipleChoiceField(
        label="Теги",
        queryset=Tag.objects.order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) > 50:
            raise ValidationError("Длина заголовка превышает 50 символов.")
        return title

    def clean_slug(self):
        slug = slugify(self.cleaned_data.get("slug", ""), allow_unicode=True)
        return slug


class DiscussionModelForm(forms.ModelForm):
    title = forms.CharField(
        label="Название темы",
        min_length=5,
        max_length=255,
        validators=[ForbiddenWordsValidator()],
    )
    slug = forms.SlugField(
        label="Слаг",
        required=False,
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
        fields = ["title", "slug", "author", "category", "status", "content", "photo", "tags"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 8}),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) > 50:
            raise ValidationError("Длина заголовка превышает 50 символов.")
        return title

    def clean_slug(self):
        slug = slugify(self.cleaned_data.get("slug", ""), allow_unicode=True)
        return slug


class UploadFileForm(forms.Form):
    file = forms.FileField(label="Файл")
