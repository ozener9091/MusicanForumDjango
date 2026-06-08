from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context, Template
from django.test import TestCase
from django.urls import reverse

from .forms import CommentForm, DiscussionModelForm, DiscussionSimpleForm, UploadFileForm
from .models import Comment, Discussion, DiscussionPassport, DiscussionReaction, ReactionValue, Tag


class DiscussionModelTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="OwnerPass123!",
            first_name="Иван",
            last_name="Петров",
        )
        self.discussion = Discussion.objects.create(
            title="Тестовая тема",
            author="Иван Петров",
            created_by=self.owner,
            category=Discussion.Category.GUITAR,
            status=Discussion.Status.PUBLISHED,
            content="Содержимое тестовой темы",
        )

    def test_discussion_creates_passport_automatically(self):
        self.assertTrue(DiscussionPassport.objects.filter(discussion=self.discussion).exists())

    def test_display_author_uses_related_user(self):
        self.assertEqual(self.discussion.display_author, "Иван Петров")

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
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="OwnerPass123!",
            first_name="Иван",
            last_name="Петров",
        )
        self.other = user_model.objects.create_user(
            username="other",
            email="other@example.com",
            password="OtherPass123!",
            first_name="Анна",
            last_name="Соколова",
        )
        self.tag = Tag.objects.create(name="Практика тест")
        self.discussion = Discussion.objects.create(
            title="Гитарная практика",
            author="Иван Петров",
            created_by=self.owner,
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
            created_by=self.other,
            text="Попробуй медленные упражнения под метроном.",
        )
        self.other_discussion = Discussion.objects.create(
            title="Черновик по вокалу",
            author="Анна Соколова",
            created_by=self.other,
            category=Discussion.Category.VOCALS,
            status=Discussion.Status.DRAFT,
            content="Черновой текст",
        )

    def test_index_contains_tags_comment_and_reaction_counts(self):
        response = self.client.get(reverse("musicforum:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "#Практика тест")
        self.assertContains(response, "Комментарии: 1")
        self.assertContains(response, "Лайки: 0")

    def test_discussion_page_contains_comments_and_comment_form(self):
        response = self.client.get(reverse("musicforum:discussion", kwargs={"slug": self.discussion.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["discussion"].passport.views_count, 40)
        self.assertContains(response, "Просмотры:")
        self.assertContains(response, "Попробуй медленные упражнения под метроном.")
        self.assertContains(response, "Чтобы оставить комментарий, войдите в аккаунт.")

    def test_about_page_contains_grouped_orm_statistics(self):
        self.client.force_login(self.other)

        response = self.client.get(reverse("musicforum:about"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("orm_status_counts", response.context)
        self.assertIn("orm_tag_counts", response.context)
        self.assertIn("orm_reaction_counts", response.context)
        self.assertContains(response, "Практика тест")

    def test_search_with_q_finds_discussion_by_tag_and_comment(self):
        by_tag = self.client.get(reverse("musicforum:index"), {"q": "Практика тест"})
        by_comment = self.client.get(reverse("musicforum:index"), {"q": "метроном"})

        self.assertContains(by_tag, self.discussion.title)
        self.assertNotContains(by_tag, self.other_discussion.title)
        self.assertContains(by_comment, self.discussion.title)

    def test_authenticated_user_can_create_comment(self):
        self.client.force_login(self.other)

        response = self.client.post(
            reverse("musicforum:discussion_comment", kwargs={"slug": self.discussion.slug}),
            {"text": "Отличный совет, спасибо!"},
        )

        self.assertRedirects(response, f"{self.discussion.get_absolute_url()}#comments")
        self.assertTrue(Comment.objects.filter(discussion=self.discussion, created_by=self.other).exists())

    def test_reaction_toggle_create_update_and_delete(self):
        self.client.force_login(self.other)
        reaction_url = reverse(
            "musicforum:discussion_reaction",
            kwargs={"slug": self.discussion.slug, "value": ReactionValue.LIKE},
        )

        response = self.client.post(reaction_url)
        self.assertRedirects(response, self.discussion.get_absolute_url())
        self.assertTrue(
            DiscussionReaction.objects.filter(
                discussion=self.discussion,
                user=self.other,
                value=ReactionValue.LIKE,
            ).exists()
        )

        response = self.client.post(
            reverse(
                "musicforum:discussion_reaction",
                kwargs={"slug": self.discussion.slug, "value": ReactionValue.DISLIKE},
            )
        )
        self.assertRedirects(response, self.discussion.get_absolute_url())
        self.assertTrue(
            DiscussionReaction.objects.filter(
                discussion=self.discussion,
                user=self.other,
                value=ReactionValue.DISLIKE,
            ).exists()
        )

        response = self.client.post(
            reverse(
                "musicforum:discussion_reaction",
                kwargs={"slug": self.discussion.slug, "value": ReactionValue.DISLIKE},
            )
        )
        self.assertRedirects(response, self.discussion.get_absolute_url())
        self.assertFalse(
            DiscussionReaction.objects.filter(
                discussion=self.discussion,
                user=self.other,
            ).exists()
        )

    def test_only_creator_can_edit_discussion(self):
        self.client.force_login(self.other)

        response = self.client.post(
            reverse("musicforum:discussion_update", kwargs={"slug": self.discussion.slug}),
            {
                "title": "Изменённая тема",
                "slug": self.discussion.slug,
                "category": self.discussion.category,
                "status": self.discussion.status,
                "content": self.discussion.content,
                "photo": "",
                "tags": [],
            },
        )

        self.assertEqual(response.status_code, 403)
        self.discussion.refresh_from_db()
        self.assertEqual(self.discussion.title, "Гитарная практика")

    def test_creator_can_edit_discussion(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("musicforum:discussion_update", kwargs={"slug": self.discussion.slug}),
            {
                "title": "Изменённая тема",
                "slug": self.discussion.slug,
                "category": self.discussion.category,
                "status": self.discussion.status,
                "content": "Обновлённое содержание",
                "tags": [self.tag.pk],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.discussion.refresh_from_db()
        self.assertEqual(self.discussion.title, "Изменённая тема")
        self.assertEqual(self.discussion.created_by, self.owner)


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

    def test_comment_form_requires_min_length(self):
        form = CommentForm(data={"text": "1234"})
        self.assertFalse(form.is_valid())
        self.assertIn("text", form.errors)


class UploadFileFormTests(TestCase):
    def test_upload_form_requires_file(self):
        form = UploadFileForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_upload_form_accepts_file(self):
        upload = SimpleUploadedFile("track.txt", b"demo")
        form = UploadFileForm(data={}, files={"file": upload})
        self.assertTrue(form.is_valid())
