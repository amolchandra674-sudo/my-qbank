#!/usr/bin/env python3
"""Reconstruct the original Corebtr Elite.html reference from numbered source parts."""
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARTS = HERE / "Corebtr Elite.html.parts"
OUTPUT = HERE / "Corebtr Elite.html"
EXPECTED_PARTS = 28
EXPECTED_CHARACTERS = 6_975_021
EXPECTED_SHA256 = "5288840455c6902ce46663a22f925f8077ee2758ab71ee01dd60984137e15ff5"


def main() -> None:
    parts = sorted(PARTS.glob("part-*.txt"))
    if len(parts) != EXPECTED_PARTS:
        raise SystemExit(f"Expected {EXPECTED_PARTS} parts, found {len(parts)}")

    chunks = []
    for expected_num, path in enumerate(parts, start=1):
        expected_name = f"part-{expected_num:03d}.txt"
        if path.name != expected_name:
            raise SystemExit(f"Unexpected or missing part; expected {expected_name}, got {path.name}")
        with path.open("r", encoding="utf-8", newline="") as stream:
            chunks.append(stream.read())

    content = "".join(chunks)
    if len(content) != EXPECTED_CHARACTERS:
        raise SystemExit(
            f"Unexpected reconstructed length: {len(content)} characters; "
            f"expected {EXPECTED_CHARACTERS}"
        )

    with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        stream.write(content)

    digest = sha256(OUTPUT.read_bytes()).hexdigest()
    print(f"Reconstructed {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")
    print(f"SHA-256: {digest}")
    if digest != EXPECTED_SHA256:
        raise SystemExit("Hash mismatch: reconstructed reference does not match the recorded source.")


if __name__ == "__main__":
    main()
