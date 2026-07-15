from app.main import profile

def test_profile() -> None:
    assert profile()["name"] == "Ada"
