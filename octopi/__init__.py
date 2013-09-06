from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from sqlalchemy import engine_from_config
from .models import (DBSession, Base, Project, ProjectFactory, RootFactory,
                     SubmissionFactory, groupfinder)


def set_routes(config):
    config.add_route('home', '/')
    config.add_route('robots', '/robots.txt')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('submission', '/sub/', factory=SubmissionFactory)
    config.add_route('submission.create', '/sub/_new',
                     factory=SubmissionFactory)
    config.add_route('submission.item', '/sub/{project_id}/{submission_id}/',
                     factory=ProjectFactory,
                     traverse='/{project_id}/{submission_id}')
    #config.add_route('register', '/register')


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    authn_policy = AuthTktAuthenticationPolicy('<SECRET>',
                                               callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()
    session_factory = UnencryptedCookieSessionFactoryConfig('<COOKIE_SECRET>')
    config = Configurator(settings=settings,
                          root_factory=RootFactory,
                          authentication_policy=authn_policy,
                          authorization_policy=authz_policy,
                          session_factory=session_factory)
    config.add_static_view('data', path=Project.STORAGE_PATH,
                           cache_max_age=3600)
    config.add_static_view('images', path='/tmp/octopi_images/',
                           cache_max_age=3600)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.include(set_routes)
    config.scan()
    return config.make_wsgi_app()
