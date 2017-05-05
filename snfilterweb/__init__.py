from pyramid.config import Configurator
import redis
import requests

def redisconnection(request):
    host = request.registry.settings["redis.host"]
    port = request.registry.settings["redis.port"]
    db = request.registry.settings["redis.db"]
    return redis.Redis(host=host, port=port, db=db)

def get_feed(request):
    rawfeed = request.redis.get("rawfeed")
    if rawfeed is None:
        r = requests.get(request.registry.settings["spotternetwork.feed"])
        if r.ok:
            request.redis.setex("rawfeed", r.text, 60)
            rawfeed = r.text
    else:
        rawfeed = rawfeed.decode('utf-8')
    return rawfeed

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')
    config.add_renderer(".html", "pyramid_jinja2.renderer_factory")
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_request_method(redisconnection, "redis", reify=True)
    config.add_request_method(get_feed, "rawfeed", reify=True)
    config.add_route('index', '/')
    config.add_route('createfeed', '/createfeed')
    config.add_route('editfeed', '/editfeed/{id}')
    config.add_route('addname', '/addname/{id}')
    config.add_route('delname', '/delname/{id}')
    config.add_route('feed', '/feed/{viewid}/{feedformat}')
    config.add_route('origfeed', '/origfeed')
    config.scan()
    return config.make_wsgi_app()
