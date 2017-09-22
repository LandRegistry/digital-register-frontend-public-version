from werkzeug.routing import BaseConverter
from service import encryption_utils
import re


TITLE_NUMBER_REGEX = re.compile('^([A-Z]{0,3}[1-9][0-9]{0,5}|[0-9]{1,6}[ZT])$')


def is_title_number(search_term):
    return TITLE_NUMBER_REGEX.match(search_term) is not None


class TitleNumberConverter(BaseConverter):

    def to_python(self, value):
        return encryption_utils.decrypt(value)

    def to_url(self, value):
        return encryption_utils.encrypt(value)
