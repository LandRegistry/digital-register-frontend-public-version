from flask.ext.assets import Bundle
import sass


def compile_sass(_in, out, **kw):
    out.write(
        sass.compile(
            string=_in.read()
        )
    )


govuk = Bundle('.land-registry-elements/assets/stylesheets/govuk-template.css',
               filters=('cssmin'), output='.dist/stylesheets/govuk-template.%(version)s.css')

govuk_ie8 = Bundle('.land-registry-elements/assets/stylesheets/govuk-template-ie8.css',
                   filters=('cssmin'), output='.dist/stylesheets/govuk-template-ie8.%(version)s.css')

govuk_ie7 = Bundle('.land-registry-elements/assets/stylesheets/govuk-template-ie7.css',
                   filters=('cssmin'), output='.dist/stylesheets/govuk-template-ie7.%(version)s.css')

govuk_ie6 = Bundle('.land-registry-elements/assets/stylesheets/govuk-template-ie6.css',
                   filters=('cssmin'), output='.dist/stylesheets/govuk-template-ie6.%(version)s.css')

govuk_print = Bundle('.land-registry-elements/assets/stylesheets/govuk-template-print.css',
                     filters=('cssmin'), output='.dist/stylesheets/govuk-template-print.%(version)s.css')

elements = Bundle('.land-registry-elements/assets/stylesheets/elements.css',
                  'app/stylesheets/application.scss',
                  filters=(compile_sass, 'cssmin'), output='.dist/stylesheets/main.%(version)s.css')

elements_ie8 = Bundle('.land-registry-elements/assets/stylesheets/elements-ie8.css',
                      '.land-registry-elements/assets/stylesheets/fonts-ie8.css',
                      'app/stylesheets/application.scss',
                      filters=(compile_sass, 'cssmin'), output='.dist/stylesheets/main-ie8.%(version)s.css')

elements_ie7 = Bundle('.land-registry-elements/assets/stylesheets/elements-ie7.css',
                      '.land-registry-elements/assets/stylesheets/fonts-ie8.css',
                      'app/stylesheets/application.scss',
                      filters=(compile_sass, 'cssmin'), output='.dist/stylesheets/main-ie7.%(version)s.css')

elements_ie6 = Bundle('.land-registry-elements/assets/stylesheets/elements-ie6.css',
                      '.land-registry-elements/assets/stylesheets/fonts-ie8.css',
                      'app/stylesheets/application.scss',
                      filters=(compile_sass, 'cssmin'), output='.dist/stylesheets/main-ie6.%(version)s.css')


js_polyfills_ie9 = Bundle('.land-registry-elements/assets/javascripts/polyfills-ie9.js',
                          filters=('rjsmin'), output='.dist/javascripts/polyfills-ie9.%(version)s.js')

js_polyfills_ie8 = Bundle('.land-registry-elements/assets/javascripts/polyfills-ie8.js',
                          filters=('rjsmin'), output='.dist/javascripts/polyfills-ie8.%(version)s.js')

js_promise = Bundle('.land-registry-elements/assets/javascripts/polyfills-promise.js',
                    filters=('rjsmin'), output='.dist/javascripts/polyfills-promise.%(version)s.js')


js = Bundle('.land-registry-elements/assets/javascripts/govuk-template.js',
            '.land-registry-elements/assets/javascripts/landregistry.js',
            'app/javascripts/register-form-existing-fap-user.js',
            'app/javascripts/ga_form_validation.js',
            'app/javascripts/ga_search.js',
            'app/javascripts/ga_print.js',
            'app/javascripts/ga_download.js',
            'app/javascripts/ga_outbound.js',
            'app/javascripts/rate_limiting.js',
            filters='rjsmin', output='.dist/javascripts/main.%(version)s.js')

js_map = Bundle('.land-registry-elements/assets/javascripts/leaflet.js',
                filters='rjsmin', output='.dist/javascripts/property-map.%(version)s.js')

js_ga_payment = Bundle('app/javascripts/ga_payment.js',
                       filters='rjsmin', output='.dist/javascripts/ga_payment.%(version)s.js')
