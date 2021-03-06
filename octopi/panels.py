from pyramid_layout.panel import panel_config


@panel_config(name='navbar', renderer='octopi:templates/panels/navbar.pt')
def navbar(context, request):
    def nav_item(name, url):
        active = request.current_route_url() == url
        return {'active': active, 'name': name, 'url': url}
    nav = [nav_item('Turn In', request.route_url('submission.create')),
           nav_item('Submissions', request.route_url('submission'))]

    title = 'OCTOPI'
    if request.user:
        nav.append(nav_item('Logout', request.route_url('logout')))
        title += ' ({})'.format(request.user.username)
    else:
        nav.append(nav_item('Login', request.route_url('login')))
    return {'nav': nav, 'title': title}
