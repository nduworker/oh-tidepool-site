#!/usr/bin/env python3
"""Build the landing page's demo clips from a simulator recording.

    python3 scripts/build-demo-clips.py --scenario where --input where.mov
    python3 scripts/build-demo-clips.py --scenario where --input where.mov --check

One screen recording per scenario, produced in the private application
repository at the device's own resolution. The script trims the idle head and
tail of the recording, cuts the loop to the scenario's window, scales to twice
the figure's rendered width, and writes an H.264 clip plus its poster frame.

Video rather than GIF: the same eight seconds cost about 0.5 MB here against
2-3 MB as a GIF, and the motion stays at the recording's own frame rate instead
of being quantised to a palette. Nothing it writes is committed by CI; it is an
authoring tool.

`--check` reports the trim without writing.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parent.parent

# Per scenario, because a scroll and a tap read at different speeds. `window_s`
# is the longest slice of the recording the loop may use, and `target_mb` the
# ceiling the page is allowed to spend on it. A recording may run longer than
# the window: the script cuts the loop to the window, which is what keeps the
# page inside its budget.
#
# `anchor` says which end of the movement the window keeps. These recordings come
# from a harness that asserts the screen it needs before it stops, so the payoff
# is at the end of the run: the map selected, the day's guidance present, the tip
# sheet open. Anchoring at the end keeps that and the seconds that lead to it.
#
# `start_s` pins a window to a moment a script cannot detect, such as the row a
# swipe starts from; `poster_at` picks the frame shown before the clip plays, as
# a fraction of the loop. Both were read off the 29 September captures with
# `tesseract` and need checking against a new recording.
SCENARIOS: dict[str, dict[str, object]] = {
    "where": {
        "anchor": "end",
        "window_s": 14.0,
        "hold_s": 1.0,
        "poster_at": 0.85,
        "target_mb": 1.4,
        "what": "The Explore list scrolled, then the same sites on the map",
    },
    "when": {
        "anchor": "end",
        "start_s": 57.5,
        "window_s": 16.0,
        "hold_s": 1.0,
        "target_mb": 1.2,
        "what": "A site page: the day's guidance, hazard bullets, tide and surf",
    },
    "what": {
        "anchor": "end",
        "window_s": 8.0,
        "poster_at": 0.5,
        "hold_s": 1.0,
        "target_mb": 0.8,
        "what": "A discovery site: estimated guidance and what to expect",
    },
    "tips": {
        "anchor": "end",
        "start_s": 19.0,
        "window_s": 14.0,
        "hold_s": 1.0,
        "poster_at": 0.85,
        "target_mb": 1.0,
        "what": "The tip row in the Explore header: swipe on, swipe back, tap to open",
    },
}

# Twice the 300px the figure is rendered at, so the clip stays sharp on a phone
# screen without paying for the recording's full device resolution.
WIDTH = 600
CRF = 30
SAMPLE_FPS = 4  # rate at which the recording is sampled to find the movement
CHANGE_THRESHOLD = 1.2  # mean per-pixel difference that counts as movement
HEAD_GRACE_S = 0.3  # keep a little run-up before the first change
TAIL_GRACE_S = 0.4  # and a little settle after the last one


class BuildError(RuntimeError):
    pass


def run(*command: str) -> str:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise BuildError(f"{' '.join(command[:3])}… failed:\n{result.stderr.strip()[-2000:]}")
    return result.stdout


def probe(source: Path) -> tuple[float, float, int]:
    """Duration in seconds, frame rate, and source width."""
    raw = run(
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,avg_frame_rate:format=duration",
        "-of", "json", str(source),
    )
    data = json.loads(raw)
    stream = data["streams"][0]
    numerator, _, denominator = stream["avg_frame_rate"].partition("/")
    fps = float(numerator) / float(denominator or 1)
    return float(data["format"]["duration"]), fps, int(stream["width"])


def movement_span(source: Path, samples: Path) -> tuple[float, float]:
    """Seconds of the first and last sampled frame that differ from the previous."""
    samples.mkdir(parents=True, exist_ok=True)
    run(
        "ffmpeg", "-y", "-v", "error", "-i", str(source),
        "-vf", f"fps={SAMPLE_FPS},scale=90:-2:flags=lanczos",
        "-pix_fmt", "gray", str(samples / "%05d.png"),
    )
    frames = sorted(samples.glob("*.png"))
    if not frames:
        raise BuildError("the recording produced no frames")

    previous: Image.Image | None = None
    first: int | None = None
    last = 0
    for index, path in enumerate(frames):
        thumb = Image.open(path)
        if previous is not None:
            difference = ImageStat.Stat(ImageChops.difference(thumb, previous)).mean[0]
            if difference >= CHANGE_THRESHOLD:
                if first is None:
                    first = max(index - 1, 0)
                last = index
        previous = thumb
    return (first or 0) / SAMPLE_FPS, last / SAMPLE_FPS


def build(scenario: str, source: Path, check_only: bool,
          window_override: float | None = None, hold_override: float | None = None,
          start_override: float | None = None) -> dict[str, object]:
    settings = SCENARIOS[scenario]
    window = float(settings["window_s"]) if window_override is None else window_override
    hold = float(settings["hold_s"]) if hold_override is None else hold_override
    anchor = str(settings["anchor"])
    pinned_start = settings.get("start_s")
    poster_at = float(settings.get("poster_at", 0.5))
    target_bytes = int(float(settings["target_mb"]) * 1024 * 1024)
    clip = ROOT / "demo" / f"{scenario}.mp4"
    poster = ROOT / "demo" / f"{scenario}-poster.jpg"

    with tempfile.TemporaryDirectory(prefix=f"demo-{scenario}-") as workspace:
        duration, source_fps, source_width = probe(source)
        start, end = movement_span(source, Path(workspace) / "samples")
        start = max(0.0, start - HEAD_GRACE_S)
        end = min(duration, end + TAIL_GRACE_S)
        if window > 0:
            if start_override is not None:
                start = max(0.0, start_override)
                end = min(duration, start + window)
            elif pinned_start is not None:
                start = max(0.0, float(pinned_start))
                end = min(duration, start + window)
            elif anchor == "end":
                start = max(0.0, end - window)
            else:
                end = min(end, start + window)
        length = max(0.5, end - start)
        report = {
            "scenario": scenario,
            "source": str(source),
            "source_s": round(duration, 2),
            "source_fps": round(source_fps, 1),
            "source_width": source_width,
            "start_s": round(start, 2),
            "loop_s": round(length + hold, 2),
            "trimmed_s": round(length, 2),
            "window_s": window,
            "width": min(WIDTH, source_width),
            "output": str(clip.relative_to(ROOT)),
            "poster": str(poster.relative_to(ROOT)),
        }
        if check_only:
            return report

        clip.parent.mkdir(parents=True, exist_ok=True)
        scale = f"scale='min({WIDTH},iw)':-2:flags=lanczos"
        fresh_clip = Path(workspace) / "clip.mp4"
        fresh_poster = Path(workspace) / "poster.jpg"
        run(
            "ffmpeg", "-y", "-v", "error",
            "-ss", f"{start:.3f}", "-t", f"{length + hold:.3f}", "-i", str(source),
            "-vf", scale, "-c:v", "libx264", "-preset", "slow", "-crf", str(CRF),
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(fresh_clip),
        )
        run(
            "ffmpeg", "-y", "-v", "error",
            "-ss", f"{start + length * poster_at:.3f}", "-i", str(source),
            "-vf", scale, "-frames:v", "1", "-q:v", "4", str(fresh_poster),
        )
        # A clip over budget is not left in demo/: the previous one stays until a
        # build fits, so a failed run never leaves the page heavier than before.
        size = fresh_clip.stat().st_size
        report["bytes"] = size
        report["poster_bytes"] = fresh_poster.stat().st_size
        report["target_bytes"] = target_bytes
        report["over_budget"] = size > target_bytes
        if not report["over_budget"]:
            fresh_clip.replace(clip)
            fresh_poster.replace(poster)

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scenario", required=True, choices=sorted(SCENARIOS))
    parser.add_argument("--input", required=True, type=Path, help="screen recording (.mov, .mp4 or .gif)")
    parser.add_argument("--check", action="store_true", help="report the build without writing the clip")
    parser.add_argument("--window-seconds", type=float, default=None,
                        help="override the scenario's window; 0 keeps the whole capture")
    parser.add_argument("--hold-seconds", type=float, default=None,
                        help="override the scenario's final hold")
    parser.add_argument("--start-seconds", type=float, default=None,
                        help="start the window at this second of the recording")
    arguments = parser.parse_args()

    if not arguments.input.exists():
        print(f"build-demo-clips: no such recording: {arguments.input}", file=sys.stderr)
        return 2
    try:
        report = build(arguments.scenario, arguments.input, arguments.check,
                       arguments.window_seconds, arguments.hold_seconds, arguments.start_seconds)
    except BuildError as error:
        print(f"build-demo-clips: {error}", file=sys.stderr)
        return 1

    print(f"{report['scenario']}: {SCENARIOS[report['scenario']]['what']}")
    print(f"  recording {report['source_s']}s at {report['source_fps']} fps, "
          f"{report['source_width']}px wide")
    print(f"  trim {report['start_s']}s to {round(report['start_s'] + report['trimmed_s'], 2)}s, "
          f"loop {report['loop_s']}s at {report['width']}px wide")
    if "bytes" in report:
        budget = report["target_bytes"] / 1024 / 1024
        megabytes = report["bytes"] / 1024 / 1024
        if report["over_budget"]:
            print(f"  built {megabytes:.2f} MB and {report['poster_bytes'] / 1024:.0f} KB, "
                  f"over the {budget:.2f} MB budget; {report['output']} is untouched",
                  file=sys.stderr)
            print("  record a shorter run or trim the scenario's window", file=sys.stderr)
            return 1
        print(f"  wrote {report['output']} at {megabytes:.2f} MB "
              f"and {report['poster']} at {report['poster_bytes'] / 1024:.0f} KB "
              f"(budget {budget:.2f} MB)")
    else:
        print(f"  would write {report['output']} and {report['poster']} (check only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
