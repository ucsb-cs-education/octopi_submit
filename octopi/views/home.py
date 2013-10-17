from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config


@view_config(route_name='home')
def home(request):
    if request.user:
        url = request.route_path('submission.create')
    else:
        url = request.route_path('login')
    raise HTTPFound(location=url)


@view_config(route_name='robots', request_method='GET', http_cache=86400)
def robots(request):
    return Response(body='User-agent: *\nDisallow: /\n',
                    content_type=str('text/plain'))
