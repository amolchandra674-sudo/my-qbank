#!/usr/bin/env python3
"""Merge the numbered QBank PDF parts into qbank_merged_6322.pdf."""
import argparse
from pathlib import Path
from pypdf import PdfReader, PdfWriter

PARTS = (
    "SplitPDFFile_1_to_2000.pdf",
    "SplitPDFFile_2001_to_4000.pdf",
    "SplitPDFFile_4001_to_6322.pdf",
)
EXPECTED_PAGES = 6322


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", nargs="?", default="source-pdfs",
                        help="directory containing the three numbered source PDF parts")
    parser.add_argument("output", nargs="?", default="qbank_merged_6322.pdf",
                        help="merged output PDF path")
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    output = Path(args.output)
    missing = [name for name in PARTS if not (source_dir / name).is_file()]
    if missing:
        raise SystemExit("Missing source PDF part(s): " + ", ".join(missing))

    writer = PdfWriter()
    total_pages = 0
    for name in PARTS:
        path = source_dir / name
        reader = PdfReader(str(path), strict=False)
        pages = len(reader.pages)
        print(f"{name}: {pages} pages")
        total_pages += pages
        writer.append(reader)

    if total_pages != EXPECTED_PAGES:
        raise SystemExit(
            f"Expected {EXPECTED_PAGES} source pages, found {total_pages}; "
            "refusing to write a merged PDF."
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        writer.write(handle)

    merged_pages = len(PdfReader(str(output), strict=False).pages)
    if merged_pages != EXPECTED_PAGES:
        raise SystemExit(f"Merge validation failed: output has {merged_pages} pages.")
    print(f"Validated {merged_pages} pages -> {output}")


if __name__ == "__main__":
    main()
