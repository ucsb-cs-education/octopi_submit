from pyramid.view import view_config


@view_config(route_name='submit', renderer='octopi:templates/form_submit.pt')
def submit(request):
    return {'action': request.route_url('submission'), 'method': 'POST'}
