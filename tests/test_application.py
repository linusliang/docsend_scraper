import pytest

from application import normalize_url, ApplicationError


@pytest.mark.parametrize("input_,expected",[
    ('https://docsend.com/view/p8jxsqr', 'https://docsend.com/view/p8jxsqr'),
    ('docsend.com/view/p8jxsqr', 'https://docsend.com/view/p8jxsqr'),
    ('p8jxsqr', 'https://docsend.com/view/p8jxsqr')
])
def test_normalize_url_good(input_, expected):
    assert normalize_url(input_) == expected


@pytest.mark.parametrize("input_,expected",[
    ('', '`` is not a valid url or id'),
    ('h3a.af', '`h3a.af` is not a valid url or id')
])
def test_normalize_url_bad(input_, expected):
    with pytest.raises(ApplicationError) as err:
        normalize_url(input_)
    assert err.value.args == (expected,)
