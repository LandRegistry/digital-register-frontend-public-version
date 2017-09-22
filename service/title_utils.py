
def is_caution_title(title_data):

    return False if title_data is None else title_data.get('is_caution_title', False)
