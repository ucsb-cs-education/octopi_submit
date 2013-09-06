from pyramid.response import Response
from pyramid.view import view_config


@view_config(route_name='home', renderer='octopi:templates/home.pt')
def home(request):
    return {}


@view_config(route_name='robots', request_method='GET', http_cache=86400)
def robots(request):
    return Response(body='User-agent: *\nDisallow: /\n',
                    content_type=str('text/plain'))
