# digital-register-frontend

This is the repo for the frontend of the digital register service. It is written in Python, with the Flask framework.

## Setup

To create a virtual env, run the following from a shell:

```
    mkvirtualenv -p /usr/bin/python3 digital-register-frontend
    source environment.sh
    pip install -r requirements.txt
```

## How to run the tests

To run the tests for the Digital Register, go to its folder and run `lr-run-tests`.

## Run the acceptance tests

To run the acceptance tests for the Digital Register, go to the `acceptance-tests` folder and run:
```
   ./run-tests.sh
```

You will need to have a Postgres database running (see `db/lr-start-db` and `db/insert-fake-data` scripts in the [centos-dev-env](https://github.com/LandRegistry/centos-dev-env) project), as well as the digital-register-frontend and digital-register-api applications running on your development VM.

## Run the server

### Run in dev mode

To run the server in dev mode, execute the following command:

    ./run_flask_dev.sh

### Run using gunicorn

To run the server using gunicorn, activate your virtual environment, add the application directory to python path
(e.g. `export PYTHONPATH=/vagrant/apps/digital-register-frontend/:$PYTHONPATH`) and execute the following commands:

    pip install gunicorn
    gunicorn -p /tmp/gunicorn-digital-register-frontend.pid service.server:app -c gunicorn_settings.py

## Frontend assets
The frontend assets are supplied by [LandRegistry/land-registry-elements](https://github.com/LandRegistry/land-registry-elements).
To rebuild these, this repository contains a script called `build_assets.js`. This can be run as follows:
* `npm install` followed by `npm run build` from the `digital-register-frontend` application directory. This should be done from the host machine and not the vagrant box. Requires Nodejs 6 to be installed (Highly recommend using [https://github.com/creationix/nvm](https://github.com/creationix/nvm) and doing `nvm install 6`).

If you want to work on `land-registry-elements` in it's own right, you should check out the `land-registry-elements` repository to another location and using [npm link](https://docs.npmjs.com/cli/link) to symlink it into digital-registry-frontend.

Due to time constraints, the resulting build artefacts have been committed into the `digital-register-frontend` repository in the `service/static/.land-registry-elements` folder (Which on many OSs should be hidden). Therefore once you have rebuilt the assets based on changes upstream in the `land-registry-elements` repository, you need to then commit the changes to `digital-register-frontend`. Ideally this constraint will be removed in future by improvements to the build pipeline.

Note: *DO NOT EDIT THE BUILD ARTEFACTS MANUALLY!*. Changes to these should only come via the pattern library build scripts.

### Application specific CSS
Sometimes, if you just need to do something quickly or work on a component that is not appropriate to push up to the pattern library it may be necessary to add local CSS. This can be done in `service/static/app/stylesheets/application.scss`. This can be used to override small things from the pattern library or as a scratch pad for things that should be pushed to the pattern library when they are more fully formed.

## Dependencies

The GDSTransportWebsite fonts should also be installed (although you can generate the PDFs without them - they just wont look as nice). Copy GDSTransportWebsite.ttf and GDSTransportWebsite-Bold.ttf to /usr/share/fonts/GDSTransportWebsite/

## Third Party Tools

<a href="http://www.browserstack.com"><img src="https://www.browserstack.com/images/layout/browserstack-logo-600x315.png" alt="browserstack logo" width=300/></a>

<p>This repo is being tested using browserstack</p>
<p><i>Rapid Selenium webdriver testing with 100% reliability</i></p>

## Welsh language support

This has been implemented with Flask-Babel.

### Dependency

There is a single dependency: the Flask-Babel package. It should be specified in `requirements.sh`;

    Flask-Babel==0.9

### Setup

Include the following lines in the application `__init__.py`;

```python
from flask.ext.babel import Babel
.
.
babel = Babel(app)
.
.
@babel.localeselector
def get_locale():
    return g.locale
.
@app.before_request
def before_request():
    g.locale = request.args.get('language','en')
    g.current_lang = g.locale
```

The language code ('en' or 'cy') is maintained in the Flask global `g`. By default it is initialised to 'en' (English). The `localeselector` decorator function returns the value of `g`.

On the client side, the value is set in `display_title.html`. At the top of the template is a form with no action; when the submit button is pressed, the form will resubmit the page. The language value is set through the `name` GET parameter, which is added to the url when the page is resubmitted. Flask will detect the language code through the `before_request` decorator function and set the value of `g.locale`.

Now create a file in the root application folder and call it `babel.cfg`. Add the following lines to this file;

    python: **.py]
    [jinja2: **/templates/**.html]
    extensions=jinja2.ext.autoescape,jinja2.ext.with_

### Translations

There is a good tutorial available [here](http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xiv-i18n-and-l10n)

The following summarises the steps required to create and update the translations.

NB: Babel does not translate anything; that has to be done by a human (preferably one that is a native speaker).

#### Mark the text

Text must first be tagged (or marked) for translation. The text would normally be in a Jinja template, but it doesn't have to be (it can be anywhere in the application).

Text should be marked with a combination of Jinja and Babel tags. For example, an entry such as this;

    <h1>Heading</h1>

would be converted to;

    <h1>{{ _('Heading') }}</h1>

#### Extract the text

    NB: for all the next steps, you will need to open a terminal window and navigate
    to the root application folder (ie, digital-register-frontend/)

The next step is to extract all text that has been marked, as above.

    pybabel extract -F babel.cfg -o messages.pot .

This step creates the `messages.pot` file, which contains a list of all texts that require translation. Do not edit this file. It is temporary and can be deleted when all the steps are complete.

#### Generate the language dictionary

This next step creates the folder structure that will retain a human-readable translation file and an associated compiled file that will be used by Flask-Babel.

    pybabel init -i messages.pot -d service/translations -l cy

Make sure that there is a `translations` folder in `service/` as this is where Flask-Babel will look.

This step should create the following file;

    service/translations/cy/LC_MESSAGES/messages.po

This is the file that should contain the Welsh translations. It can be edited in any text editor.

An example of a translation is;

    #: service/templates/display_title.html:56
    #, fuzzy
    msgid "Summary of title"
    msgstr "Crynodeb o deitl "

The value for `msgstr` is added manually.

#### Compile the translations

The final step is to compile the translations into a `.mo` file. The command is;

    pybabel compile -f -d service/translations

Verify `service/translations/cy/LC_MESSAGES`; it should contain two files, 'messages.po' (the original language file) and `messages.mo` (the compiled language file).

#### Updating the translations

Translations can be updated by re-running the extract command above followed by an update;

    pybabel extract -F babel.cfg -o messages.pot .
    pybabel update -i messages.pot -d service/translations

The update command should merge existing and new translations. Following this, recompile in the same way as above;

    pybabel compile -f -d service/translations

Cael hwyl!
