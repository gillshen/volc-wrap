import json
from collections import namedtuple

from pypinyin import lazy_pinyin

LANGUAGE_NAMES = {
    "cn": "中文",
    "en": "英语",
    "ja": "日语",
    "thth": "泰语",
    "vivn": "越南语",
    "ptbr": "葡萄牙语",
    "esmx": "西班牙语",
    "id": "印尼语",
    "zh_dongbei": "东北话",
    "zh_yueyu": "粤语",
    "zh_shanghai": "上海话",
    "zh_xian": "西安话",
    "zh_chengdu": "成都话",
    "zh_taipu": "台湾普通话",
    "zh_guangxi": "广西普通话",
}

Language = namedtuple("Language", ["name", "code"])

with open("languages.json", encoding="utf-8") as _json:
    _languages = json.load(_json)


del _json


def get_languages(voice_name: str) -> list[Language]:
    codes = _languages.get(voice_name, [])
    langs: list[Language] = [Language(LANGUAGE_NAMES[c], c) for c in codes]

    def as_pinyin(lang: Language) -> list:
        if lang.code == "cn":
            # Put Chinese first
            return []
        else:
            return lazy_pinyin(lang.name)

    langs.sort(key=as_pinyin)
    return langs


if __name__ == "__main__":
    print(locals().keys())
