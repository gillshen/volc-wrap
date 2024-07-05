import base64
from dataclasses import dataclass, asdict
import json
import uuid
import re
import requests


class ApiError(Exception):
    pass


@dataclass()
class AudioParams:
    voice_type: str = "BV702_streaming"  # Stefan
    rate: int = 24_000  # sample rate
    encoding: str = "mp3"
    compression_rate: int = 1
    speed_ratio: float = 1.0
    volume_ratio: float = 1.0
    pitch_ratio: float = 1.0
    emotion: str = ""
    language: str = ""


with open("apikey.txt") as api_file:
    appid, access_token, cluster = filter(None, api_file.read().splitlines())

headers = {"Authorization": f"Bearer;{access_token}"}
host = "openspeech.bytedance.com"
api_url = f"https://{host}/api/v1/tts"
user_uid = str(uuid.uuid4())


def tts(text: str, audio_params: AudioParams, save_path: str):
    language = AudioParams.language
    if language in {"", "cn", "ja"} or language.startswith("zh_"):
        sentence_pattern = r""".+?(?:[。！？]["”」』)）]*|\n|$)\s*"""
    else:
        sentence_pattern = r""".+?(?:[.!?]["”)]*|\n|$)\s*"""

    max_len = 1024
    chunks = []
    for sentence in re.findall(sentence_pattern, text):
        if not chunks or _byte_len(chunks[-1] + sentence) > max_len:
            chunks.append(sentence)
        else:
            chunks[-1] += sentence

    audio_params_dict = asdict(audio_params)
    if not language:
        del audio_params_dict["language"]
    if not audio_params.emotion:
        del audio_params_dict["emotion"]

    with open(save_path, "wb") as target_file:
        n = len(chunks)
        for i, chunk in enumerate(chunks, start=1):
            resp = api_request(chunk, audio_params_dict)
            if "data" not in resp:
                raise ApiError(resp["message"])
            data = resp["data"]
            target_file.write(base64.b64decode(data))
            yield data, f"Progress: {i}/{n}"


def _byte_len(text: str):
    return len(text.encode("utf-8"))


def api_request(text: str, audio_params: dict):
    payload = {
        "app": {
            "appid": appid,
            "token": "access_token",
            "cluster": cluster,
        },
        "user": {
            "uid": user_uid,
        },
        "audio": audio_params,
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "text_type": "plain",
            "operation": "query",
            "with_frontend": 1,
            "frontend_type": "unitTson",
        },
    }
    try:
        resp = requests.post(api_url, json.dumps(payload), headers=headers)
        return resp.json()
    except Exception as e:
        raise ApiError from e
