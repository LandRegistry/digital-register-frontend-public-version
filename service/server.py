import json
import logging.config
import re
import os
from flask import abort, Markup, redirect, render_template, request, Response, url_for, session, escape, flash, jsonify
from flask.ext.babel import gettext

import requests
import demjson

import config
from service import address_utils, api_client, app, auditing, health_checker, title_formatter, \
    title_utils, markdown_utils, encryption_utils, csrf, limiter, utils, template_filters
from service.forms import TitleSearchForm, ConfirmTermsConditionsForm, AccountCreationForm, PasswordResetForm, \
    ChangePasswordForm
from service.error_handler import TitleSummaryViewExpired
from datetime import datetime
import dateutil
import pytz

# TODO(Your Name): move this to the template
UNAUTHORISED_WORDING = Markup('If this problem persists please contact us at '
                              '<a rel="external" href="mailto:digital-register-'
                              'feedback@digital.landregistry.gov.uk">'
                              'digital-register-feedback@digital.landregistry.gov.uk</a>.')
# TODO(Your Name): move this to the template
POSTCODE_REGEX = re.compile(address_utils.BASIC_POSTCODE_REGEX)
LOGGER = logging.getLogger(__name__)


if config.CONFIG_DICT['SHOW_CREATE_ACCOUNT']:
    @app.route('/register', defaults={'title_number': None, 'search_term': None}, methods=['GET'])
    @app.route('/register/<encrypted_title_number:title_number>/<search_term>', methods=['GET'])
    def create_account(title_number, search_term):
        # If the user is logged in, don't let them view the page
        if utils.username_from_header(request):
            return redirect(url_for('search'))

        if title_number:
            encrypted_title_number = encryption_utils.encrypt(title_number)
            form = AccountCreationForm(request.form, encrypted_title_number=encrypted_title_number, search_term=search_term)
        else:
            form = AccountCreationForm(request.form)

        return render_template('account/create.html', form=form)

    @app.route('/register', methods=['POST'])
    def submit_create_account():
        # If the user is logged in, don't let them view the page
        if utils.username_from_header(request):
            return redirect(url_for('search'))

        form = AccountCreationForm()

        if form.validate():
            response = api_client.create_account(form.data)
            if response.status_code == 200 and response.json()['status'] == 'success':

                # Redirect onto the success page rather than rendering success here
                # This prevents people refreshing the account creation page and getting warnings
                if form.encrypted_title_number.data:
                    return redirect(url_for('registration_successful',
                                            title_number=encryption_utils.decrypt(form.encrypted_title_number.data),
                                            search_term=form.search_term.data))
                else:
                    return redirect(url_for('registration_successful'))

            elif response.status_code == 429:
                message = """<p>You have selected to register too many times. Please wait 1 minute before trying again</p>"""

                flash(Markup(message))

                return render_template('account/create.html', form=form)

            else:

                error_details = response.json()

                if form.encrypted_title_number.data:
                    sign_in_url = url_for('sign_in', title_number=form.encrypted_title_number.data, search_term=form.search_term.data)
                else:
                    sign_in_url = url_for('sign_in')

                # Trap the existing Find a Property account errors early and
                # flash a message instead of letting it fall through to the form validation errors
                if error_details['data']['errorCode'] == 'FPE':

                    # If we have an existing user ID in the returned payload, build a data
                    # attribute to supply the value to the JavaScript
                    existing_user_id_data_attribute = ''
                    if error_details['data'].get('existingUserId'):
                        existing_user_id_data_attribute = ' data-existing-fap-email="{}"'.format(escape(form.email.data))

                    message = """<p>The email address you have supplied is associated with the username <strong class="bold">{2}</strong> from our "Find a Property" service</p>
                                <a class="button" href="{0}"{1}>Sign in with this account</a>""".format(url_for('search'),
                                                                                                        existing_user_id_data_attribute,
                                                                                                        escape(error_details['data'].get('existingUserId')))

                    flash(Markup(message))

                    return render_template('account/create.html', form=form)

                elif error_details['data']['errorCode'] == 'archived user':
                    message = _archived_user_message()

                    flash(Markup(message))
                    LOGGER.debug("ENDED: change_password with unsuccessful password change".format(response.json))
                    return render_template(
                        'account/create.html', form=form)

                else:
                    return render_template('account/create.html',
                                           form=form,
                                           processerrors=_sanitise_error_message(
                                               error_details,
                                               'create the account',
                                               sign_in_url=sign_in_url
                                           ))
        else:
            return render_template('account/create.html', form=form)

    @app.route('/registration-successful', methods=['GET'], defaults={'title_number': None, 'search_term': None})
    @app.route('/registration-successful/<encrypted_title_number:title_number>/<search_term>', methods=['GET'])
    def registration_successful(title_number, search_term):
        ip_address = utils.get_ip_address()
        auditing.audit(
            "ACCOUNT CREATED: IP Address {0} ".format(
                ip_address))

        # If we've been redirected here from the account creation form, render the success message
        if request.referrer and url_for('create_account') in request.referrer:
            if title_number and search_term:
                return render_template('account/registration_successful.html', title_number=encryption_utils.encrypt(title_number), search_term=search_term)
            else:
                return render_template('account/registration_successful.html')

        # Otherwise the user has managed to arrive here "directly" such as via entering the url manually
        # In this situation we redirect them on to the search page
        return redirect(url_for('search'))

    # This route has to be exempt from CSRF since it is being called from WebSeal
    # which cannot have knowledge of CSRF tokens generated by this app
    @csrf.exempt
    @limiter.limit(config.CONFIG_DICT['CHECK_USERNAME_BASED_ACCOUNT_RATE_LIMIT'])
    @app.route('/get-account-details', methods=['POST'])
    def get_account_details():
        ip_address = utils.get_ip_address()

        LOGGER.debug("STARTED: get-account-details email -: {0} from IP: {1}".format(
            request.form.get('email'), ip_address)
        )

        # Pass request straight through to public-account-services-api
        status = 200
        try:
            data = api_client.get_account_details(request.form['email'])
        except requests.exceptions.HTTPError as e:
            LOGGER.debug("get-account-details email not found -: {0}".format(
                request.form.get('email'))
            )

            data = {}
            status = e.response.status_code

        LOGGER.debug("ENDED: get-account-details")
        return jsonify(data), status


# If user is already logged out but the button is there, it redirects to our own signout page
@app.route('/pkmslogout', methods=['GET'])
def pkmslogout():
    return render_template('signout.html')


@limiter.limit(config.CONFIG_DICT['CHECK_USERNAME_BASED_ACCOUNT_RATE_LIMIT'])
@app.route('/request-reset-password-email', methods=['GET', 'POST'])
def request_reset_password_email():
    LOGGER.debug("STARTED: request_reset_password_email")

    form = PasswordResetForm()

    if form.validate_on_submit():
        response = api_client.request_reset_password(form.data)

        if response.status_code == 200 and response.json()['status'] == 'success':
            LOGGER.debug("ENDED: request_reset_password_email success: email sent")
            return render_template('account/reset_password_email_sent.html', email=form.email.data)

        elif response.status_code == 422 and response.json()['data']['errorCode'] == 'archived user':
            message = _archived_user_message(link_to_create_account=True)

            flash(Markup(message))
            LOGGER.debug("ENDED: request_reset_password_email error: archived user")
            return reset_password_page(heading="Reset password", message="Enter your email address - we'll send you a link")

        elif response.status_code == 422 and response.json()['data']['errorCode'] == 'unknown user':
            message = """<p>This account doesn't exist, would you like to
                      <a href="{}">create an account</a></p>""".format(
                      url_for('create_account'))

            flash(Markup(message))
            LOGGER.debug("ENDED: request_reset_password_email error: unknown user")
            return reset_password_page(heading="Reset password", message="Enter your email address - we'll send you a link")
        else:
            LOGGER.debug("ENDED: request_reset_password_email error occurred")
            return reset_password_page(heading="Reset password",
                                       message="Enter your email address - we'll send you a link", processerrors=_sanitise_error_message(response.json(),
                                                                                                                                         'reset your password'))

    else:
        LOGGER.debug("ENDED: request_reset_password_email reset password page displayed")
        return reset_password_page(heading="Reset password", message="Enter your email address - we'll send you a link")


@app.route('/change-password/<token>', methods=['GET'])
def view_change_password(token):
    form = ChangePasswordForm()

    LOGGER.debug("STARTED: GET change_password")

    response = api_client.validate_password_reset_token(token)

    if response and hasattr(response, 'json'):

        if response.json().get('status') is not True:
            LOGGER.debug("ENDED: change_password error - invalid token")
            return reset_password_page(
                heading="Sorry that link isn't valid",
                message="Enter your email address - we'll send you a new link")
        else:
            LOGGER.debug("ENDED: change_password with valid token")
            return render_template('account/change_password.html', form=form, token=token)

    else:
        return reset_password_page(
            heading="Sorry that link isn't valid",
            message="Enter your email address - we'll send you a new link")


@app.route('/change-password/<token>', methods=['POST'])
def submit_change_password(token):
    form = ChangePasswordForm()
    if form.validate():
        # submit form with valid token, is validated and submitted and will say whether password
        # succesfully changed
        LOGGER.debug("STARTED: POST change_password")
        response = api_client.change_password(token, form.data)
        if hasattr(response, 'json'):
            if response.json()['status'] == 'success':
                LOGGER.debug("ENDED: change_password with successful password change")

                # The password change has happened successfully so shown the succesful page
                return render_template('account/change_password_successful.html')

            else:
                if response.json()['data']['errorCode'] == 'archived user':
                    message = _archived_user_message(link_to_create_account=True)

                    flash(Markup(message))
                    LOGGER.debug("ENDED: change_password with unsuccessful password change: {}".format(response.json()))
                    return render_template(
                        'account/change_password.html', form=form, token=token)
                else:
                    LOGGER.debug("ENDED: change_password with unsuccessful password change".format(response.json))
                    return render_template(
                        'account/change_password.html', form=form, token=token,
                        processerrors=_sanitise_error_message(response.json(), 'reset your password'))

        return reset_password_page(
            heading="Sorry that link isn't valid",
            message="Enter your email address - we'll send you a new link")


def reset_password_page(heading, message, processerrors=None):
    form = PasswordResetForm()
    return render_template('account/request_reset_password_email.html', form=form, heading=heading, message=message, processerrors=processerrors)


@app.route('/start', methods=['GET'])
def govuk_start_page():
    return redirect(config.CONFIG_DICT['GOVUK_START_URL'])


@app.route('/', methods=['GET'])
def initial_route():
    return redirect(url_for('search'))


@app.route('/search', methods=['GET'])
def search():
    LOGGER.debug("STARTED: Search")
    LOGGER.debug("ENDED: Search")
    return render_template(
        'search.html',
        form=TitleSearchForm(),
        price=app.config['TITLE_REGISTER_SUMMARY_PRICE'],
        price_text=app.config['TITLE_REGISTER_SUMMARY_PRICE_TEXT']
    )


@app.route('/about-this-property/<encrypted_title_number:title_number>/<search_term>', methods=['GET'])
def about_this_property(title_number, search_term):
    LOGGER.debug("STARTED: about_this_property title_number: {}, search_term: {}".format(
        title_number, search_term
    ))

    title = _get_register_title(title_number)
    if not title:
        abort(404)

    display_page_number = int(request.args.get('page') or 1)
    price_text = app.config['TITLE_REGISTER_SUMMARY_PRICE_TEXT']
    username = utils.username_from_header(request)

    form = ConfirmTermsConditionsForm()

    _audit_title_viewed(title_number, username)

    params = _worldpay_form(search_term, title_number, title['last_changed'], username)

    LOGGER.debug('Saving user\'s search request')
    response = api_client.save_search_request(params)

    params['cartId'] = response['cart_id']
    params['MC_timestamp'] = response['search_datetime']

    # The params aren't carried over from a GET to a POST so save in sessions using titlenumber as the key
    encrypted_title_number = encryption_utils.encrypt(title_number)
    session[encrypted_title_number] = params

    template_arguments = {
        'page_title': 'About this property',
        'title': title,
        'title_number': title_number,
        'encrypted_title_number': encrypted_title_number,
        'price_text': price_text,
        'form': form if username else False,
        'search_term': search_term,
        'display_page_number': display_page_number,
        'username': username,
        'enable_help_block': False,
        'confirm': False
    }

    LOGGER.debug("ENDED: about_this_property")
    return render_template('about_property.html', **template_arguments)


@app.route('/sign-in', methods=['GET'])
def sign_in():
    """This route is the first one to be protected by webseal

    Visiting it when not signed in will trigger the login form to kick in.
    Once you've logged in, you then get redirected onto the appropriate place.

    Note:
    The title number and search term parameters are in the query string instead of
    URL parameters because the sign in page needs to be able to inject these into
    the /register links. Since we cannot write backend code on the webseal server
    we have to do this with JavaScript. The happy path would work with URL parameters,
    but if the user gets their password wrong, it modifies the URL to be the following:

    /pkmslogin.form

    At this point, Webseal has remembered the URL that we were viewing, but it has
    hidden the title number and search term from my JavaScript, which makes it
    impossible to rewrite the /register links.

    By putting it in the query string parameters, we can use JavaScript to forcibly
    put them onto the form action like

    /pkmslogin.form?title_number=asd&search_term=foo
    """

    LOGGER.debug("STARTED: sign_in")
    encrypted_title_number = request.args.get('title_number')
    search_term = request.args.get('search_term')

    if encrypted_title_number and search_term:
        title_number = encryption_utils.decrypt(encrypted_title_number)

        LOGGER.debug("sign_in title_number: {0}".format(
            title_number
        ))

        LOGGER.debug("ENDED: sign_in")
        return redirect(url_for('confirm_your_purchase', title_number=title_number, search_term=search_term))
    else:
        return redirect(url_for('search'))


@app.route('/confirm-your-purchase/<encrypted_title_number:title_number>/<search_term>', methods=['GET', 'POST'])
def confirm_your_purchase(title_number, search_term):
    LOGGER.debug("STARTED: confirm_your_purchase title_number: {0}".format(
        title_number
    ))

    title = _get_register_title(title_number)
    if not title:
        abort(404)

    encrypted_title_number = encryption_utils.encrypt(title_number)

    form = ConfirmTermsConditionsForm()
    username = utils.username_from_header(request)
    display_page_number = int(request.args.get('page') or 1)
    price_text = app.config['TITLE_REGISTER_SUMMARY_PRICE_TEXT']

    try:
        params = session[encrypted_title_number]
    except KeyError:
        return redirect(url_for('about_this_property', title_number=title_number, search_term=search_term))

    if form.validate_on_submit():
        LOGGER.debug("ENDED: confirm_your_purchase")
        return _payment(price_text, username, title_number, params)

    else:
        api_client.update_search_request(username, params['MC_timestamp'], params['title_number'])

        template_arguments = {
            'page_title': 'Confirm your purchase',
            'title': title,
            'title_number': title_number,
            'price_text': price_text,
            'form': form,
            'search_term': search_term,
            'display_page_number': display_page_number,
            'enable_help_block': False,
            'confirm': True
        }
        LOGGER.debug("ENDED: confirm_your_purchase")
        return render_template('about_property.html', **template_arguments)


def _audit_title_viewed(title_number, username):
    # This puts something in our audit logs of what a user/ip address viewed at what time
    ip_address = utils.get_ip_address()
    date_and_time_viewed = datetime.now()
    auditing.audit("VIEWED TITLE ON CONFIRM PAGE: Title number {0} was viewed by {3} on ip address {1} viewed on {2}".format(
        title_number, ip_address, date_and_time_viewed, username))


def _payment(price_text, username, title_number, params):
    LOGGER.debug("STARTED: _payment price_text: {0}".format(price_text))

    lrpi_url = app.config['LAND_REGISTRY_PAYMENT_INTERFACE_URI']

    LOGGER.debug("_payment: Form validation and user logged in {0}".format(username))

    params['MC_userId'] = username

    worldpay_data = requests.post(lrpi_url, data=params)

    if worldpay_data.headers['pay_mode'] == 'worldpay':
        worldpay_json = json.loads(worldpay_data.text)
        LOGGER.debug("ENDED: _payment")

        return render_template('hiddenWP.html', worldpay_params=worldpay_json)
    else:
        redirect_url = worldpay_data.text
        LOGGER.debug("ENDED: _payment")

        return redirect(redirect_url)


@app.route('/health', methods=['GET'])
def healthcheck():
    LOGGER.debug("STARTED: healthcheck")
    errors = health_checker.perform_healthchecks()
    status, http_status = ('error', 500) if errors else ('ok', 200)

    response_body = {'status': status}

    if errors:
        response_body['errors'] = errors
    LOGGER.debug("ENDED: healthcheck")
    return Response(
        json.dumps(response_body),
        status=http_status,
        mimetype='application/json',
    )


@app.route('/cookies', methods=['GET'])
def cookies():
    return _cookies_page()


@app.route('/terms-of-use', methods=['GET'])
def terms_of_use():
    terms = open('service/data/terms-of-use.md')
    return _generic_page(content=markdown_utils.render(terms.read()), title="Find property information: terms of use", back_link=True)


@app.route('/titles/<encrypted_title_number>', methods=['GET'])
def title_summary(encrypted_title_number):
    # On return from LRPI, the title number is unencrypted
    # In order to mask it from google analytics, we need to encrypt it and redirect the user on
    if len(encrypted_title_number) < 10:
        return redirect(url_for('title_summary',
                                encrypted_title_number=encryption_utils.encrypt(encrypted_title_number),
                                **request.args))

    """Show title (result) if user is logged in, has paid and hasn't viewed before."""
    title_number = encryption_utils.decrypt(encrypted_title_number)
    LOGGER.debug("STARTED: title_summary title_number: {0}".format(title_number))

    username = utils.username_from_header(request)
    trans_id = request.args.get('transid')
    search_term = request.args.get('search_term', title_number)

    params = _get_title_data(trans_id, username, title_number)

    auditing.audit("VIEW REGISTER: Title number {0} was viewed by {1}".format(
                   title_number,
                   username))

    LOGGER.debug("ENDED: title_summary")

    return render_template('display_title.html',
                           search_term=search_term,
                           encrypted_title_number=encrypted_title_number,
                           show_summary_map=app.config['SHOW_SUMMARY_MAP'],
                           **params)


if app.config['TITLE_SUMMARY_DOWNLOAD']:
    @app.route('/titles/<title_number>.pdf', methods=['GET'])
    def display_summary_pdf(title_number):
        LOGGER.debug("STARTED: display_summary_pdf title_number: {}".format(title_number))

        username = utils.username_from_header(request)
        trans_id = request.args.get('transid')

        LOGGER.debug("ENDED: display_summary_pdf")

        return api_client.get_title_summary_pdf(**_get_title_data(trans_id, username, title_number))


def _get_title_data(trans_id, username, title_number):
    LOGGER.debug("STARTED: _get_title_data title_number: {}".format(title_number))

    title = _get_register_title(title_number)

    if title:
        if _user_can_view(username, title_number):

            is_caution_title = title_utils.is_caution_title(title)

            if app.config['SHOW_FULL_TITLE_DATA']:
                full_title_data = _strip_delimiters(api_client.get_official_copy_data(title_number))
            else:
                full_title_data = None

            if is_caution_title:
                title['summary_heading'] = gettext("Summary of caution title")
            else:
                title['summary_heading'] = gettext("Summary of title")

            if is_caution_title:
                title['proprietor_type_heading'] = gettext("Cautioner")
            elif title['tenure'].upper() == "LEASEHOLD":
                title['proprietor_type_heading'] = gettext("Leaseholder")
            else:
                title['proprietor_type_heading'] = gettext("Owner")

            if len(title['proprietors']) > 1:
                title['proprietor_type_heading'] += "s"

            title['last_changed_readable'] = "This title was last changed on {} at {}".format(
                template_filters.format_date(title['last_changed']),
                template_filters.format_time(title['last_changed'])
            )

            receipt = _create_receipt(trans_id, title_number)

            LOGGER.debug("ENDED: _get_title_data")

            return {
                'title': title,
                'is_caution_title': is_caution_title,
                'receipt': receipt,
                'full_title_data': full_title_data
            }

        else:
            raise TitleSummaryViewExpired

    else:
        LOGGER.debug("ENDED: _get_title_data")
        abort(404)


def _create_receipt(trans_id, title_number):
    vat_json = {"date": 'N/A',
                "address1": 'N/A',
                "address2": 'N/A',
                "address3": 'N/A',
                "address4": 'N/A',
                "postcode": 'N/A',
                "title_number": 'N/A',
                "net_amt": 0,
                "vat_amt": 0,
                "fee_amt": 0,
                "vat_num": 'N/A'}

    if trans_id:
        receipt_data = api_client.get_invoice_data(trans_id)
        receipt_text = demjson.decode(receipt_data.text)
        vat_json = demjson.decode(receipt_text['vat_json'])

        vat_json['date'] = dateutil.parser.parse(vat_json['date']).astimezone(pytz.timezone('Europe/London')).strftime('%d %B %Y at %H:%M:%S')

    receipt = {"trans_id": trans_id,
               "date": vat_json['date'],
               "address1": vat_json['address1'],
               "address2": vat_json['address2'],
               "address3": vat_json['address3'],
               "address4": vat_json['address4'],
               "postcode": vat_json['postcode'],
               "title_number": title_number,
               "net": "{0:.2f}".format(vat_json['net_amt']),
               "vat": "{0:.2f}".format(vat_json['vat_amt']),
               "total": "{0:.2f}".format(vat_json['fee_amt']),
               "reg_number": vat_json['vat_num']}

    return receipt


@app.route('/title-search', methods=['POST'])
@app.route('/title-search/<search_term>', methods=['POST'])
def find_titles():
    LOGGER.debug("STARTED: find_titles")
    display_page_number = int(request.args.get('page') or 1)
    search_term = request.form['search_term'].strip()
    form = TitleSearchForm()

    if search_term and form.validate():
        LOGGER.debug("ENDED: find_titles search_term: {0}".format(search_term))

        return redirect(url_for('find_titles', search_term=search_term, page=display_page_number))
    else:
        # TODO(Your Name): we should redirect to that page
        LOGGER.debug("ENDED: find_titles")

        return _initial_search_page(request)


@app.route('/title-search', methods=['GET'])
@app.route('/title-search/<search_term>', methods=['GET'])
def find_titles_page(search_term=''):
    LOGGER.debug("STARTED: find_titles_page search_term: {}".format(search_term))

    display_page_number = int(request.args.get('page') or 1)
    page_number = display_page_number - 1  # page_number is 0 indexed
    username = utils.username_from_header(request)
    search_term = search_term.strip()

    if not search_term:
        LOGGER.debug("ENDED: find_titles_page")

        return _initial_search_page(request)
    else:
        message_format = "SEARCH REGISTER: '{0}' was searched by {1}"
        auditing.audit(message_format.format(search_term, username))
        LOGGER.debug("ENDED: find_titles_page search_term: {0}".format(search_term))

        return _get_address_search_response(search_term, page_number)


@app.route('/service-error', methods=['GET'])
def payment_error():
    LOGGER.debug("STARTED: payment_error page")

    return render_template('payment-error.html', title='Service error')


def _worldpay_form(search_term, title_number, last_changed, username):
    LOGGER.debug("STARTED: _worldpay_form search_term, title_number, username: {0}, {1}, {2}".format(
        search_term, title_number, username
    ))

    params = {
        'search_term': search_term,
        'title_number': title_number,
        'MC_titleNumber': title_number,
        # should one of: A, D, M, T, I
        'MC_searchType': 'D',
        'MC_purchaseType': os.getenv('WP_MC_PURCHASETYPE', 'drvSummaryView'),
        'MC_unitCount': '1',
        'desc': search_term,
        'amount': app.config['TITLE_REGISTER_SUMMARY_PRICE'],
        'MC_userId': username
    }

    # Last changed date - modified to remove colon in UTC offset, which python
    # datetime.strptime() doesn't like >>>
    datestring = last_changed
    if len(datestring) == 25:
        if datestring[22] == ':':
            l = list(datestring)
            del (l[22])
            datestring = "".join(l)

    dt_obj = datetime.strptime(datestring, "%Y-%m-%dT%H:%M:%S%z")

    params['last_changed_datestring'] = \
        "%d %s %d" % (dt_obj.day, dt_obj.strftime("%B"), dt_obj.year)
    params['last_changed_timestring'] = \
        "%s:%s:%s" % ('{:02d}'.format(dt_obj.hour),
                      '{:02d}'.format(dt_obj.minute),
                      '{:02d}'.format(dt_obj.second))

    LOGGER.debug("ENDED: _worldpay_form")

    return params


def _initial_search_page(request):
    price = app.config['TITLE_REGISTER_SUMMARY_PRICE']
    price_text = app.config['TITLE_REGISTER_SUMMARY_PRICE_TEXT']
    form = TitleSearchForm()
    search_term = ''

    if request.method == 'POST':
        form.validate()
        search_term = request.form['search_term'].strip()

    return render_template(
        'search.html',
        form=form,
        price=price,
        price_text=price_text,
        search_term=search_term
    )


def _get_register_title(title_number):
    LOGGER.debug("STARTED: _get_register_title title_number{}".format(title_number))
    title = api_client.get_title(title_number)
    LOGGER.debug("_get_register_title: {0}".format(title))
    LOGGER.debug("ENDED: _get_register_title")
    return title_formatter.format_display_json(title) if title else None


def _user_can_view(username, title_number):
    LOGGER.debug("STARTED: _user_can_view username, title_number: {0}, {1}".format(
        username, title_number
    ))
    access_granted = api_client.user_can_view(username, title_number)
    LOGGER.debug("_user_can_view: {0}".format(access_granted))
    LOGGER.debug("ENDED: _user_can_view")
    return access_granted


def _get_address_search_response(search_term, page_number):
    LOGGER.debug("STARTED: _get_address_search_response search_term, page_number: {0}, {1}".format(
        search_term, page_number
    ))
    search_term = search_term.upper()
    if _is_postcode(search_term):
        LOGGER.info('postcode search used')
        LOGGER.debug("ENDED: _get_address_search_response")
        return _get_search_by_postcode_response(search_term, page_number)
    else:
        LOGGER.info('address search used')
        LOGGER.debug("ENDED: _get_address_search_response")
        return _get_search_by_address_response(search_term, page_number)


def _get_search_by_postcode_response(search_term, page_number):
    LOGGER.debug("STARTED: _get_search_by_postcode_response search_term, page_number: {0}, {1}".format(
        search_term, page_number
    ))
    postcode = _normalise_postcode(search_term)
    postcode_search_results = api_client.get_titles_by_postcode(postcode, page_number)
    LOGGER.debug("_get_search_by_postcode_response: {0}".format(postcode_search_results))
    LOGGER.debug("ENDED: _get_search_by_postcode_response")
    return _search_results_page(postcode_search_results, postcode, True)


def _get_search_by_address_response(search_term, page_number):
    LOGGER.debug("STARTED: _get_search_by_address_response search_term, page_number: {0}, {1}".format(
        search_term, page_number
    ))
    address_search_results = api_client.get_titles_by_address(search_term, page_number)
    LOGGER.debug("_get_search_by_address_response: {0}".format(address_search_results))
    LOGGER.debug("ENDED: _get_search_by_address_response")
    return _search_results_page(address_search_results, search_term)


def _is_postcode(search_term):
    return POSTCODE_REGEX.match(search_term)


def _normalise_postcode(postcode_in):
    # We strip out the spaces - and reintroduce one four characters from end
    no_spaces = postcode_in.replace(' ', '')
    postcode = no_spaces[:len(no_spaces) - 3] + ' ' + no_spaces[-3:]
    return postcode


def _search_results_page(results, search_term, addressbase=False):
    return render_template(
        'search_results.html',
        search_term=search_term,
        results=results,
        form=TitleSearchForm(),
        addressbase=addressbase
    )


def _cookies_page():
    return render_template('cookies.html')


def _generic_page(**kwargs):
    return render_template('generic_page.html', **kwargs)


def _strip_delimiters(json_in):
    # Remove all delimiters and not notes from json
    LOGGER.debug("STARTED: _strip_delimiters")
    json_out = json_in
    try:
        for i, sub_register in enumerate(json_in['official_copy_data']['sub_registers']):
            for j, entry in enumerate(sub_register['entries']):
                '''
                Unicode characters:
                35 - Hash #
                37 - Percentage %
                42 - Asterix *
                60 - Less than <
                61 - Equals =
                62 - Greater than >
                172 - Not note ¬
                '''
                delimiter_array = [35, 37, 42, 60, 61, 62, 172]
                txt = json_in['official_copy_data']['sub_registers'][i]['entries'][j]['full_text']
                for delimiter in delimiter_array:
                    txt = txt.replace(chr(delimiter), "")
                    json_out['official_copy_data']['sub_registers'][i]['entries'][j]['full_text'] = txt
    except Exception:
        # For when SHOW_FULL_TITLE_DATA = False
        pass
    LOGGER.debug("ENDED: _strip_delimiters")
    return json_out


def _sanitise_error_message(error_details, action='perform the requested action', sign_in_url=False):
    """Sanitises webseal error messages

    :param error_details: json version of the webseal error
    :param action: string representing the action which the user was performing at the time
    :return: a user readable version of the error
    """
    LOGGER.debug('START: _sanitise_error_message')
    # Display this message if error code is unknown or not found.
    default_error_message = ''.join((
        'Unable to {}. Please try again. ',
        'If you continue to have problems, you can '
        '<a href="https://www.gov.uk/government/organisations/land-registry/about/access-and-opening">contact HM Land Registry</a>.'))

    if not sign_in_url:
        sign_in_url = url_for('sign_in')

    in_use_message = 'This email address is already in use. Would you like to <a href="{}">sign in</a> or '\
                     '<a href="{}">create a new password</a>?'.format(sign_in_url, url_for('request_reset_password_email'))

    try:
        LOGGER.debug(error_details)
        error_code = error_details['data']['errorCode']

        error_message = {
            'u020': in_use_message,
            'u062': "The password cannot be set to a password previously used",
            'u063': "The password isn't long enough. Needs to be at least 8 characters.",
            'u073': 'The password is too long. Keep it within 20 characters.',
            'u066': 'The password needs at least 2 alpha characters.',
            'u089': 'The password needs at least 2 numbers in it.',
            'u078': "Password should not be the same as your email address",
            'DBF': default_error_message.format('create the account'),
            'CEAF': default_error_message.format('create the account'),
            'CEPF': default_error_message.format('create the account'),
            'AEAF': default_error_message.format('activate the account'),
            'EAC': in_use_message,
            'ARPF': default_error_message.format('reset your password'),
            'token generation failure': default_error_message.format('reset your password'),
            '999': 'Some items are not quite right: {}'.format(error_details['data']['errorMessage']),
        }.get(error_code, default_error_message.format(action))
    except KeyError:
        # we've no idea what's come back so just log whole error and pass back generic message.
        LOGGER.error('_sanitise_error_message failed with a key error for error_details - {}'.format(error_details))
        error_message = default_error_message.format(action)
    return [error_message]


def _archived_user_message(link_to_create_account=False):
    message = """<h2 class="heading-small spacing-bottom-flush">Email already in use</h2>
                 <p class="spacing-top-flush">The email address was used for the Find a Property service.
                 Your registration details for the service have been deleted because you haven’t used it for over 12 months. Either:</p>
                 <ul class="list list-bullet">
                   <li><a href="{0}">Search in Find a Property</a> and re-register with a different username, or</li>
                   <li>Use a different email address to {1}create an account{2}.</li>
                 </ul>""".format(
              'https://eservices.landregistry.gov.uk/www/wps/portal/Property_Search',
              '<a href="{}">'.format(url_for('create_account')) if link_to_create_account else '',
              '</a>' if link_to_create_account else '')

    return message
