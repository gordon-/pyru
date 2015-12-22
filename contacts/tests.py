import pytest

from . import models


def test_apply_mapping():
    row = {'key': 'val'}
    mapping = {'new_key': 'key'}
    res = models.apply_mapping(row, mapping)
    assert isinstance(res, dict)
    assert 'new_key' in res
    assert res['new_key'] == 'val'
    assert 'key' not in res

    row = {'k1': 'v1', 'k2': 'v2', 'k3': 'v3'}
    mapping = {'k1_': 'k1', 'k2_': 'k2'}
    res = models.apply_mapping(row, mapping)
    assert 'k1_' in res
    assert 'k3' in res
    assert 'k2' not in res

    # keep the same row
    mapping = {'k4_': 'k4'}
    exception_raised = False
    try:
        models.apply_mapping(row, mapping)
    except models.DataImportError:
        exception_raised = True
    assert exception_raised
