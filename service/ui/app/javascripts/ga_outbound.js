/* global ga */
(function () {
  var links = document.getElementsByTagName('a');

  [].forEach.call(links, function (link) {
    var isExternal = link.href.indexOf(window.location.protocol + '//' + window.location.host) !== 0
    var isHash = link.href.indexOf('#') === 0
    if (isExternal && !isHash) {
      link.addEventListener('click', function (e) {
        e.preventDefault()

        ga('send', 'event', 'outbound', 'click', link.href, {
          'transport': 'beacon',
          'hitCallback': function () {
            document.location = link.href
          }
        })
      })
    }
  })
})();
