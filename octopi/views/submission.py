from cStringIO import StringIO
from hairball import Hairball
from hashlib import sha1
from kurt import Project
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPNotFound
from pyramid.view import view_config
from ..hairball import octopi
from ..models import Submission
import os

EXT_MAPPING = {'.oct': 'octopi', '.sb': 'scratch14', '.sb2': 'scratch20'}


@view_config(route_name='submission', request_method='POST')
def submission_create(request):
    file_ = request.POST['file_to_upload'].file
    filename = request.POST['file_to_upload'].filename
    base, ext = os.path.splitext(filename)
    if ext not in EXT_MAPPING:
        # TODO: Pretty up this exceptio handling
        return HTTPBadRequest()

    # Compute the sha1sum of the file and build the response
    sha1sum = sha1(file_.read()).hexdigest()
    file_.seek(0)
    response = HTTPFound(request.route_url('submission_item',
                                           submission_id=sha1sum))

    # Check to see if we've already processed this file
    path = os.path.join(Submission.STORAGE_PATH, sha1sum)
    if os.path.isfile(path):
        return response

    # Kurt closes the file-like object so we need to duplicate it
    if hasattr(file_, 'fileno'):
        tmp_file = os.fdopen(os.dup(file_.fileno()))
    else:
        tmp_file = StringIO(file_.read())

    # Load the file with Kurt
    try:
        scratch = Project.load(tmp_file, format=EXT_MAPPING[ext])
    except Exception as e:  # Probably not a valid scratch file
        # TODO: Pretty up this exception handling
        print e
        return HTTPBadRequest()

    # Save a copy of the file
    temp_path = path + '~'
    with open(temp_path, 'wb') as fp:
        fp.write(file_.read())
    os.rename(temp_path, path)

    # Save the thumbnail
    scratch.thumbnail.save(path + '.png')

    # Run the plugins
    #hairball = Hairball(['-p', 'blocks.BlockCounts'])
    #hairball.initialize_plugins()

    return response


@view_config(route_name='submission_item', request_method='GET',
             renderer='octopi:templates/submission_item.pt')
def submission_item(request):
    submission = Submission.get_submission(request.matchdict['submission_id'])
    if not submission:
        return HTTPNotFound()
    return {'submission': submission,
            'thumbnail_url': submission.get_thumbnail_url(request)}


@view_config(route_name='submission', request_method='GET',
             renderer='octopi:templates/submission_list.pt')
def submission_list(request):
    return {'submissions': Submission.get_submission_list()}
