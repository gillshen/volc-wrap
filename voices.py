import json
from collections import namedtuple

Voice = namedtuple("Voice", ["name", "code", "category"])
_voices: list[Voice] = []

categories: list[str] = []

with open("voices.json", encoding="utf-8") as _json:
    _data: dict = json.load(_json)
    for category, collection in _data.items():
        categories.append(category)
        for name, code in collection.items():
            _voices.append(Voice(name, code, category))

_voices.sort()

del category
del collection
del name
del code


def get_voices(category: str = "") -> list[Voice]:
    if category:
        return [v for v in _voices if v.category == category]

    # if `category` is empty, return the whole list without duplicates
    codes = set()
    all_voices: list[Voice] = []
    for v in _voices:
        if v.code not in codes:
            all_voices.append(v)
            codes.add(v.code)
    return all_voices
