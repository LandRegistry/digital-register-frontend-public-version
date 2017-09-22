"""
babel_admin.py

Creates or updates a set of translations for front end
DM 19-Nov-2015
"""

import os
import sys


def _preamble():

    txt = "\nFlask-Babel admin script (by Dunc)\n\nUse this to create (generate)"\
          "a set of translations or update existing translations.\n\n"
    print(txt)


def _compile_translations():

    os.system('pybabel extract -F babel.cfg -o messages.pot .')
    os.system('pybabel init -i messages.pot -d service/translations -l cy')
    os.system('pybabel compile -f -d service/translations')
    return


def _update_translations():

    os.system('pybabel extract -F babel.cfg -o messages.pot .')
    os.system('pybabel update -i messages.pot -d service/translations')
    os.system('pybabel compile -f -d service/translations')
    return


if __name__ == "__main__":

    _preamble()

    # Get update or create option
    opt = input("(C)reate or (U)pdate: ")
    if opt is None:
        sys.exit(0)

    opt = opt.lower()

    if opt == 'c':
        _compile_translations()
    elif opt == 'u':
        _update_translations()
    else:
        print("Invalid option (%s)" % opt)
        sys.exit(0)
