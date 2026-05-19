import pytest

from services.auth.password import check_password, hash_password

password = '123123test'


@pytest.mark.unit
def test_hash_password_returns_non_empty_string():
    hashed_password = hash_password(password)

    assert hashed_password is not None


@pytest.mark.unit
def test_hash_password_returns_string():
    hashed_password = hash_password(password)

    assert isinstance(hashed_password, str)


@pytest.mark.unit
def test_hash_password_returns_string_differs_from_input():
    hashed_password = hash_password(password)

    assert hashed_password != password


@pytest.mark.unit
def test_hash_password_returns_different_hash_for_same_input():
    hashed_password1 = hash_password(password)
    hashed_password2 = hash_password(password)

    assert hashed_password1 != hashed_password2


@pytest.mark.unit
def test_check_password_returns_true_if_password_is_correct():
    hashed_password = hash_password(password)

    assert check_password(password, hashed_password)


@pytest.mark.unit
def test_check_password_returns_wrong_if_password_is_wrong():
    hashed_password = hash_password(password)

    assert not check_password('Test123123', hashed_password)


@pytest.mark.unit
def test_check_password_returns_false_if_password_is_wrong():
    hashed_password = hash_password(password)

    assert not check_password('Test123123', hashed_password)


def test_check_password_returns_false_if_password_is_empty():
    hashed_password = hash_password(password)

    assert not check_password('', hashed_password)
