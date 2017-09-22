import copy
from flask import request
from service import auditing
import re
import logging
import logging.config

LOGGER = logging.getLogger(__name__)


def request_wants_json():
    """Simple method which can be used to negotiate based on the Accept header

    Use it like:

    if utils.request_wants_json():
        return jsonify(...)
    else
        return render_template(...)

    See http://flask.pocoo.org/snippets/45
    """
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])

    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']


def get_ip_address():
    ip_address_actual = request.headers.get("iv-remote-address", None)
    if ip_address_actual:
        auditing.audit("IP Address: {}".format(ip_address_actual))
    if ip_address_actual is None:
        auditing.audit("IP ADDRESS EMPTY")
    return ip_address_actual


def desensitise_data(data_to_amend):
    """Need to remove certain items for security reasons

    Returns: The same json keys but with redacted values
    For example :
    {'UserId': 'someone@somewhere.com'} turns into {'UserId': 'XXXXXXX'}

    """
    clean_json = copy.deepcopy(data_to_amend)
    key_values_to_amend = ['currentPW', 'newPW', 'requestorID', 'title', 'phonenumber', 'commonName',
                           'address1', 'address2', 'address3', 'password', 'familyName', 'postcode', 'org', 'title']
    for key in clean_json:
        if key in key_values_to_amend:
            clean_json[key] = 'XXXXXXX'

    return clean_json


def username_from_header(request):
    # Gets username, if any, from webseal headers
    user_id = request.headers.get("iv-user", None)
    if user_id:
        p = re.compile("[%][{0-9}][{0-9}]")
        user_id = p.sub("", user_id)
    if user_id == "Unauthenticated":
        user_id = None
    LOGGER.debug("_username_from_header: {0}".format(user_id))
    return user_id
