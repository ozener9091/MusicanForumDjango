from datetime import date

MENU = [
    {"title": "Главная", "url_name": "musicforum:index"},
    {"title": "О форуме", "url_name": "musicforum:about"},
    {"title": "Категории", "url_name": "musicforum:categories"},
]

CATEGORIES = [
    {"slug": "guitar", "title": "Гитара", "description": "Обсуждения гитар, усилителей и педалей."},
    {"slug": "vocals", "title": "Вокал", "description": "Техника пения, дыхание и сценическая подача."},
    {"slug": "production", "title": "Продакшн", "description": "Запись, сведение и домашние студии."},
]

DISCUSSIONS = [
    {
        "id": 1,
        "category": "guitar",
        "title": "Выбор первой электрогитары",
        "author": "Илья",
        "content": "Хочу подобрать универсальную гитару для рока и блюза. Какие модели посмотреть в первую очередь?",
        "created_at": date(2026, 2, 18),
    },
    {
        "id": 2,
        "category": "vocals",
        "title": "Разминка перед репетицией",
        "author": "Марина",
        "content": "Какие упражнения лучше делать за 10-15 минут до репетиции, чтобы голос не уставал?",
        "created_at": date(2026, 2, 22),
    },
    {
        "id": 3,
        "category": "production",
        "title": "Бюджетный аудиоинтерфейс",
        "author": "Артем",
        "content": "Нужен интерфейс до 20 тысяч рублей для записи вокала и гитары. Какие варианты сейчас самые надежные?",
        "created_at": date(2026, 2, 27),
    },
]


def get_menu():
    return MENU


def get_categories():
    return CATEGORIES


def get_category(slug):
    for category in CATEGORIES:
        if category["slug"] == slug:
            return category
    return None


def get_discussions(category_slug=None):
    if not category_slug:
        return DISCUSSIONS
    return [item for item in DISCUSSIONS if item["category"] == category_slug]


def get_discussion(category_slug, discussion_id):
    for item in DISCUSSIONS:
        if item["category"] == category_slug and item["id"] == discussion_id:
            return item
    return None
