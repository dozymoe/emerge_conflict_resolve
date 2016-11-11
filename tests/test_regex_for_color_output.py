from json import load as json_load
from re import sub as replace
from emerge import RE_COLOR

def test_regex_match():
    datafile = replace('\.py$', '.json', __file__)
    with open(datafile, 'r') as f:
        data = json_load(f)

    for sample in data:
        assert RE_COLOR.match(sample) is not None
