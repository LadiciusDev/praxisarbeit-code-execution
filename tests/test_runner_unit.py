from app.runner import _truncate_output


def test_truncate_output_short():
    data = b"Hello, World!\n"
    res = _truncate_output(data, 100)
    assert res == "Hello, World!\n"


def test_truncate_output_exceeding():
    data = b"A" * 150
    res = _truncate_output(data, 100)
    assert res.startswith("A" * 100)
    assert "Hinweis: Ausgabe bei 0 KB abgeschnitten" in res
