(function () {
  var durationElement = document.querySelector('[data-rate-limit-retry-seconds]')
  var button = document.querySelector('[data-rate-limit-retry-action]')

  var notifier = document.createElement('div')
  notifier.classList.add('visuallyhidden')
  notifier.setAttribute('role', 'log')
  notifier.setAttribute('aria-live', 'polite')
  notifier.setAttribute('aria-atomic', 'false')
  document.body.appendChild(notifier)

  function divmod (value, divisor) {
    return [Math.floor(value / divisor), value % divisor]
  }

  function formatDuration (seconds) {
    var duration = divmod(seconds, 60)

    if (seconds === 0) {
      return 'now.'
    }

    var formattedDuration = ''

    if (duration[0] > 0) {
      formattedDuration += duration[0] + ' minute' + (duration[0] > 1 ? 's ' : ' ')
    }

    if (duration[1] > 0) {
      formattedDuration += duration[1] + ' second' + (duration[1] > 1 ? 's ' : ' ')
    }

    return 'in ' + formattedDuration.trim()
  }

  if (durationElement) {
    var durationAmount = parseInt(durationElement.getAttribute('data-rate-limit-retry-seconds'))
    button.disabled = true

    var countdown = setInterval(function () {
      if (durationAmount > 0) {
        durationAmount--
        durationElement.textContent = formatDuration(durationAmount)
      }

      // Notify screen readers every 10 seconds
      if (durationAmount % 10 === 0) {
        notifier.textContent = durationElement.parentNode.textContent
      }

      if (durationAmount === 0) {
        clearInterval(countdown)
        button.disabled = false
        button.focus()
      }
    }, 1000)
  }
})();
