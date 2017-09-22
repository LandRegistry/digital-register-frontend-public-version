(function() {
  var search_form = document.querySelector('[data-clientside-validation="search_form_validation"]');

  window.PubSub.subscribe('clientside-form-validation.valid', function(msg, data) {

    if (search_form !== data.element) {
      return
    }

    var promise = new Promise(function (resolve, reject) {
      search_term = document.getElementById('search_term').value
      title_number_regex = '^([A-Z]{0,3}[1-9][0-9]{0,5}|[0-9]{1,6}[ZT])$'
      if (search_term.match(title_number_regex)) {
        ga('send', 'event', 'Search', 'TitleNumber', {
          hitCallback: function() {
            submitCalled = true
            clearTimeout(timeout)
            resolve()
          }
        });
      } else {
        resolve()
      }

      var submitCalled = false

      // If google analytics is slow, just bail out after 5 seconds
      var timeout = setTimeout(function() {
        if (!submitCalled) {
          resolve()
        }
      }, 5000)
    })

    data.registerPromise(promise)
  });
})();
