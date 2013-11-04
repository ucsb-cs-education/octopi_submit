from collections import defaultdict
from pyramid.httpexceptions import HTTPForbidden, HTTPFound
from pyramid.security import forget, remember
from pyramid.view import forbidden_view_config, view_config
from ..models import USERS
import json


@forbidden_view_config()
def forbidden_view(request):
    if request.user:
        return HTTPForbidden()
    location = request.route_url('login', _query=(('next', request.path),))
    return HTTPFound(location=location)


@view_config(route_name='login', renderer='octopi:templates/form_login.pt')
def login(request):
    next_path = (request.params.get('next') or
                 request.route_url('submission.create'))
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

    class_to_user = defaultdict(list)
    for user in USERS.values():
        name = user.username
        if name[-2:].isdigit():
            name = name[-2:]
        for class_ in user.classes:
            class_to_user[class_.display_name].append((name, user.username))
            class_to_user[class_.display_name].sort()

    return {'classes': sorted(class_to_user),
            'data': json.dumps(class_to_user),
            'next': next_path, 'failed': failed}


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    location = request.route_url('login')
    return HTTPFound(location=location, headers=headers)
