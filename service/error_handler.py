from flask import render_template, jsonify, redirect, url_for, flash, Markup
from werkzeug.exceptions import default_exceptions, HTTPException
import logging
from service import utils
from jinja2 import TemplateNotFound

GENERIC_ERROR_TITLE = 'Sorry, we are experiencing technical difficulties.'
GENERIC_ERROR_DESCRIPTION = 'Please try again in a few moments.'

ERROR_RESPONSES = {
    404: {
        'title': 'Page not found',
        'description': 'If you entered a web address please check it was correct.'
    },
    429: {
        'title': 'Too many requests',
        'description': 'The maximum rate allowed is {description}'
    }
}

LOGGER = logging.getLogger(__name__)


class ApplicationError(Exception):
    """
    This class is to be raised when the application identifies that there's been a problem
    and that the user should be informed.

    This should only be used for absolute edge case exceptions.
    As a matter of course, exceptions should be caught and dealt with higher up
    in the flow and users should be given a decent onward journey.

    Consider security issues when writing messages - what information might you
    be revealing to potential attackers?

    Example:
        raise ApplicationError('Friendly message here', 'E102', 400)
    """
    def __init__(self, message, code=None, http_code=500):
        Exception.__init__(self)
        self.message = message
        self.http_code = http_code
        self.code = code


def error_handler(error):
    LOGGER.debug("STARTED: error_handler")
    LOGGER.error('An error occurred when processing a request', exc_info=error)

    if isinstance(error, HTTPException):
        code = error.code
        error_title = GENERIC_ERROR_TITLE
        error_description = GENERIC_ERROR_DESCRIPTION
        error_response = ERROR_RESPONSES.get(code, False)
        if(error_response):
            error_title = error_response.get('title', GENERIC_ERROR_TITLE)
            error_description = error_response.get('description', GENERIC_ERROR_DESCRIPTION).format(**error.__dict__)
    else:
        code = 500
        error_title = GENERIC_ERROR_TITLE
        error_description = GENERIC_ERROR_DESCRIPTION

    LOGGER.debug("ENDED: error_handler")

    # Negotiate based on the Accept header
    if utils.request_wants_json():
        return jsonify({'status': 'fail', 'message': '{} - {}'.format(error_title, error_description)}), code
    else:
        return render_template("error.html",
                               error=error_title,
                               code=code,
                               description=error_description
                               ), code


class TitleSummaryViewExpired(Exception):
    code = 403
    description = 'Your viewing period has expired, please search again.'


# Replace with ApplicationException after flask-skeleton-ui arrives
def title_summary_view_expired_handler(e):
    flash(Markup('<p>' + e.description + '</p>'))
    return redirect(url_for('search'))


def application_error(e):
    LOGGER.debug('Application Exception: %s', repr(e), exc_info=True)

    # ApplicationError allows developers to specify an HTTP code.
    # This will be written to the logs correctly, but we don't want to allow
    # this code through to the user as it may expose internal workings of the system
    # (See OWASP guidelines on error handling)
    if e.http_code in [500, 404, 403, 429]:
        http_code = e.http_code
    else:
        http_code = 500

    if utils.request_wants_json():
        return jsonify({
                       'message': e.message,
                       'code': e.code
                       }), http_code
    else:
        try:
            return render_template('errors/application/{}.html'.format(e.code),
                                   description=e.message,
                                   code=e.code,
                                   e=e,
                                   http_code=http_code
                                   ), http_code
        except TemplateNotFound:
            return render_template('error.html',
                                   description=e.message,
                                   code=e.code,
                                   e=e,
                                   http_code=http_code
                                   ), http_code


def setup_errors(app):
    # Replace with ApplicationException after flask-skeleton-ui arrives
    app.register_error_handler(TitleSummaryViewExpired, title_summary_view_expired_handler)

    app.register_error_handler(ApplicationError, application_error)

    for exception in default_exceptions:
        app.register_error_handler(exception, error_handler)
    app.register_error_handler(Exception, error_handler)
