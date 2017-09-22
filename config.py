import os
from datetime import timedelta


CONFIG_DICT = {
    'LOGGING_LEVEL': os.environ.get('LOGGING_LEVEL', "WARN"),
    'FAULT_LOG_FILE_PATH': os.environ['FAULT_LOG_FILE_PATH'],
    'GOOGLE_ANALYTICS_API_KEY': os.environ['GOOGLE_ANALYTICS_API_KEY'],
    'LOGGING': True,
    'LOGGING_CONFIG_FILE_PATH': os.environ['LOGGING_CONFIG_FILE_PATH'],
    'PERMANENT_SESSION_LIFETIME': timedelta(minutes=15),
    'REGISTER_TITLE_API': os.environ['REGISTER_TITLE_API'],
    'LAND_REGISTRY_PAYMENT_INTERFACE_URI': os.environ['LAND_REGISTRY_PAYMENT_INTERFACE_URI'],
    'LAND_REGISTRY_PAYMENT_INTERFACE_BASE_URI': os.environ['LAND_REGISTRY_PAYMENT_INTERFACE_BASE_URI'],
    'PUBLIC_ACCOUNT_SERVICES_API_URI': os.environ['PUBLIC_ACCOUNT_SERVICES_API_URI'],
    'PDF_API_URI': os.environ['PDF_API_URI'],
    'SECRET_KEY': os.environ['APPLICATION_SECRET_KEY'],
    'SERVICE_NOTICE_HTML': os.environ['SERVICE_NOTICE_HTML'],
    'SESSION_COOKIE_SECURE': os.environ['SESSION_COOKIE_SECURE'].lower() != 'false',
    'MORE_PROPRIETOR_DETAILS': os.environ['MORE_PROPRIETOR_DETAILS'],
    'ORDNANCE_SURVEY_TERMS_URL': os.environ['ORDNANCE_SURVEY_TERMS_URL'],
    'GOVUK_FEEDBACK_URL': os.environ['GOVUK_FEEDBACK_URL'],
    'GOVUK_START_URL': os.environ['GOVUK_START_URL'],
    'JUNCTION': os.environ['JUNCTION'],
    'CCC_PHONE_NUMBER': os.environ['CCC_PHONE_NUMBER'],

    # These values are set at run-time.
    'TITLE_REGISTER_SUMMARY_PRICE': None,
    'TITLE_REGISTER_SUMMARY_PRICE_TEXT': None,
    'COUNTRIES': None,

    # security settings
    'REQUESTORID': os.environ['REQUESTORID'],
    'ORG': os.environ['ORG'],
    'ORGUNIT': os.environ['ORGUNIT'],
    'LOCALITYNAME': os.environ['LOCALITYNAME'],
    'ROLES': os.environ['ROLES'],
    'CHECK_USERNAME_BASED_ACCOUNT_RATE_LIMIT': os.environ['CHECK_USERNAME_BASED_ACCOUNT_RATE_LIMIT'],
    'RATELIMIT_HEADERS_ENABLED': os.environ['RATELIMIT_HEADERS_ENABLED'].lower() == 'true',

    # feature flags
    'SHOW_FULL_TITLE_DATA': os.environ['SHOW_FULL_TITLE_DATA'].lower() == 'true',
    'SHOW_CREATE_ACCOUNT': os.environ['SHOW_CREATE_ACCOUNT'].lower() == 'true',
    'SHOW_SUMMARY_MAP': os.environ['SHOW_SUMMARY_MAP'].lower() == 'true',
    'TITLE_SUMMARY_DOWNLOAD': os.environ['TITLE_SUMMARY_DOWNLOAD'] == 'true',
}  # type: Dict[str, Union[bool, str, timedelta]]


settings = os.environ.get('SETTINGS')

if settings == 'dev':
    CONFIG_DICT['DEBUG'] = True
elif settings == 'test':
    # We do NOT set TESTING to True here as it turns off authentication, and we
    # want to make sure the app behaves the same when running tests locally
    # as it does in production.
    CONFIG_DICT['DEBUG'] = True
    CONFIG_DICT['DISABLE_CSRF_PREVENTION'] = True
    CONFIG_DICT['WTF_CSRF_ENABLED'] = False
    CONFIG_DICT['FAULT_LOG_FILE_PATH'] = '/dev/null'
    CONFIG_DICT['LOGGING'] = False
    CONFIG_DICT['RATELIMIT_ENABLED'] = False
