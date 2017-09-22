unittest:
	export SETTINGS='test'; py.test --junitxml=test-output/unit-test-output.xml tests/ --cov-report=html:test-output/unit-test-cov-report --ignore=integration_tests --doctest-modules

integrationtest:
	py.test --junitxml=test-output/integration-test-output.xml integration_tests/ --cov-append --cov-report=html:test-output/integration-test-cov-report --ignore=tests
