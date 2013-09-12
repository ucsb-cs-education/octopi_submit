from cStringIO import StringIO
from hashlib import sha1
from kelp.kelpplugin import KelpPlugin
from kelp.offline import (htmlwrappers as HTML_WRAPPERS,
                          plugins as PLUGIN_MAPPING)
from kurt import Project as KurtProject
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden, HTTPFound
from pyramid.security import authenticated_userid
from pyramid.view import view_config
from zipfile import ZipFile
from ..helpers import alphanum_key
from ..models import CLASSES, Submission, USERS
import json
import os
import traceback

EXT_MAPPING = {'.oct': 'octopi', '.sb': 'scratch14', '.sb2': 'scratch20'}


# Monkey patch get_paths function to save images as we want them
def _get_paths(image, *args, **kwargs):
    sha1sum = sha1(image.image._pil_image.tostring()).hexdigest()
    filename = '{}.png'.format(sha1sum)
    file_path = os.path.join('/tmp/octopi_images', filename)
    url_path = '/images/{}'.format(filename)
    return file_path, url_path
KelpPlugin.get_paths = staticmethod(_get_paths)


@view_config(route_name='submission', request_method='POST',
             permission='create')
def submission_create(request):
    # Validate fields
    try:
        class_name, project_name = json.loads(request.POST['project'])
        to_upload = request.POST['file_to_upload']
        base, ext = os.path.splitext(to_upload.filename)
        if ext == '.zip':  # Attempt to read as zip and look for project.oct
            with ZipFile(to_upload.file) as zfp:
                to_upload.file = StringIO(zfp.open('project.oct').read())
                to_upload.file.seek(0)
                ext = '.oct'
        elif ext not in EXT_MAPPING:
            raise Exception('Invalid extension')
    except Exception:
        return HTTPBadRequest()

    # Verify authorization
    user = USERS[authenticated_userid(request)]
    if 'admin' not in user.groups and class_name not in user.classes_dict:
        return HTTPForbidden()

    # Verify project exists
    project = CLASSES[class_name].projects.get(project_name)
    if not project:
        return HTTPBadRequest()

    # Compute the sha1sum of the file and build the response
    sha1sum = sha1(to_upload.file.read()).hexdigest()
    to_upload.file.seek(0)
    response = HTTPFound(request.route_url('submission.item',
                                           class_id=class_name,
                                           project_id=project_name,
                                           submission_id=sha1sum))

    # Check to see if we've already processed this file
    if project.has_submission(sha1sum, add_user=user):
        pass  # For now re-process the submission
        #return response
    # Load the file with Kurt
    try:
        scratch = KurtProject.load(to_upload.file, format=EXT_MAPPING[ext])
    except Exception:  # Probably not a valid scratch file
        # TODO: Pretty up this exception handling
        return HTTPBadRequest()
    # Save the project
    Submission.save(project, sha1sum, to_upload.file, ext, scratch, user)

    # Run each plugin and append its HTML template output to the HTML result
    dir_path = os.path.join(project.path, sha1sum)
    html = []
    try:
        for plugin_class in PLUGIN_MAPPING[project.plugin]:
            plugin = plugin_class()
            results = plugin._process(scratch)
            html.append(HTML_WRAPPERS[plugin.__class__.__name__](results))
    except:
        html.append('<pre>{}</pre>'.format(traceback.format_exc()))
    with open(os.path.join(dir_path, 'results.html'), 'w') as fp:
        fp.write('\n'.join(html))
    return response


@view_config(route_name='submission.create', permission='create',
             renderer='octopi:templates/form_submit.pt')
def submission_form(request):
    projects = USERS[authenticated_userid(request)].get_projects()
    return {'projects': sorted(projects, key=lambda x: x.display_name)}


@view_config(route_name='submission.item', request_method='GET',
             renderer='octopi:templates/submission_item.pt', permission='view')
def submission_item(submission, request):
    return {'submission': submission,
            'content': submission.get_results(),
            'thumbnail_url': submission.get_thumbnail_url(request)}


@view_config(route_name='submission', request_method='GET', permission='list',
             renderer='octopi:templates/submission_list.pt')
def submission_list(request):
    user = USERS[authenticated_userid(request)]
    owned = []
    projects = user.get_projects()
    subs_by_prod = {}
    for project in projects:
        if project.class_.name in user.owner_of:
            owned.append(project.name)
        submissions = project.get_submissions(user)
        if submissions:
            subs_by_prod[project.name] = submissions
    projects = sorted(subs_by_prod, key=alphanum_key)
    return {'owned': owned, 'projects': projects, 'subs_by_prod': subs_by_prod}
