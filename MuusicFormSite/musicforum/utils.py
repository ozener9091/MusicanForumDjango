from .data import get_menu
from .models import Discussion, Tag


class DataMixin:
    title_page = None
    extra_context = {}
    paginate_by = 2

    def __init__(self):
        self.extra_context = self.extra_context.copy()

        if self.title_page:
            self.extra_context["title"] = self.title_page

        if "menu" not in self.extra_context:
            self.extra_context["menu"] = get_menu()

    def get_mixin_context(self, context, **kwargs):
        if self.title_page:
            context["title"] = self.title_page

        context["menu"] = get_menu()
        context["current_category"] = ""
        context["category_options"] = Discussion.Category.choices
        context["status_options"] = Discussion.get_status_options()
        context["ordering_options"] = Discussion.get_ordering_options()
        context["all_tags"] = Tag.objects.order_by("name")
        context.update(kwargs)
        return context
