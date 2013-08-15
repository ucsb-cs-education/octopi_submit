from pyramid_layout.panel import panel_config


@panel_config(name='navbar', renderer='octopi:templates/panels/navbar.pt')
def navbar(context, request):
    def nav_item(name, url):
        active = request.current_route_url() == url
        return {'active': active, 'name': name, 'url': url}
    nav = [nav_item('Home', request.route_url('home')),
           nav_item('Submit', request.route_url('submission.create')),
           nav_item('Submissions', request.route_url('submission'))]
    return {'nav': nav, 'title': 'OCTOPI'}
