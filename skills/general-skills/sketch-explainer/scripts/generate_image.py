"""
Generate a sketch-explainer image.

Primary backend: OpenAI GPT Image (gpt-image-2, falls back to gpt-image-1).
Fallback backend: Google Gemini ("Nano-banana") if OpenAI is unavailable/errors.

Usage:
    python generate_image.py "your image prompt here" [output_filename]

Key handling (secure — no secret ever lives in this skill folder or in argv):
    The script reads keys from, in order:
      1. ~/.claude/skills/sketch-explainer/.config/.env.local  (KEY=VALUE, chmod 600)
      2. process environment
    Looks for OPENAI_API_KEY (primary) and GEMINI_API_KEY (fallback).

    Optional overrides (env or .env file):
      SKETCH_IMAGE_SIZE     default "1536x1024" (landscape; W & H divisible by 16)
      SKETCH_IMAGE_QUALITY  default "high"      (low | medium | high | auto)
"""

import sys
import os
import json
import base64
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

KEY_FILE = Path.home() / ".claude" / "skills" / "sketch-explainer" / ".config" / ".env.local"
OPENAI_URL = "https://api.openai.com/v1/images/generations"
OPENAI_MODELS = ["gpt-image-2", "gpt-image-1"]  # primary, then fallback model


def load_keys() -> dict:
    """Merge keys from the dedicated key file and the process environment.
    Environment wins over the file. Values are never printed."""
    keys = {}
    if KEY_FILE.is_file():
        try:
            for raw in KEY_FILE.read_text().splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                keys[k.strip()] = v.strip().strip('"').strip("'")
        except Exception as e:
            print(f"WARNING: could not read {KEY_FILE}: {e}")
    for k in ("OPENAI_API_KEY", "GEMINI_API_KEY"):
        if os.environ.get(k):
            keys[k] = os.environ[k]
    return keys


def _write_image_bytes(data: bytes, output_path: str, ext: str) -> str:
    final_path = str(output_path).rsplit(".", 1)[0] + "." + ext
    Path(final_path).parent.mkdir(parents=True, exist_ok=True)
    with open(final_path, "wb") as f:
        f.write(data)
    return final_path


def generate_openai(prompt: str, output_path: str, api_key: str) -> str:
    """Call OpenAI Images. Returns saved path, or raises on hard failure.
    The API key is passed to curl through a chmod-600 config file so it never
    appears in the process argument list (`ps`)."""
    size = os.environ.get("SKETCH_IMAGE_SIZE") or "1536x1024"
    quality = os.environ.get("SKETCH_IMAGE_QUALITY") or "high"

    last_err = None
    for model in OPENAI_MODELS:
        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
            "output_format": "png",
        }
        tmp = tempfile.mkdtemp(prefix="sketch_openai_")
        try:
            payload_path = os.path.join(tmp, "payload.json")
            cfg_path = os.path.join(tmp, "curl.cfg")
            with open(payload_path, "w") as f:
                json.dump(payload, f)
            # curl config file — key stays out of argv
            cfg = (
                f'url = "{OPENAI_URL}"\n'
                'request = "POST"\n'
                f'header = "Authorization: Bearer {api_key}"\n'
                'header = "Content-Type: application/json"\n'
                f'data-binary = "@{payload_path}"\n'
                "fail-with-body\n"
                "silent\n"
                "show-error\n"
            )
            with open(cfg_path, "w") as f:
                f.write(cfg)
            os.chmod(cfg_path, 0o600)
            os.chmod(payload_path, 0o600)

            print(f"Trying OpenAI model: {model} (size={size}, quality={quality})")
            proc = subprocess.run(
                ["curl", "-K", cfg_path],
                capture_output=True,
                text=True,
                timeout=300,
            )
            body = proc.stdout or ""
            if proc.returncode != 0:
                # HTTP error: body carries an OpenAI error object
                msg = body
                try:
                    err = json.loads(body).get("error", {})
                    msg = err.get("message", body)
                    code = err.get("code") or ""
                except Exception:
                    code = ""
                # Unknown model -> try the next model in the chain
                if "model" in msg.lower() and (
                    "does not exist" in msg.lower()
                    or "not found" in msg.lower()
                    or code == "model_not_found"
                ):
                    print(f"Model {model} unavailable, trying next OpenAI model...")
                    last_err = msg
                    continue
                raise RuntimeError(f"OpenAI error: {msg}")

            resp = json.loads(body)
            b64 = resp["data"][0]["b64_json"]
            final = _write_image_bytes(base64.b64decode(b64), output_path, "png")
            print(f"Image saved: {final}")
            return final
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    raise RuntimeError(f"All OpenAI models failed. Last error: {last_err}")


def generate_gemini(prompt: str, output_path: str, api_key: str) -> str:
    """Fallback backend: Google Gemini image models ("Nano-banana")."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise RuntimeError(
            "google-genai package not installed. Run: pip install google-genai"
        )

    client = genai.Client(api_key=api_key)
    models_to_try = ["gemini-3.1-flash-image-preview", "gemini-2.5-flash-image"]
    response = None
    for model in models_to_try:
        try:
            print(f"Trying Gemini model: {model}")
            response = client.models.generate_content(
                model=model,
                contents=[prompt],
                config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
            )
            break
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"Quota exceeded for {model}, trying next model...")
                continue
            raise

    if response is None:
        raise RuntimeError("Gemini returned no response (all models exhausted).")

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            mime = part.inline_data.mime_type  # e.g. "image/png"
            ext = mime.split("/")[-1] if "/" in mime else "png"
            final = _write_image_bytes(part.inline_data.data, output_path, ext)
            print(f"Image saved: {final}")
            return final

    raise RuntimeError("No image returned by Gemini.")


def generate_image(prompt: str, output_path: str) -> None:
    keys = load_keys()
    openai_key = keys.get("OPENAI_API_KEY")
    gemini_key = keys.get("GEMINI_API_KEY")

    if not openai_key and not gemini_key:
        print(
            "ERROR: no API key found.\n"
            f"  Put OPENAI_API_KEY=... in {KEY_FILE} (chmod 600), or export it.\n"
            "  (GEMINI_API_KEY is used only as a fallback.)"
        )
        sys.exit(1)

    # Primary: OpenAI. Fallback: Gemini.
    if openai_key:
        try:
            generate_openai(prompt, output_path, openai_key)
            return
        except Exception as e:
            print(f"OpenAI backend failed: {e}")
            if gemini_key:
                print("Falling back to Gemini...")
            else:
                print("No Gemini fallback key available.")
                sys.exit(1)

    if gemini_key:
        try:
            generate_gemini(prompt, output_path, gemini_key)
            return
        except Exception as e:
            print(f"Gemini backend failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python generate_image.py "prompt" [output_filename]')
        sys.exit(1)

    prompt = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"sketch_explainer_output/sketch_{timestamp}.png"

    generate_image(prompt, output_file)
