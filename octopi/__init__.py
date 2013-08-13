from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from .models import DBSession, Base, Submission


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view('data', path=Submission.STORAGE_PATH,
                           cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('submission', '/sub/')
    config.add_route('submit', '/sub/_new')
    config.add_route('submission_item', '/sub/{submission_id}/')
    config.scan()
    return config.make_wsgi_app()
