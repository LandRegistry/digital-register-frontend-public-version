(function() {
  var emailField = document.querySelector('[data-existing-fap-email]');

  if(emailField) {
    var existingUserEmail = emailField.getAttribute('data-existing-fap-email');
    sessionStorage.setItem('find-property-information-email', existingUserEmail);
  }

})();
