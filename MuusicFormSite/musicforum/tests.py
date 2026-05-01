from django.template import Context, Template
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .forms import DiscussionModelForm, DiscussionSimpleForm, UploadFileForm
from .models import Comment, Discussion, DiscussionPassport, Tag


class DiscussionModelTests(TestCase):
    def setUp(self):
        self.discussion = Discussion.objects.create(
            title="Тестовая тема",
            author="Иван",
            category=Discussion.Category.GUITAR,
            status=Discussion.Status.PUBLISHED,
            content="Содержимое тестовой темы",
        )

    def test_discussion_creates_passport_automatically(self):
        self.assertTrue(
            DiscussionPassport.objects.filter(discussion=self.discussion).exists()
        )

    def test_comment_is_deleted_with_discussion(self):
        comment = Comment.objects.create(
            discussion=self.discussion,
            author="Петр",
            text="Комментарий для удаления",
        )

        self.discussion.delete()

        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_tag_many_to_many_relationship(self):
        first_tag = Tag.objects.create(name="Тег 1")
        second_tag = Tag.objects.create(name="Тег 2")
        second_discussion = Discussion.objects.create(
            title="Вторая тема",
            author="Мария",
            category=Discussion.Category.VOCALS,
            status=Discussion.Status.PUBLISHED,
            content="Еще одна тема",
        )

        self.discussion.tags.add(first_tag, second_tag)
        second_discussion.tags.add(first_tag)

        self.assertEqual(self.discussion.tags.count(), 2)
        self.assertEqual(first_tag.discussions.count(), 2)


class DiscussionViewTests(TestCase):
    def setUp(self):
        self.tag = Tag.objects.create(name="Практика тест")
        self.discussion = Discussion.objects.create(
            title="Гитарная практика",
            author="Олег",
            category=Discussion.Category.GUITAR,
            status=Discussion.Status.PUBLISHED,
            content="Ищу упражнения для ежедневной практики",
        )
        self.discussion.tags.add(self.tag)
        DiscussionPassport.objects.filter(discussion=self.discussion).update(
            views_count=40,
            bookmarks_count=5,
        )
        Comment.objects.create(
            discussion=self.discussion,
            author="Сергей",
            text="Попробуй медленные упражнения под метроном.",
        )
        self.other_discussion = Discussion.objects.create(
            title="Черновик по вокалу",
            author="Анна",
            category=Discussion.Category.VOCALS,
            status=Discussion.Status.DRAFT,
            content="Черновой текст",
        )

    def test_index_contains_tags_and_comment_counts(self):
        response = self.client.get(reverse("musicforum:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "#Практика тест")
        self.assertContains(response, "Комментарии: 1")

    def test_discussion_page_contains_comments_and_passport_data(self):
        response = self.client.get(
            reverse("musicforum:discussion", kwargs={"slug": self.discussion.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["discussion"].passport.views_count, 40)
        self.assertContains(response, "Просмотры:")
        self.assertContains(response, "Попробуй медленные упражнения под метроном.")

    def test_about_page_contains_grouped_orm_statistics(self):
        response = self.client.get(reverse("musicforum:about"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("orm_status_counts", response.context)
        self.assertIn("orm_tag_counts", response.context)
        self.assertContains(response, "Практика тест")

    def test_search_with_q_finds_discussion_by_tag_and_comment(self):
        by_tag = self.client.get(reverse("musicforum:index"), {"q": "Практика тест"})
        by_comment = self.client.get(reverse("musicforum:index"), {"q": "метроном"})

        self.assertContains(by_tag, self.discussion.title)
        self.assertNotContains(by_tag, self.other_discussion.title)
        self.assertContains(by_comment, self.discussion.title)


class TemplateTagTests(TestCase):
    def test_show_popular_tags_returns_tags_with_discussion_counts(self):
        discussion = Discussion.objects.create(
            title="Студийная запись",
            author="Максим",
            category=Discussion.Category.PRODUCTION,
            status=Discussion.Status.PUBLISHED,
            content="Нужно обсудить запись дома",
        )
        tag = Tag.objects.create(name="Запись тест")
        discussion.tags.add(tag)

        rendered = Template(
            "{% load musicforum_tags %}{% show_popular_tags 5 %}"
        ).render(Context())

        self.assertIn("#Запись тест", rendered)
        self.assertIn("1", rendered)


class DiscussionFormTests(TestCase):
    def setUp(self):
        self.tag = Tag.objects.create(name="Тест формы")
        self.valid_data = {
            "title": "Корректный заголовок",
            "slug": "korrektnyj-zagolovok",
            "author": "Тестер",
            "category": Discussion.Category.GUITAR,
            "status": Discussion.Status.PUBLISHED,
            "content": "Текст тестовой темы",
            "tags": [self.tag.pk],
        }

    def test_simple_form_valid_data(self):
        form = DiscussionSimpleForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_simple_form_standard_validator_rejects_short_slug(self):
        form = DiscussionSimpleForm(data={**self.valid_data, "slug": "abc"})
        self.assertFalse(form.is_valid())
        self.assertIn("slug", form.errors)

    def test_simple_form_custom_validator_rejects_forbidden_word(self):
        form = DiscussionSimpleForm(data={**self.valid_data, "title": "Спам тема"})
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_model_form_valid_data(self):
        form = DiscussionModelForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_model_form_standard_validator_rejects_short_slug(self):
        form = DiscussionModelForm(data={**self.valid_data, "slug": "abc"})
        self.assertFalse(form.is_valid())
        self.assertIn("slug", form.errors)

    def test_model_form_custom_validator_rejects_long_title(self):
        too_long_title = "Очень длинный заголовок для проверки пользовательского валидатора"
        form = DiscussionModelForm(data={**self.valid_data, "title": too_long_title})
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)


class UploadFileFormTests(TestCase):
    def test_upload_form_requires_file(self):
        form = UploadFileForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_upload_form_accepts_file(self):
        upload = SimpleUploadedFile("track.txt", b"demo")
        form = UploadFileForm(data={}, files={"file": upload})
        self.assertTrue(form.is_valid())
