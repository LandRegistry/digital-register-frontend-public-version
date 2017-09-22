import requests
import json
import config
import logging
import logging.config
from datetime import datetime
from flask import Response, stream_with_context
from random import randint, choice

from service.utils import desensitise_data
from service.utils import get_ip_address
from service.error_handler import ApplicationError

LOGGER = logging.getLogger(__name__)

LAND_REGISTRY_PAYMENT_INTERFACE_BASE_URI = config.CONFIG_DICT['LAND_REGISTRY_PAYMENT_INTERFACE_BASE_URI']
REGISTER_TITLE_API_URL = config.CONFIG_DICT['REGISTER_TITLE_API'].rstrip('/')
LAND_REGISTRY_PAYMENT_INTERFACE_URI = config.CONFIG_DICT['LAND_REGISTRY_PAYMENT_INTERFACE_URI']
PUBLIC_ACCOUNT_SERVICES_API_URI = config.CONFIG_DICT['PUBLIC_ACCOUNT_SERVICES_API_URI']
PDF_API_URI = config.CONFIG_DICT['PDF_API_URI']


# This hits v1 of render_pdf of the pdf_generator_api
def get_title_summary_pdf(title, receipt, **kwargs):
    LOGGER.debug("STARTED: get_title_summary_pdf title: {}".format(title))
    try:
        title.update({"receipt": receipt})
        pdf_data = json.dumps(title)
    except Exception as e:
        LOGGER.error('get_title_summary_pdf failed. Invalid params:  {}'.format(e))
        return None

    try:
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        req = requests.post('{}/v1/pdf'.format(PDF_API_URI), stream=True, data=pdf_data, headers=headers)
        LOGGER.debug('get_title_summary_pdf response: {}'.format(req))
        req.raise_for_status()
        response = Response(stream_with_context(req.iter_content(chunk_size=10 * 1024)),
                            content_type='application/pdf')
        response.headers["Content-Disposition"] = "attachment; filename=summary-of-{}.pdf".format(title['number'])
        LOGGER.debug("ENDED: get_title_summary_pdf")
    except Exception as e:
        LOGGER.error('get_title_summary_pdf failed. Exception {}'.format(e))
        raise e

    return response


def get_title(title_number):
    LOGGER.debug("STARTED: get_title title_number: {}".format(title_number))
    response = requests.get('{}/titles/{}'.format(REGISTER_TITLE_API_URL, title_number))
    LOGGER.debug('get_title response: {}'.format(response))
    if response.status_code == 200:
        LOGGER.debug("ENDED: get_title")
        return _to_json(response)
    elif response.status_code == 404:
        LOGGER.debug("ENDED: get_title")
        return None
    else:
        error_msg = 'API returned an unexpected response ({0}) when called for a title'.format(
            response.status_code
        )
        LOGGER.debug("ENDED: get_title")
        raise Exception(error_msg)


class SearchRateLimitExceeded(ApplicationError):
    def __init__(self, response):
        rate_limit_headers = ['X-RateLimit-Limit', 'X-RateLimit-Remaining', 'Retry-After', 'X-RateLimit-Reset']

        response_data = response.json()

        self.message = 'Search rate limit hit'
        self.http_code = 429
        self.code = 'search_rate_limit'
        self.limit_headers = {k: v for k, v in response.headers.items() if k in rate_limit_headers}
        self.limit_exceeded = response_data['limit_exceeded']


def get_titles_by_postcode(postcode, page_number):
    LOGGER.debug("STARTED: get_titles_by_postcode postcode, pagenumber: {0}, {1}".format(
        postcode, page_number
    ))
    try:
        response = requests.get(
            '{}/title_search_postcode/{}'.format(REGISTER_TITLE_API_URL, postcode),
            params={'page': page_number, 'user_ip': get_ip_address()}
        )
        response.raise_for_status()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            raise SearchRateLimitExceeded(response) from e
        else:
            raise

    LOGGER.debug("get_titles_by_postcode {0}".format(response))
    LOGGER.debug("ENDED: get_titles_by_postcode")
    return _to_json(response)


def get_titles_by_address(address, page_number):
    LOGGER.debug("STARTED: get_titles_by_address address, page_number: {0}, {1}".format(
        address, page_number
    ))
    try:
        response = requests.get(
            '{}/title_search_address/{}'.format(REGISTER_TITLE_API_URL, address),
            params={'page': page_number, 'user_ip': get_ip_address()}
        )
        response.raise_for_status()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            raise SearchRateLimitExceeded(response) from e
        else:
            raise

    LOGGER.debug("get_titles_by_address {0}".format(response))
    LOGGER.debug("ENDED: get_titles_by_address")
    return _to_json(response)


def check_health():
    return requests.get('{0}/health'.format(REGISTER_TITLE_API_URL))


def get_official_copy_data(title_number):
    LOGGER.debug("STARTED: get_official_copy_data title_number: {}".format(title_number))
    response = requests.get(
        '{}/titles/{}/official-copy'.format(REGISTER_TITLE_API_URL, title_number)
    )

    if response.status_code == 200:
        LOGGER.debug("ENDED: get_official_copy_data")
        return _to_json(response)
    elif response.status_code == 404:
        LOGGER.debug("ENDED: get_official_copy_data")
        return None
    else:
        error_msg_format = (
            'API returned an unexpected response ({0}) when called for official copy data'
        )
        LOGGER.debug("ENDED: get_official_copy_data")
        raise Exception(error_msg_format.format(response.status_code))


def save_search_request(search_parameters):
    """Saves user's Search Request and returns the 'cart id' and 'search_datetime'."""
    LOGGER.debug("STARTED: save_search_request search_parameters: {}".format(search_parameters))
    response = requests.post('{}/save_search_request'.format(REGISTER_TITLE_API_URL), json=search_parameters)
    response.raise_for_status()
    LOGGER.debug("save_search_request: {0}".format(response))
    LOGGER.debug("ENDED: save_search_request")
    json_response = json.loads(response.text)
    return json_response


def update_search_request(username, search_datetime, title_number):
    """Updates thes search_request save with the user_id after the user has signed in"""
    LOGGER.debug("STARTED: update_search_request username: {} search_datetime: {}, title_number: {}".format(username, search_datetime, title_number))

    update_search_details = {
        'user_id': username,
        'search_datetime': search_datetime,
        'title_number': title_number
    }

    response = requests.post(
        '{}/update_search_request'.format(REGISTER_TITLE_API_URL), json=update_search_details
    )
    response.raise_for_status()
    LOGGER.debug("update_search_request: {}".format(response))
    LOGGER.debug("ENDED: update_search_request")
    return response


def get_pound_price(product='drvSummary'):
    """Get price value (nominally in pence) and convert to Pound format if necessary.

    :param product: str (product type)
    :return: decimal (price in pounds)
    """
    LOGGER.debug("STARTED: get_pound_price product: {}".format(product))
    response = requests.get('{}/get_price/{}'.format(REGISTER_TITLE_API_URL, product))
    response.raise_for_status()
    try:
        price = int(response.text)
    except ValueError as e:
        LOGGER.debug("ENDED: with error: get_pound_price")
        raise Exception('Nominal price is not an integer (pence value)', e)

    if price % 1 == 0:
        price /= 100
    LOGGER.debug("get_pound_price: {0}".format(price))
    LOGGER.debug("ENDED: get_pound_price")
    return price


def user_can_view(username, title_number):
    """Check whether user has access or not."""
    LOGGER.debug("STARTED: user_can_view username, title_number: {0}, {1}".format(
        username, title_number
    ))
    response = requests.get('{}/user_can_view/{}/{}'.format(REGISTER_TITLE_API_URL, username, title_number))
    LOGGER.debug("get_pound_price: {0}".format(response))
    LOGGER.debug("ENDED: user_can_view")
    return response.status_code == 200


def _to_json(response):
    try:
        return response.json()
    except Exception as e:
        raise Exception('API response body is not JSON', e)


def _get_time():
    # Postgres datetime format is YYYY-MM-DD MM:HH:SS.mm
    _now = datetime.now()
    return _now.strftime("%Y-%m-%d %H:%M:%S.%f")


def get_invoice_data(transaction_id):
    LOGGER.debug("STARTED: get_invoice_data transaction_id: {}".format(transaction_id))
    response = requests.get(
        '{}/get-invoice-data?transId={}'.format(LAND_REGISTRY_PAYMENT_INTERFACE_BASE_URI, transaction_id)
    )
    response.raise_for_status()
    LOGGER.debug("get_invoice_data: {}".format(response))
    LOGGER.debug("ENDED: get_invoice_data")
    return response


def create_account(form_data):
    """Method that will place the correct form values passed in from the frontend to the expected values for the api call.

    Then it will call the api, with those values, and return the response
    :param form_data:
    :return:
    """
    LOGGER.debug('Start create_account')
    try:
        account_details = {
            'userId': form_data['email'],
            'password': form_data['password'],
            'familyName': form_data['surname'],
            'commonName': form_data['firstname'],
            'phonenumber': form_data.get('phone'),
            'address1': form_data['address1'],
            'title': form_data['title'],
            'city': form_data['city'],
            'country': form_data['country'],
            'postcode': form_data.get('postcode'),
            'requestorID': config.CONFIG_DICT['REQUESTORID'],
            'org': config.CONFIG_DICT['ORG'],
            'orgUnit': config.CONFIG_DICT['ORGUNIT'],
            'localityName': config.CONFIG_DICT['LOCALITYNAME'],
            'roles': config.CONFIG_DICT['ROLES'],
            'email': form_data['email'].lower(),
            'createdBy': 'FPI',
        }
    except Exception as e:
        LOGGER.error('create_account failed. Invalid params:  {}'.format(e))
        return Response(status=500)
    LOGGER.debug('Before api call using : {}'.format(desensitise_data(account_details)))
    try:
        response = requests.post('{}/create_account'.format(PUBLIC_ACCOUNT_SERVICES_API_URI), json=account_details)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 422:
            return response
    except Exception as e:
        LOGGER.error('create_account failed. Exception {}'.format(e))
        return response
    LOGGER.debug('End create_account')
    return response


def request_reset_password(form_data):
    """Method that calls the pasa web service /request-reset-password
    with the username and esec admin user

    Args:
        form_data

    Returns:
        response
    """
    LOGGER.debug('Start request_reset_password')
    try:
        password_reset_details = {
            'userID': form_data['email'],
            'requestorID': config.CONFIG_DICT['REQUESTORID']
        }
    except Exception as e:
        LOGGER.error("Request for reset password email has failed. Invalid params: {}".format(e))
        return Response(status=500)

    LOGGER.debug('Sending request for password reset email using: {}'.format(password_reset_details))
    try:
        response = requests.post('{}/request-reset-password'.format(PUBLIC_ACCOUNT_SERVICES_API_URI), json=password_reset_details)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 422 or response.status_code == 429:
            return response
    except Exception as e:
        LOGGER.error('request_reset_password failed. Exception {}'.format(e))
        return None
    LOGGER.debug('End request_reset_password response: {}'.format(response.json()))

    return response


def validate_password_reset_token(token):
    """Method that calls the pasa web service /validate-password-reset-token with the token

    Args:
        token

    Returns:
        response
    """

    LOGGER.debug("Start validate_password_reset_token")
    token_check_details = {
        'token': token,
    }

    try:
        response = requests.post('{}/validate-password-reset-token'.format(PUBLIC_ACCOUNT_SERVICES_API_URI), json=token_check_details)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 422:
            return response
    except Exception as e:
        LOGGER.error('validate_password_reset_token failed. Exception {}'.format(e))
        return None
    LOGGER.debug("End validate_password_reset_token with response: {}".format(response))
    return response


def change_password(token, form_data):
    """Method that calls the pasa web service /enact-reset-password with the token and password from the form

    Args:
        form_data
        token

    Returns:
        response
    """
    LOGGER.debug("Start change_password")
    try:
        change_password_details = {
            'newPW': form_data['password'],
            'token': token,
            'requestorID': config.CONFIG_DICT['REQUESTORID'],
        }
    except Exception as e:
        LOGGER.error("Request for change password has failed. Invalid params: {}".format(e))
        return None

    LOGGER.debug("Sending request to change password sent with: {}".format(desensitise_data(change_password_details)))
    try:
        response = requests.post('{}/enact-reset-password'.format(PUBLIC_ACCOUNT_SERVICES_API_URI), json=change_password_details)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 422:
            return response
    except KeyError as e:
        LOGGER.error('change_password failed. Exception {}'.format(e))
        return None
    LOGGER.debug("End change_password with response: {}".format(response.json()))
    return response


def get_account_details(email):
    LOGGER.debug('Start check_username_based_account')

    response = requests.post('{}/get-account-details'.format(PUBLIC_ACCOUNT_SERVICES_API_URI), json={'email': email})
    response.raise_for_status()

    LOGGER.debug('End get-account-details')
    return response.json()


def _generate_random_password():
    """Generate a password that includes 2 human recognizable words and 2 digits"""
    selectable_words = ['dawn', 'book', 'cake', 'card', 'tree', 'word', 'skip', 'bark', 'page', 'know']
    random_number = randint(11, 68)
    generated_password = '{}{}{}'.format(choice(selectable_words), choice(selectable_words), random_number)
    return generated_password
