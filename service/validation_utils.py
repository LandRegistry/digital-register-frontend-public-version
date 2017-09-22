import re


# Postcode regex is initialised on first call to validate_postcode().
_POSTCODE_REGEX = None


def is_valid_postcode(postcode):

    # Check if a postcode is valid or not

    global _POSTCODE_REGEX
    if _POSTCODE_REGEX is None:
        # Initialise regex on first use.
        parts = {
            'fst': 'ABCDEFGHIJKLMNOPRSTUWYZ',
            'sec': 'ABCDEFGHKLMNOPQRSTUVWXY',
            'thd': 'ABCDEFGHJKMNPRSTUVWXY',
            'fth': 'ABEHMNPRVWXY',
            'inward': 'ABDEFGHJLNPQRSTUWXYZ',
        }
        _POSTCODE_REGEX = re.compile('|'.join([r.format(**parts) for r in (
            '^[{fst}][1-9]\d[{inward}][{inward}]$',
            '^[{fst}][1-9]\d\d[{inward}][{inward}]$',
            '^[{fst}][{sec}]\d\d[{inward}][{inward}]$',
            '^[{fst}][{sec}][1-9]\d\d[{inward}][{inward}]$',
            '^[{fst}][1-9][{thd}]\d[{inward}][{inward}]$',
            '^[{fst}][{sec}][1-9][{fth}]\d[{inward}][{inward}]$',
        )]))

    return _POSTCODE_REGEX.match(postcode.replace(' ', '').upper()) is not None
