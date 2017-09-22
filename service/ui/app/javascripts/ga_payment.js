(function () {
  window.PubSub.subscribe('clientside-form-validation.valid', function(msg, data) {
    if (data.element.getAttribute('data-clientside-validation') !== 'pay_form_validation') {
      return
    }

    var promise = new Promise(function (resolve, reject) {

      var submitCalled = false

      // If google analytics is slow, just bail out after 5 seconds
      var timeout = setTimeout(function() {
        if (!submitCalled) {
          resolve()
        }
      }, 5000)

      ga('send', 'pageview', '/payment', {
        title: 'Payment',
        hitCallback: function() {
          submitCalled = true
          clearTimeout(timeout)
          resolve()
        }
      })
    })

    data.registerPromise(promise)
  })
})();
