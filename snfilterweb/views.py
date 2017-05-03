from pyramid.view import view_config
from uuid import uuid4

@view_config(route_name='index', renderer='base.html')
def index(request):
    return dict()
