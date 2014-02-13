from cStringIO import StringIO
from cgi import FieldStorage
from hashlib import sha1
from kelp.kelpplugin import KelpPlugin
from kelp.offline import htmlwrappers
from kurt import Project as KurtProject
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden, HTTPFound
from pyramid.view import view_config
from traceback import format_exc
from zipfile import ZipFile
from ..models import CLASSES, PROJECTS, Submission
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
    # Validate form submission
    if 'file_to_upload' not in request.POST:
        return HTTPBadRequest()
    elif not isinstance(request.POST['file_to_upload'], FieldStorage):
        request.session.flash('Please select a file to upload.')
        return HTTPFound(request.route_url('submission.create'))

    # Validate fields
    try:
        to_upload = request.POST['file_to_upload']
        project_name, ext = os.path.splitext(to_upload.filename)
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
        print(format_exc())
        return HTTPBadRequest()

    # Submit to the first class the user is a member of
    if not request.user.classes_dict:
        return HTTPForbidden()
    class_name = request.user.classes_dict.keys()[0]

    # Find the appropriate project
    if project_name not in PROJECTS:
        project_name = '_OTHER_'
    project = CLASSES[class_name].projects[project_name]

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
        return response
    # Load the file with Kurt
    try:
        scratch = KurtProject.load(to_upload.file, format=EXT_MAPPING[ext])
    except Exception:  # Probably not a valid scratch file
        print(format_exc())
        return HTTPBadRequest()
    # Save the project
    Submission.save(project, sha1sum, to_upload, ext, scratch,
                    request.user, zip_file)

    # Write the results (nothing to save anymore)
    dir_path = os.path.join(project.path, sha1sum)
    html = []
    exceptions = []
    for plugin_class in project.plugins:
        try:
            plugin = plugin_class()
            results = plugin._process(scratch)
            html.append(htmlwrappers[plugin.__class__.__name__](results))
        except:
            exceptions.append(format_exc())
    if exceptions:
        html.append('<div class="alert alert-danger">There was an error '
                    'processing your submission. Please notify your teacher.'
                    '</div>')
        for exc in exceptions:
            html.append('<pre style="display: None">{}</pre>'.format(exc))
    with open(os.path.join(dir_path, 'results.html'), 'w') as fp:
        fp.write('\n'.join(html))
    # Save the flash message
    request.session.flash('Thanks for submitting your project!')
    return response


@view_config(route_name='submission.create', permission='create',
             renderer='octopi:templates/form_submit.pt')
def submission_form(request):
    return {'flash': request.session.pop_flash()}


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

    subs = []
    for project in request.user.get_projects():
        subs.extend(project.get_submissions(request.user))

    return {'sub_groups': group_by_date(subs)}
