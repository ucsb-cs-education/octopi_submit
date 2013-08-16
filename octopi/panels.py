from pyramid_layout.panel import panel_config
from pyramid.security import authenticated_userid


@panel_config(name='navbar', renderer='octopi:templates/panels/navbar.pt')
def navbar(context, request):
    def nav_item(name, url):
        active = request.current_route_url() == url
        return {'active': active, 'name': name, 'url': url}
    nav = [nav_item('Home', request.route_url('home')),
           nav_item('Submit', request.route_url('submission.create')),
           nav_item('Submissions', request.route_url('submission'))]

    title = 'OCTOPI'
    if authenticated_userid(request):
        nav.append(nav_item('Logout', request.route_url('logout')))
        title += ' ({})'.format(authenticated_userid(request))
    else:
        nav.append(nav_item('Login', request.route_url('login')))
    return {'nav': nav, 'title': title}
