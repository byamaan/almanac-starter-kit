#!/usr/bin/env python3
"""
Sequential Replicate batch generator for almanac carousels.

Walks every <carousel>/prompts.json under this directory, skips slides whose
illustration PNG already exists, and POSTs to Replicate's
google/nano-banana-2 endpoint with >=10.5s spacing between creates
(low-credit rate-limit defense). Polls each prediction in a background
thread and downloads the output to <carousel>/illustrations/<id>.png.

REPLICATE_API_TOKEN is sourced from (in order):
  1. The REPLICATE_API_TOKEN environment variable
  2. A `.env` file at the project root, line `REPLICATE_API_TOKEN=r8_...`

Usage:
    # Generate for one specific carousel folder
    python3 batch_generate.py almanac-01-<slug>

    # Generate for every carousel that has a prompts.json
    python3 batch_generate.py
"""
from __future__ import annotations
import json
import os
import re
import sys
import time
import threading
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
ENDPOINT = "https://api.replicate.com/v1/models/google/nano-banana-2/predictions"
CREATE_SPACING_S = 10.5
POLL_INTERVAL_S = 3.0


def _load_token() -> str:
    token = os.environ.get("REPLICATE_API_TOKEN")
    if token:
        return token.strip()
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            m = re.match(r"\s*REPLICATE_API_TOKEN\s*=\s*(.+?)\s*$", line)
            if m:
                value = m.group(1).strip().strip('"').strip("'")
                if value:
                    return value
    sys.exit(
        "REPLICATE_API_TOKEN not found.\n"
        "Set the REPLICATE_API_TOKEN env var, or create a `.env` file at\n"
        f"  {PROJECT_ROOT}\n"
        "with line:  REPLICATE_API_TOKEN=r8_..."
    )


TOKEN = _load_token()
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

CAROUSEL_FILTER = sys.argv[1:] if len(sys.argv) > 1 else None


def http_request(url: str, method: str = "GET", body: dict | None = None, timeout: int = 60) -> bytes:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def download(url: str, dest: Path, timeout: int = 120) -> None:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        dest.write_bytes(r.read())


def poll_and_download(prediction_id: str, get_url: str, dest: Path, label: str) -> None:
    while True:
        try:
            res = json.loads(http_request(get_url))
        except urllib.error.HTTPError as e:
            print(f"  [{label}] poll err {e.code}; retry")
            time.sleep(POLL_INTERVAL_S)
            continue
        status = res.get("status")
        if status in ("succeeded", "failed", "canceled"):
            break
        time.sleep(POLL_INTERVAL_S)

    if status != "succeeded":
        print(f"  [{label}] FAILED: {res.get('error') or status}")
        return

    out = res.get("output")
    out_url = out[0] if isinstance(out, list) else out
    if not out_url:
        print(f"  [{label}] no output url")
        return
    try:
        download(out_url, dest)
        print(f"  [{label}] done -> {dest.relative_to(ROOT)}")
    except Exception as e:
        print(f"  [{label}] download err: {e}")


def main() -> None:
    jobs: list[tuple[str, str, Path, str]] = []
    for carousel_dir in sorted(ROOT.glob("almanac-*")):
        if not carousel_dir.is_dir():
            continue
        if CAROUSEL_FILTER and carousel_dir.name not in CAROUSEL_FILTER:
            continue
        prompts_path = carousel_dir / "prompts.json"
        if not prompts_path.exists():
            continue
        prompts = json.loads(prompts_path.read_text())
        slides = prompts.get("slides", {})
        for sid, sdef in slides.items():
            ill_dir = carousel_dir / "illustrations"
            ill_dir.mkdir(exist_ok=True)
            dest = ill_dir / f"{sid}.png"
            if dest.exists():
                continue
            jobs.append((carousel_dir.name, sid, dest, sdef["prompt"]))

    if not jobs:
        print("nothing to generate; all illustrations present")
        return

    print(f"queueing {len(jobs)} fresh generation(s) at {CREATE_SPACING_S}s spacing")
    threads: list[threading.Thread] = []
    for i, (carousel, sid, dest, prompt) in enumerate(jobs):
        label = f"{carousel}/{sid}"
        body = {
            "input": {
                "prompt": prompt,
                "aspect_ratio": "1:1",
                "resolution": "1K",
                "output_format": "png",
            }
        }
        try:
            res = json.loads(http_request(ENDPOINT, method="POST", body=body))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            print(f"[{label}] CREATE FAILED {e.code}: {err_body[:200]}")
            time.sleep(CREATE_SPACING_S)
            continue
        pid = res.get("id")
        get_url = res.get("urls", {}).get("get")
        if not pid or not get_url:
            print(f"[{label}] no prediction id/url in response: {res}")
            time.sleep(CREATE_SPACING_S)
            continue
        print(f"[{label}] created {pid}")
        t = threading.Thread(target=poll_and_download, args=(pid, get_url, dest, label))
        t.start()
        threads.append(t)
        if i < len(jobs) - 1:
            time.sleep(CREATE_SPACING_S)

    print("all creates posted; waiting for downloads...")
    for t in threads:
        t.join()
    print("batch complete")


if __name__ == "__main__":
    main()
