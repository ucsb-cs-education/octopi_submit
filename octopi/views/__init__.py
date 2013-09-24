from pyramid.httpexceptions import HTTPForbidden, HTTPFound
from pyramid.security import forget, remember
from pyramid.view import forbidden_view_config, view_config
from ..models import USERS


@forbidden_view_config()
def forbidden_view(request):
    if request.user:
        return HTTPForbidden()
    location = request.route_url('login', _query=(('next', request.path),))
    return HTTPFound(location=location)


@view_config(route_name='login', renderer='octopi:templates/form_login.pt')
def login(request):
    next_path = request.params.get('next') or request.route_url('home')
    login = ''
    failed = False
    if 'submit' in request.POST:
        login = request.POST.get('login', '')
        passwd = request.POST.get('passwd', '')
        user = USERS.get(login, None)
        if user and user.password == passwd:
            headers = remember(request, login)
            return HTTPFound(location=next_path, headers=headers)
        failed = True
    return {'login': login, 'next': next_path, 'failed': failed}


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    location = request.route_url('home')
    return HTTPFound(location=location, headers=headers)
