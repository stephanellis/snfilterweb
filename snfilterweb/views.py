from pyramid.view import view_config
from uuid import uuid4

import json

from pyramid.httpexceptions import HTTPFound

from snfilter import parse_nameslist, filter_feed, output_gr, output_truvu

@view_config(route_name='index', renderer='index.html')
def index(request):
    request.redis.incr("hits")
    return dict(homepage=request.redis.get("homepage"))

@view_config(route_name='stats', renderer='stats.html')
def getstats(request):
    return dict()

@view_config(route_name="createfeed")
def createfeed(request):
    feedname = request.params.get("feedname", "")
    if feedname is not "":
        id = str(uuid4())
        viewid = str(uuid4())
        request.redis.set(id + ":name", feedname)
        request.redis.set(id +":view", viewid)
        request.redis.set(viewid + ":feed", id)
        return HTTPFound(request.route_url('editfeed', id=id))
    else:
        return HTTPFound(request.route_url("index"))

@view_config(route_name="origfeed", renderer="string")
def origfeed(request):
    request.redis.incr("totalhits")
    request.redis.incr("orighits")
    return request.rawfeed

@view_config(route_name="feed", renderer="string")
def feed(request):
    viewid = request.matchdict['viewid']
    feedformat = request.matchdict['feedformat']
    id = request.redis.get(viewid + ":feed")
    if id is None:
        return HTTPFound(request.route_url('index'))
    else:
        id = id.decode('utf-8')
    ff = get_filtered_feed(id, request)
    request.redis.incr(id + ":hits")
    request.redis.incr("totalhits")
    if feedformat == "gr":
        name = request.redis.get(id + ":name").decode('utf-8')
        return output_gr(ff, filtername=name)
    if feedformat == "json":
        return json.dumps(ff, indent=2)
    if feedformat == "truvu":
        name = request.redis.get(id + ":name").decode('utf-8')
        request.response.headers["Content-Disposition"] = "attachment; filename=\"%s.csv\"" % name
        return output_truvu(ff)

def get_filtered_feed(id, request):
    o = dict()
    nameslist = ",".join([ x.decode('utf-8') for x in request.redis.sscan_iter(id + ":names") ])
    names, xlator = parse_nameslist(nameslist)
    return filter_feed(request.rawfeed, names, translator=xlator)

class FeedEditor(object):
    def __init__(self, request):
        self.request = request
        self.id = self.request.matchdict['id']
        self.redis = request.redis
        self.feedname = self.redis.get(self.id + ":name")
        self.viewid = self.redis.get(self.id + ":view")

        if self.feedname is None or self.viewid is None:
            return HTTPFound(request.route_url('index'))
        else:
            self.feedname = self.feedname.decode('utf-8')
            self.viewid = self.viewid.decode('utf-8')

        self.members = self.redis.sscan_iter(self.id + ":names")
        self.nameslist = ",".join([ x.decode('utf-8') for x in self.redis.sscan_iter(self.id + ":names") ])

    def filter_feed_gr(self):
        return output_gr(get_filtered_feed(self.id, self.request), filtername=self.feedname)

    @view_config(route_name="editfeed", renderer="editfeed.html")
    def editfeed(self):
        return dict(
            feedname=self.feedname,
            id=self.id,
            members=self.members,
            output=self.filter_feed_gr(),
            nameslist=self.nameslist,
            viewid=self.viewid
            )

    @view_config(route_name="addname")
    def addname(self):
        name = self.request.params.get("name", "")
        if name is not "":
            self.redis.sadd(self.id + ":names", name)
        return HTTPFound(self.request.route_url("editfeed", id=self.id))

    @view_config(route_name="delname")
    def delname(self):
        name = self.request.params.get("name", "")
        if name is not "":
            if self.redis.sismember(self.id + ":names", name):
                self.redis.srem(self.id + ":names", name)
        return HTTPFound(self.request.route_url("editfeed", id=self.id))
