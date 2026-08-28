from src.hello import hello


def test_hello_output(capsys):
    """Test that hello() prints exactly 'Hello World'."""
    hello()
    captured = capsys.readouterr()
    assert captured.out.strip() == "Hello World"
