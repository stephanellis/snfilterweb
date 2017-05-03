from pyramid.view import view_config
from uuid import uuid4
import snfilter

@view_config(route_name='index', renderer='index.html')
def index(request):
    request.redis.incr("hits")
    return dict(homepage=request.redis.get("homepage"))
