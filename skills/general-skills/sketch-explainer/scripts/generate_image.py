"""
Generate a sketch-explainer image using the Gemini API.
Usage: python generate_image.py "your image prompt here" [output_filename]
"""

import sys
import os
from pathlib import Path
from datetime import datetime


def generate_image(prompt: str, output_path: str) -> None:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("ERROR: google-genai package not installed. Run: pip install google-genai")
        sys.exit(1)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "paste_your_key_here":
        print("ERROR: GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Try paid model first, fall back to free-tier model on quota errors
    models_to_try = ["gemini-3.1-flash-image-preview", "gemini-2.5-flash-image"]
    response = None
    for model in models_to_try:
        try:
            print(f"Trying model: {model}")
            response = client.models.generate_content(
                model=model,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )
            break
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"Quota exceeded for {model}, trying next model...")
                continue
            raise

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            # SDK returns already-decoded bytes; derive extension from mime type
            mime = part.inline_data.mime_type  # e.g. "image/jpeg" or "image/png"
            ext = mime.split("/")[-1] if "/" in mime else "jpg"
            final_path = str(output_path).rsplit(".", 1)[0] + "." + ext
            Path(final_path).parent.mkdir(parents=True, exist_ok=True)
            with open(final_path, "wb") as f:
                f.write(part.inline_data.data)
            print(f"Image saved: {final_path}")
            return

    print("ERROR: No image returned by the API.")
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_image.py \"prompt\" [output_filename]")
        sys.exit(1)

    prompt = sys.argv[1]

    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"sketch_explainer_output/sketch_{timestamp}.png"

    generate_image(prompt, output_file)
