from pyramid.httpexceptions import HTTPForbidden, HTTPFound
from pyramid.security import authenticated_userid
from pyramid.view import forbidden_view_config


@forbidden_view_config()
def forbidden_view(request):
    if authenticated_userid(request):
        return HTTPForbidden()
    location = request.route_url('login', _query=(('next', request.path),))
    return HTTPFound(location=location)
