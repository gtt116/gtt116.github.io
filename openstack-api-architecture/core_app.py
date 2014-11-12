import eventlet
from eventlet import wsgi


def core_app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return "hello netease"


def authorize(environ, start_response):
    if environ['HTTP_X_AUTH_TOKEN'] == 'openstack':
        return core_app(environ, start_response)
    else:
        start_response('401 Unauthorized', [('Content-Type', 'text/plain')])
        return '401 Unauthorized'


wsgi.server(eventlet.listen(('', 8090)), authorize)
