import faulthandler
from flask import Flask, request, g
from flask.ext.babel import Babel

from config import CONFIG_DICT
from service import logging_config, error_handler, ui, template_filters, api_client, utils
from flask_wtf.csrf import CsrfProtect
from flask_limiter import Limiter
from service.data import countries
from service.title_number_utils import TitleNumberConverter
import logging.config

# This causes the traceback to be written to the fault log file in case of serious faults
fault_log_file = open(str(CONFIG_DICT['FAULT_LOG_FILE_PATH']), 'a')
faulthandler.enable(file=fault_log_file)

app = Flask(__name__, static_folder='ui')
app.config.update(CONFIG_DICT)


app.url_map.strict_slashes = False

babel = Babel(app)
csrf = CsrfProtect(app)

limiter = Limiter(app, key_func=utils.get_ip_address)

LOGGER = logging.getLogger(__name__)

LANGUAGES = {
    'cy': 'Cymraeg',
    'en': 'English'
}

# Load the countries
app.config.update({'COUNTRIES': countries.load_countries('service/data/country-records.json')})

# Register our title number converter which handles encryption and decryption of the url arguments
app.url_map.converters['encrypted_title_number'] = TitleNumberConverter

# app.config['BABEL_DEFAULT_LOCALE'] = 'en'


@babel.localeselector
def get_locale():
    return g.locale


@app.before_request
def before_request():

    if request.path.startswith('/ui/'):
        return

    # Set language options
    g.locale = request.args.get('language', 'en')
    g.current_lang = g.locale

    # Grab the price from digital-register-api if we don't already have it
    if not (app.config.get('TITLE_REGISTER_SUMMARY_PRICE') or app.config.get('TITLE_REGISTER_SUMMARY_PRICE_TEXT')):
        LOGGER.debug("Price not found - requesting from digital-register-api")

        price = api_client.get_pound_price()
        price_format = "&pound{} inc VAT"

        # If the price is a round number of pounds we don't want to display any decimal places
        if price.is_integer():
            price = "{0:.0f}".format(price)
        else:
            price = "{0:.2f}".format(price)

        price_text = price_format.format(price)

        app.config.update({'TITLE_REGISTER_SUMMARY_PRICE': price})
        app.config.update({'TITLE_REGISTER_SUMMARY_PRICE_TEXT': price_text})


ui.register_assets(app)

for (filter_name, filter_method) in template_filters.get_all_filters().items():
    app.jinja_env.filters[filter_name] = filter_method


def get_print_intent_event_label():

    # If we've got a matching endpoint, use it
    # Otherwise just use the URL
    if request.endpoint:
        event = request.endpoint
    else:
        event = request.path

    return event


@app.context_processor
def inject_global_config():
    return dict(
        google_api_key=app.config['GOOGLE_ANALYTICS_API_KEY'],
        ordnance_survey_terms_url=app.config['ORDNANCE_SURVEY_TERMS_URL'],
        govuk_feedback_url=app.config['GOVUK_FEEDBACK_URL'],
        govuk_start_url=app.config['GOVUK_START_URL'],
        junction=app.config['JUNCTION'],
        ccc_phone_number=app.config['CCC_PHONE_NUMBER'],
        title_summary_download=app.config['TITLE_SUMMARY_DOWNLOAD'],
        print_intent_event_label=get_print_intent_event_label(),
        username=utils.username_from_header(request)
    )


logging_config.setup_logging()
if app.config['DEBUG'] is False:
    # Retain traceback when DEBUG = True
    error_handler.setup_errors(app)
error_handler.setup_errors(app)
