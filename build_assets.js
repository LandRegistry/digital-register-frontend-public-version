var path = require('path');
var landRegistryElements = require('land-registry-elements');

landRegistryElements({
  'mode': 'production',
  'destination': path.resolve(__dirname, 'service/ui/.land-registry-elements'),
  'assetPath': false, // Don't insert an asset path, we'll let flask set it as a global JS variable
  'components': [
    'pages/find-property-information/search-form',
    'pages/find-property-information/search-results',
    'pages/find-property-information/about-this-property',
    'pages/find-property-information/about-this-property-signed-in',
    'pages/find-property-information/confirm-your-purchase',
    'pages/find-property-information/summary',
    'pages/find-property-information/cookies',
    'pages/find-property-information/account/create',
    'pages/land-registry/error-page'
  ]
})
  .then(function(dest) {
    console.log('Done');
  })
  .catch(function(e) {
    console.error(e);
  });
