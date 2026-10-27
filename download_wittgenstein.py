
import requests
from pathlib import Path

URL = "https://wab.uib.no/cost-a32_philospace/wittgenstein.owl"
OUTPUT = Path(__file__).resolve().parent / "wittgenstein.owl"

try:
    with requests.get(URL, stream=True, timeout=(20, 300)) as response:
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        first_chunk = next(
            response.iter_content(chunk_size=1024 * 1024),
            b""
        )

        if not first_chunk:
            raise ValueError("The server returned an empty file.")

        if b"<html" in first_chunk[:1000].lower():
            raise ValueError(
                "The server returned HTML instead of the OWL file."
            )

        with OUTPUT.open("wb") as file:
            file.write(first_chunk)

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):
                if chunk:
                    file.write(chunk)

    print("Download completed:", OUTPUT)
    print("File size:", round(OUTPUT.stat().st_size / (1024 * 1024), 2), "MB")

except requests.RequestException as error:
    print("Download failed:", error)

except (OSError, ValueError) as error:
    if OUTPUT.exists():
        OUTPUT.unlink()
    print("Error:", error)
