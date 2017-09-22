/* global GOVUK */
(function () {

  var head = document.head || document.getElementsByTagName('head')[0]
  var css = document.createElement('style')

  css.setAttribute('type', 'text/css')
  css.setAttribute('media', 'print')
  head.appendChild(css)

  function updateStyles () {
    // If we're not currently showing the window, don't bother updating the cachebuster
    if (document.hidden) {
      return
    }

    var gif = 'https://google-analytics.com/collect?v=1&t=event' +
    '&ec=browser&tid=' + window.google_api_key + '&cid=' + GOVUK.getCookie('_ga') +
    '&ea=print_intent' +
    '&el=' + encodeURIComponent(window.printIntentEventLabel) +
    '&z=' + (Math.round((new Date()).getTime() / 1000)).toString()

    var rule = 'body:after{content:url(' + gif + ')}'

    if (css.styleSheet) { // For IE
      css.styleSheet.cssText = rule
    } else {
      while (css.firstChild) {
        css.removeChild(css.firstChild)
      }
      css.appendChild(document.createTextNode(rule))
    }
  }

  // Periodically update the tracking styles to force the cache buster to be different each time
  // This is so that repeated views of print preview get tracked consistently across browsers
  // E.g. IE8 sends the tracking every time, but Chrome was not. This resolves that.
  setInterval(updateStyles, 3000)
  updateStyles()
})();
