import base64
import os
import time
from typing import List, Optional, Tuple
import requests

def _encode_image_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def upload_image_to_imgbb(image_path: str, api_key: str, name: Optional[str] = None, timeout: int = 30) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Upload a single image to imgbb.

    Returns: (success, direct_url, error_message)
    """
    try:
        if not os.path.isfile(image_path):
            return False, None, f"Archivo no encontrado: {image_path}"

        img_b64 = _encode_image_b64(image_path)
        payload = {
            "key": api_key,
            "image": img_b64,
        }
        if name:
            payload["name"] = name

        resp = requests.post("https://api.imgbb.com/1/upload", data=payload, timeout=timeout)
        if resp.status_code != 200:
            return False, None, f"HTTP {resp.status_code}: {resp.text}"

        data = resp.json().get("data", {})
        # prefer direct image URL if available, else fallback to public URL
        direct = None
        if isinstance(data, dict):
            # imgbb typically provides display_url and url; some clients include image.url
            direct = data.get("image", {}).get("url") if isinstance(data.get("image"), dict) else None
            if not direct:
                direct = data.get("display_url") or data.get("url")
        if not direct:
            return False, None, "Respuesta de imgbb sin URL usable"

        return True, direct, None
    except Exception as e:
        return False, None, str(e)

def upload_images_to_imgbb(image_paths: List[str], api_key: str, name_prefix: Optional[str] = None, max_count: int = 3) -> List[str]:
    """
    Upload multiple images and return a list of direct URLs (up to max_count).
    Skips files that fail to upload; returns URLs for successes only.
    """
    results: List[str] = []
    ts = int(time.time())
    for idx, path in enumerate(image_paths[:max_count], start=1):
        name = None
        if name_prefix:
            base = os.path.splitext(os.path.basename(path))[0]
            name = f"{name_prefix}_{base}_{ts}_{idx}"
        ok, url, _err = upload_image_to_imgbb(path, api_key, name=name)
        if ok and url:
            results.append(url)
    return results
