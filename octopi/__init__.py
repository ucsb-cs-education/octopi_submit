from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from .models import (ClassFactory, RootFactory,
                     STORAGE_PATH, SubmissionFactory, groupfinder)


def set_routes(config):
    config.add_route('home', '/')
    config.add_route('robots', '/robots.txt')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('submission', '/sub/', factory=SubmissionFactory)
    config.add_route('submission.create', '/sub/_new',
                     factory=SubmissionFactory)
    config.add_route('submission.item',
                     '/sub/{class_id}/{project_id}/{submission_id}/',
                     factory=ClassFactory,
                     traverse='/{class_id}/{project_id}/{submission_id}')


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application."""
    authn_policy = AuthTktAuthenticationPolicy('<SECRET>',
                                               callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()
    session_factory = UnencryptedCookieSessionFactoryConfig('<COOKIE_SECRET>')
    config = Configurator(settings=settings,
                          root_factory=RootFactory,
                          authentication_policy=authn_policy,
                          authorization_policy=authz_policy,
                          session_factory=session_factory)
    config.add_static_view('data', path=STORAGE_PATH,
                           cache_max_age=3600)
    config.add_static_view('images', path='/tmp/octopi_images/',
                           cache_max_age=3600)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.include(set_routes)
    config.scan()
    return config.make_wsgi_app()
