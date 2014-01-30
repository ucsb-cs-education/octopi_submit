from cStringIO import StringIO
from hashlib import sha1
from kelp.kelpplugin import KelpPlugin
from kurt import Project as KurtProject
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden, HTTPFound
from pyramid.view import view_config
from zipfile import ZipFile
from ..helpers import alphanum_key
from ..models import CLASSES, Submission
import json
import kelp.offline  # Required to load octx
import os

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
        zip_file = None
        if ext == '.octx':  # Attempt to read as zip and look for project.oct
            zip_file = to_upload.file
            with ZipFile(to_upload.file) as zfp:
                to_upload.file = StringIO(zfp.open('project.oct').read())
                to_upload.file.seek(0)
                ext = '.oct'
        elif ext not in EXT_MAPPING:
            raise Exception('Invalid extension')
    except Exception:
        return HTTPBadRequest()

    # Verify authorization
    if 'admin' not in request.user.groups and \
            class_name not in request.user.classes_dict:
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
    if project.has_submission(sha1sum, add_user=request.user,
                              zip_file=zip_file):
        pass  # For now re-process the submission (loses history)
        #return response
    # Load the file with Kurt
    try:
        scratch = KurtProject.load(to_upload.file, format=EXT_MAPPING[ext])
    except Exception:  # Probably not a valid scratch file
        # TODO: Pretty up this exception handling
        return HTTPBadRequest()
    # Save the project
    Submission.save(project, sha1sum, to_upload.file, ext, scratch,
                    request.user, zip_file, save_name=to_upload.filename)

    # Write the results (nothing to save anymore)
    dir_path = os.path.join(project.path, sha1sum)
    open(os.path.join(dir_path, 'results.html'), 'w').close()
    # Save the flash message
    request.session.flash('Thanks for submitting your project!')
    return response


@view_config(route_name='submission.create', permission='create',
             renderer='octopi:templates/form_submit.pt')
def submission_form(request):
    projects = request.user.get_projects()
    return {'projects': sorted(projects, key=lambda x: x.display_name)}


@view_config(route_name='submission.item', request_method='GET',
             renderer='octopi:templates/submission_item.pt', permission='view')
def submission_item(submission, request):
    return {'submission': submission,
            'content': submission.get_results(),
            'thumbnail_url': submission.get_thumbnail_url(request),
            'flash': request.session.pop_flash()}


@view_config(route_name='submission', request_method='GET', permission='list',
             renderer='octopi:templates/submission_list.pt')
def submission_list(request):
    def group_by_date(items):
        date = None
        group = []
        retval = []
        for item in sorted(items, reverse=True, key=lambda x: x.created_at):
            if date and item.created_at.date() != date:
                retval.append((date, group))
                group = []
            date = item.created_at.date()
            group.append(item)
        if group:
            retval.append((date, group))
        return retval

    owned = []
    projects = request.user.get_projects()
    subs_by_prod = {}
    for project in projects:
        if project.class_.name in request.user.owner_of:
            owned.append(project.name)
        submissions = project.get_submissions(request.user)
        if submissions:
            if project.name in subs_by_prod:
                subs_by_prod[project.name].extend(submissions)
            else:
                subs_by_prod[project.name] = submissions

    for key in subs_by_prod:
        subs_by_prod[key] = group_by_date(subs_by_prod[key])

    projects = sorted(subs_by_prod, key=alphanum_key)
    return {'owned': owned, 'projects': projects, 'subs_by_prod': subs_by_prod}
