import base64
import json
import uuid
import re
import requests


class ApiError(Exception):
    pass


with open("apikey.txt") as api_file:
    appid, access_token, cluster = api_file.read().splitlines()

headers = {"Authorization": f"Bearer;{access_token}"}
host = "openspeech.bytedance.com"
api_url = f"https://{host}/api/v1/tts"


def tts(
    text: str,
    save_path: str,
    voice_type: str = "BV702_streaming",
    speed_ratio: float = 1.0,
    volume_ratio: float = 1.0,
    pitch_ratio: float = 1.0,
    emotion: str = "",
    language: str = "",
):
    if language in {"", "cn", "ja"} or language.startswith("zh_"):
        sentence_pattern = r""".+?(?:[。！？]["”」』)）]*|\n|$)\s*"""
    else:
        sentence_pattern = r""".+?(?:[.!?]["”)]*|\n|$)\s*"""

    max_len = 250
    chunks = []
    for sentence in re.findall(sentence_pattern, text):
        if not chunks or len(chunks[-1]) + len(sentence) > max_len:
            chunks.append(sentence)
        else:
            chunks[-1] += sentence

    audio_params = {
        "voice_type": voice_type,
        "encoding": "mp3",
        "speed_ratio": speed_ratio,
        "volume_ratio": volume_ratio,
        "pitch_ratio": pitch_ratio,
    }
    if emotion:
        audio_params["emotion"] = emotion
    if language:
        audio_params["language"] = language

    if not save_path.endswith(".mp3"):
        save_path += ".mp3"

    with open(save_path, "wb") as target_file:
        n = len(chunks)
        for i, chunk in enumerate(chunks, start=1):
            resp = api_request(chunk, audio_params)
            if "data" not in resp:
                raise ApiError(resp["message"])
            data = resp["data"]
            target_file.write(base64.b64decode(data))
            yield data, f"Progress: {i}/{n}"


def api_request(text: str, audio_params: dict):
    payload = {
        "app": {
            "appid": appid,
            "token": "access_token",
            "cluster": cluster,
        },
        "user": {
            "uid": "388808087185088",
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
