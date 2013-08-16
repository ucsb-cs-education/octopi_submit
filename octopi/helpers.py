import re


def alphanum_key(string):
    """Return a comparable tuple with extracted number segments.

    Adapted from: http://stackoverflow.com/a/2669120/176978

    """
    convert = lambda text: int(text) if text.isdigit() else text
    return [convert(segment) for segment in re.split('([0-9]+)', string)]
