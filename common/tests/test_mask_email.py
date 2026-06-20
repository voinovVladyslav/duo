import pytest

from common.masks import mask_email


@pytest.mark.parametrize(
    ('email', 'expected'),
    [
        ('text@example.com', 't***@example.com'),
        ('t@example.com', 't@example.com'),
        ('test@test.com', 't***@test.com'),
    ],
)
def test_mask_email(email: str, expected: str):
    assert mask_email(email) == expected


def test_invalid_email_is_not_masked():
    value = 'invalid@email'
    assert mask_email(value) == value
