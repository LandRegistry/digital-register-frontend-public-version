from collections import OrderedDict
from service import api_client
import logging

LOGGER = logging.getLogger(__name__)

healthchecks = OrderedDict([
    ('digital-register-api', api_client.check_health),
])


# TODO(Your Name): tested through test_app - should have its own tests now
def perform_healthchecks():
    LOGGER.debug("STARTED: perform_healthchecks")
    results = [_check_application_health(app_name) for app_name in healthchecks.keys()]
    LOGGER.debug("perform_healthchecks: {0}".format(results))
    error_messages = [error_msg for result in results for error_msg in result]
    LOGGER.debug("ENDED: perform_healthchecks")
    return error_messages


def _check_application_health(application_name):
    LOGGER.debug("STARTED: _check_application_health application_name: {}".format(application_name))
    try:
        healthcheck_response = healthchecks[application_name]()
        response_json = _get_json_from_response(healthcheck_response)

        if response_json:
            LOGGER.debug("ENDED: _check_application_health")
            return _extract_errors_from_health_response_json(response_json, application_name)
        else:
            LOGGER.debug("ENDED: with error: _check_application_health")
            return ['{0} health endpoint returned an invalid response: {1}'.format(
                application_name, healthcheck_response.text)]
    except Exception as e:
        LOGGER.debug("ENDED: _check_application_health")
        return ['Problem talking to {0}: {1}'.format(application_name, str(e))]


def _get_json_from_response(response):
    try:
        return response.json()
    except Exception:
        return None


def _extract_errors_from_health_response_json(response_json, application_name):
    if response_json.get('status') == 'ok':
        return []
    elif response_json.get('errors'):
        return ['{0} health endpoint returned errors: {1}'.format(
            application_name, response_json['errors'])]
    else:
        return ['{0} health endpoint returned an invalid response: {1}'.format(
            application_name, response_json)]
