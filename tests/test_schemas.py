import pytest
from pydantic import ValidationError

from app.schemas import ExecuteRequest, SupportedLanguage


def test_valid_execute_request():
    req = ExecuteRequest(
        language=SupportedLanguage.PYTHON,
        code='print("Hello World")',
    )
    assert req.language == SupportedLanguage.PYTHON
    assert req.code == 'print("Hello World")'


def test_invalid_language():
    with pytest.raises(ValidationError):
        ExecuteRequest(
            language="ruby",  # type: ignore
            code='puts "Hello"',
        )


def test_empty_code_rejected():
    with pytest.raises(ValidationError):
        ExecuteRequest(
            language=SupportedLanguage.PYTHON,
            code="",
        )


def test_max_code_size_exceeded():
    huge_code = "a" * (65536 + 1)
    with pytest.raises(ValidationError):
        ExecuteRequest(
            language=SupportedLanguage.PYTHON,
            code=huge_code,
        )
