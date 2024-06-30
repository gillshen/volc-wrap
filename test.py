from core import api_request


def test_api_request():
    with open("test.txt", encoding="utf-8") as f:
        text = f.read()
    api_request(text, save_path="test")


if __name__ == "__main__":
    test_api_request()
    print("test completed")
