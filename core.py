import base64
import json
import uuid
import requests


class ApiError(Exception):
    pass


with open("apikey.txt") as api_file:
    appid, access_token, cluster = api_file.read().splitlines()

headers = {"Authorization": f"Bearer;{access_token}"}
host = "openspeech.bytedance.com"
api_url = f"https://{host}/api/v1/tts"


def api_request(
    text: str,
    save_path: str,
    voice_type: str = "BV702_streaming",
    text_type: str = "plain",
    speed_ratio: float = 1.0,
    volume_ratio: float = 1.0,
    pitch_ratio: float = 1.0,
    emotion: str = "",
    language: str = "",
):
    request_json = {
        "app": {
            "appid": appid,
            "token": "access_token",
            "cluster": cluster,
        },
        "user": {
            "uid": "388808087185088",
        },
        "audio": {
            "voice_type": voice_type,
            "encoding": "mp3",
            "speed_ratio": speed_ratio,
            "volume_ratio": volume_ratio,
            "pitch_ratio": pitch_ratio,
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "text_type": text_type,
            "operation": "query",
            "with_frontend": 1,
            "frontend_type": "unitTson",
        },
    }
    if emotion:
        request_json["audio"]["emotion"] = emotion
    if language:
        request_json["audio"]["language"] = language

    try:
        resp = requests.post(
            api_url,
            json.dumps(request_json),
            headers=headers,
        )
        body = resp.json()
    except Exception as e:
        raise ApiError from e

    if "data" in body:
        if not save_path.endswith(".mp3"):
            save_path += ".mp3"
        with open(save_path, "wb") as target_file:
            target_file.write(base64.b64decode(body["data"]))
    else:
        raise ApiError(body["message"])
