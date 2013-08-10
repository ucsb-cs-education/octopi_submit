from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config
from hashlib import sha1
from ..models import Submission
import os


@view_config(route_name='submission', request_method='POST')
def submission_create(request):
    file_ = request.POST['file_to_upload'].file
    sha1sum = sha1(file_.read()).hexdigest()
    path = os.path.join(Submission.STORAGE_PATH, sha1sum)

    response = HTTPFound(request.route_url('submission_item',
                                           submission_id=sha1sum))
    if os.path.isfile(path):
        return response

    temp_path = path + '~'
    file_.seek(0)
    with open(temp_path, 'wb') as fp:
        fp.write(file_.read())
    os.rename(temp_path, path)
    return response


@view_config(route_name='submission_item', request_method='GET',
             renderer='octopi:templates/submission_item.pt')
def submission_item(request):
    submission = Submission.get_submission(request.matchdict['submission_id'])
    if not submission:
        return HTTPNotFound()
    return {'submission': submission}


@view_config(route_name='submission', request_method='GET',
             renderer='octopi:templates/submission_list.pt')
def submission_list(request):
    return {'submissions': Submission.get_submission_list()}
