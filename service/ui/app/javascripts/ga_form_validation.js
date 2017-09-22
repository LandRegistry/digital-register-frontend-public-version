(function () {
  window.PubSub.subscribe('clientside-form-validation.error', function(msg, data) {
    ga('send', {
      hitType: 'event',
      eventCategory: 'FormValidation',
      eventAction: data.category + ' | ' + data.error.name,
      eventLabel: data.error.message
    })
  })
})();
