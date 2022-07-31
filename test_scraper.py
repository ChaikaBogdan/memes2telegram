from scraper import is_dtf_video, get_uuid


def test_is_dtf_video():
    assert is_dtf_video('https://leonardo.osnova.io/xxx/-/format/mp4/') is True


def test_is_not_dtf_video():
    assert is_dtf_video('https://img-9gag-fun.9cache.com/photo/xxx.mp4') is False


def test_get_uuid():
    assert get_uuid(
        'https://leonardo.osnova.io/c01ed790-49bd-5bea-98f6-e3534c8d7493/-/format/mp4/') == 'c01ed790-49bd-5bea-98f6-e3534c8d7493'
