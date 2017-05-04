from pyramid.view import view_config
from uuid import uuid4
import snfilter

from pyramid.httpexceptions import HTTPFound

@view_config(route_name='index', renderer='index.html')
def index(request):
    request.redis.incr("hits")
    return dict(homepage=request.redis.get("homepage"))

@view_config(route_name="createfeed")
def createfeed(request):
    feedname = request.params.get("feedname", "")
    if feedname is not "":
        id = str(uuid4())
        request.redis.set(id + ":name", feedname)
        return HTTPFound(request.route_url('editfeed', id=id))
    else:
        return HTTPFound(request.route_url("index"))


class FeedEditor(object):
    def __init__(self, request):
        self.request = request
        self.id = self.request.matchdict['id']
        self.redis = request.redis
        self.feedname = self.redis.get(self.id + ":name")
        if self.feedname is None:
            return HTTPFound(request.route_url('index'))
        self.members = self.redis.sscan_iter(self.id + ":names")

    @view_config(route_name="editfeed", renderer="editfeed.html")
    def editfeed(self):
        return dict(feedname=self.feedname.decode("utf-8"), id=self.id, members=self.members)

    @view_config(route_name="addname")
    def addname(self):
        name = self.request.params.get("name", "")
        if name is not "":
            self.redis.sadd(self.id + ":names", name)
        return HTTPFound(self.request.route_url("editfeed", id=self.id))
