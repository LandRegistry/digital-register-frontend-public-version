(function () {

  var downloadLink = document.querySelector('[data-pdf-download]');

  if(downloadLink) {
    downloadLink.addEventListener('click', function(e) {
      ga('send', {
        hitType: 'event',
        eventCategory: 'PDF',
        eventAction: 'download',
        eventLabel: 'title_summary'
      })
    })
  }

})();