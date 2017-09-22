from flask_wtf import Form
from wtforms.fields import StringField, SubmitField, BooleanField, PasswordField, SelectField, HiddenField
from wtforms.validators import InputRequired, Required, Regexp, Email, Length, ValidationError, EqualTo
from service import app, validation_utils


class TitleSearchForm(Form):
    search_term = StringField('search_term',
                              [InputRequired(message='Postcode is required')])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)


class AccountCreationForm(Form):
    forbidden_password_chars = '£\u20AC\u00AC\u00A6'
    forbidden_email_chars = '+'

    encrypted_title_number = HiddenField('encrypted_title_number')
    search_term = HiddenField('search_term')

    email = StringField('Email address', validators=[
        InputRequired('Email address is required'),
        Email('The email address you have entered is not valid'),
        Regexp(r'^[^{}]+$'.format(forbidden_email_chars),
               message='Email address must not contain the {} character'.format(' '.join(forbidden_email_chars)))
    ])
    password = PasswordField('Create a password', validators=[
        InputRequired('Password is required'),
        Length(min=8, max=20, message='Password needs to be between %(min)d and %(max)d characters'),
        Regexp(r'^[^{}]+$'.format(forbidden_password_chars),
               message='Password must not contain the characters {}'.format(' '.join(forbidden_password_chars))),
        EqualTo('password_retype', message='Please ensure both password fields match'),
    ])
    password_retype = PasswordField('Re-type your password')
    firstname = StringField('First name', validators=[InputRequired('First name is required')])
    surname = StringField('Surname', validators=[InputRequired('Surname is required')])
    phone = StringField('Phone number (optional)')
    address1 = StringField('First line of your address', validators=[InputRequired('First line of your address is '
                                                                                   'required')])

    title = SelectField('Title', validators=[InputRequired('Title is required')], choices=[
        ('', 'Please select a title'), ('Mr', 'Mr'), ('Mrs', 'Mrs'), ('Ms', 'Ms'), ('Miss', 'Miss'), ('Other', 'Other')])
    city = StringField('Town or City', validators=[InputRequired('Town or City is required')])
    country = SelectField('Country', default='United Kingdom', validators=[InputRequired()],
                          choices=app.config['COUNTRIES'])
    postcode = StringField('Postcode')
    terms = BooleanField('I have read and agree to the <a href="/terms-of-use">terms of use</a>',
                         validators=[InputRequired(message='You must agree to our terms of use before continuing')])

    submit = SubmitField('Register')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate_password(self, field):
        if sum(c.isalpha() for c in field.data) < 1:
            raise ValidationError('Password needs at least 1 letter')
        elif sum(c.isdigit() for c in field.data) < 2:
            raise ValidationError('Password needs at least 2 numbers')

        if field.data.count(' ') > 0:
            raise ValidationError('Password must not contain spaces')

        if self.email.data == field.data:
            raise ValidationError('Password should not be the same as your email address')

    def validate_postcode(self, field):
        if self.country.data == 'United Kingdom':
            if field.data:
                if not validation_utils.is_valid_postcode(field.data):
                    raise ValidationError('Postcode is not a valid UK postcode')

            else:
                raise ValidationError('Postcode is required')


class ConfirmTermsConditionsForm(Form):
    right_to_cancel = BooleanField('I have read and agree to the <a href="/terms-of-use">terms of use</a>', validators=[Required(message='You must agree to the terms of use before continuing')])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)


class PasswordResetForm(Form):
    email = StringField('email', validators=[InputRequired(message='Email address is required')])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)


class ChangePasswordForm(Form):
    forbidden_password_chars = '£\u20AC\u00AC\u00A6'

    password = PasswordField('Create a password', validators=[
        InputRequired('Password is required'),
        Length(min=8, max=20, message='Password needs to be between %(min)d and %(max)d characters'),
        Regexp(r'^[^{}]+$'.format(forbidden_password_chars),
               message='Password must not contain the characters {}'.format(' '.join(forbidden_password_chars))),
        EqualTo('password_retype', message='Please ensure both password fields match'),
    ])
    password_retype = PasswordField('Re-type your password')

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
