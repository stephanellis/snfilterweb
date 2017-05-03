from pyramid.config import Configurator
import redis

def redisconnection(request):
    return redis.Redis(request.registry.settings["redis.server"])

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')
    config.add_renderer(".html", "pyramid_jinja2.renderer_factory")
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_request_method(redisconnection, "redis", reify=True)
    config.add_route('index', '/')
    config.scan()
    return config.make_wsgi_app()
