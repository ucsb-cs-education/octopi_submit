from cStringIO import StringIO
from hashlib import sha1
from kurt import Project as KurtProject
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.security import authenticated_userid
from pyramid.view import view_config
from ..helpers import alphanum_key
from ..models import Project, Submission
import os

EXT_MAPPING = {'.oct': 'octopi', '.sb': 'scratch14', '.sb2': 'scratch20'}


@view_config(route_name='submission', request_method='POST',
             permission='create')
def submission_create(request):
    username = authenticated_userid(request)
    try:
        file_ = request.POST['file_to_upload'].file
        filename = request.POST['file_to_upload'].filename
        base, ext = os.path.splitext(filename)
        project = Project.get_project(request.POST['project'])
        if not project or not project.has_access(username) \
                or ext not in EXT_MAPPING:
            raise KeyError
    except (AttributeError, KeyError):
        # TODO: Pretty up this exception handling
        return HTTPBadRequest()

    # Compute the sha1sum of the file and build the response
    sha1sum = sha1(file_.read()).hexdigest()
    file_.seek(0)
    response = HTTPFound(request.route_url('submission.item',
                                           project_id=project.name,
                                           submission_id=sha1sum))

    # Check to see if we've already processed this file
    if Submission.exists(project, sha1sum, username=username):
        return response

    # Kurt closes the file-like object so we need to duplicate it
    if hasattr(file_, 'fileno'):
        tmp_file = os.fdopen(os.dup(file_.fileno()))
    else:
        tmp_file = StringIO(file_.read())

    # Load the file with Kurt
    try:
        scratch = KurtProject.load(tmp_file, format=EXT_MAPPING[ext])
    except Exception:  # Probably not a valid scratch file
        # TODO: Pretty up this exception handling
        return HTTPBadRequest()

    Submission.save(project, sha1sum, file_, ext, scratch, username)

    # Run the plugins
    #from hairball import Hairball
    #from ..hairball import octopi
    #hairball = Hairball(['-p', 'blocks.BlockCounts'])
    #hairball.initialize_plugins()

    return response


@view_config(route_name='submission.create', permission='create',
             renderer='octopi:templates/form_submit.pt')
def submission_form(request):
    username = authenticated_userid(request)
    projects = sorted((x.name for x in Project.get_user_projects(username)),
                      key=alphanum_key)
    return {'projects': projects}


@view_config(route_name='submission.item', request_method='GET',
             renderer='octopi:templates/submission_item.pt', permission='view')
def submission_item(submission, request):
    return {'submission': submission,
            'thumbnail_url': submission.get_thumbnail_url(request)}


@view_config(route_name='submission', request_method='GET', permission='list',
             renderer='octopi:templates/submission_list.pt')
def submission_list(request):
    username = authenticated_userid(request)
    owned = []
    subs_by_prod = {}
    for project in Project.get_user_projects(username):
        if username in project.owners:
            owned.append(project.name)
        submissions = project.get_user_submissions(username)
        if submissions:
            subs_by_prod[project.name] = submissions
    projects = sorted(subs_by_prod, key=alphanum_key)
    return {'owned': owned, 'projects': projects, 'subs_by_prod': subs_by_prod}
