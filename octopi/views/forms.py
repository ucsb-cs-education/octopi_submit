from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
from pyramid.view import view_config
from ..models import USERS


@view_config(route_name='submission.create', permission='create',
             renderer='octopi:templates/form_submit.pt')
def submit(request):
    return {'action': request.route_url('submission'), 'method': 'POST'}


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
