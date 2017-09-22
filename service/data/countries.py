import json
from operator import itemgetter


def load_countries(country_file):
    """Pull in the list of countries for the registration form"""
    countries_register = json.loads(open(country_file).read())
    countries = []

    for code in countries_register:
        countries.append((countries_register[code]['name'], countries_register[code]['name']))

    return sorted(countries, key=itemgetter(1))
