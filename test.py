from core import tts


def test_tts():
    with open("test.txt", encoding="utf-8") as f:
        text = f.read()
    for _, message in tts(text, save_path="test"):
        print(message)


def test_tts_long():
    with open("test_long.txt", encoding="utf-8") as f:
        text = f.read()
    for _, message in tts(text, save_path="test_long"):
        print(message)


if __name__ == "__main__":
    test_tts()
    test_tts_long()
