from json import load as json_load
from re import sub as replace
from emerge import RE_CONFLICTED_PACKAGES

def test_regex():
    datafile = replace('\.py$', '.json', __file__)
    with open(datafile, 'r') as f:
        data = json_load(f)

    for expectation in data:
        match = RE_CONFLICTED_PACKAGES.match(expectation['output'])
        assert match is not None
        assert match.group('package1') == expectation['result'][0]
        assert match.group('package2') == expectation['result'][1]
