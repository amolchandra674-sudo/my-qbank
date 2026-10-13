# My QBank — HTML-first project

This repository is the **HTML QBank**, not an Android project.

## Open the QBank

Open `index.html` in a modern browser. Keep the `img/` folder beside it; question data is stored in the HTML and referenced question/explanation images are stored in `img/`.

## Current authority

The last-working, single-file delivery is `QBank_self_contained.html` (5,131 questions; 348,487,764 bytes; SHA-256 recorded in [SOURCE_FILES.md](SOURCE_FILES.md)). Its ZIP delivery contains only that HTML file and passed ZIP integrity testing. GitHub rejects ordinary files larger than 100 MB, so the 332 MiB standalone HTML is intentionally not committed here.

For everyday use and source control, this repository keeps the smaller **HTML + image-folder** form. The current site HTML and 5,509 image assets are retained from the previous Android asset directory without re-encoding the existing Git image blobs.

## Regenerate from the source PDFs

1. Install Python and the [Tesseract OCR engine](https://github.com/tesseract-ocr/tesseract).
2. Install Python packages: `python -m pip install -r requirements.txt`.
3. Put the three source PDF parts listed in [SOURCE_FILES.md](SOURCE_FILES.md) into `source-pdfs/`.
4. Merge them: `python merge_qbank_pdfs.py source-pdfs qbank_merged_6322.pdf`.
5. Generate the web build: `python pdf2qbank-3.py qbank_merged_6322.pdf -o out --name "My QBank"`.
6. For a single self-contained HTML file, add `--embed` to the generator command. This produces a very large file; use the ordinary HTML + `img/` output when developing the site.

`pdf2qbank-3.py` is the latest retained generator. It omits questions with broken option/answer data by default and writes a review report. `template.html` is its generation template. The original `Corebtr Elite.html` design/reference is preserved as 28 numbered text parts under `reference/Corebtr Elite.html.parts/`; reconstruct it with `python reference/restore_reference.py`. It is not the current generated QBank.

## Repository hygiene

Android/Gradle files and the APK-build workflow are removed from this HTML-first branch. Generated OCR cache, local source PDFs, merged PDFs, and output bundles are ignored by Git so they are not accidentally committed.
