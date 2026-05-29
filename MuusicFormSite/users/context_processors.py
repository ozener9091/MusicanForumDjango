from musicforum.data import get_menu


def get_forum_context(request):
    return {'menu': get_menu()}
