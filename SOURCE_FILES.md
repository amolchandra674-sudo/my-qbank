# Source and release artifact manifest

## Last-working standalone release

- File: `QBank_self_contained.html`
- Uncompressed size: 348,487,764 bytes (about 332 MiB)
- SHA-256: `1440f928a49418b32dd52558a52f4428d1206aee9152bf8f244e571b806d35bb`
- Questions: 5,131 unique question IDs
- ZIP: `QBank_self_contained_HTML.zip`, 252,773,842 bytes
- ZIP SHA-256: `f78ec248919e3d05d8b4c2a1b67b495b10fc096f84adb672d8a99295cd0b42df`
- The ZIP passed integrity testing and contains exactly one file, `QBank_self_contained.html`.

The standalone HTML is too large for an ordinary GitHub file (GitHub's standard per-file limit is 100 MB), so it is not stored in this repository. Keep this artifact and the ZIP in durable external storage; the hashes identify the exact copies checked during cleanup.

## Source PDF parts required for regeneration

These source parts were available in the working files during cleanup, but **are not committed to this Git repository**. Save verified copies under `source-pdfs/` before attempting a fresh regeneration. The checksums identify the expected source copies.

| File | Size in bytes | SHA-256 |
|---|---:|---|
| `SplitPDFFile_1_to_2000.pdf` | 69,751,238 | `81edc9643843a3c2b5b9c0555d00fb090ab366bcb316f8e8cf076c6e54b2a01d` |
| `SplitPDFFile_2001_to_4000.pdf` | 79,290,111 | `11af9a8848a73e800601a068041bee55bfa3fbfa7d5e2024c2d62b9337731c3c` |
| `SplitPDFFile_4001_to_6322.pdf` | 70,136,228 | `9e888a2a93ece5303ff706e796084594bb9406c1a99ca0c3e66624a0abf4ac17` |

The merged source PDF previously used was named `qbank_merged_6322.pdf` (about 219.7 MB). It is also not committed here. The three parts above can be merged in their numbered order using `merge_qbank_pdfs.py`.

## Data preserved in GitHub

- The HTML site file is retained as `index.html`.
- All 5,509 existing question/explanation image blobs are retained under `img/`.
- The repository notes report 5,131 questions and 5,509 images. The standalone release was independently checked to contain 5,131 unique question IDs.

## Important reproducibility note

The GitHub repository does not yet contain the binary source PDFs or the 332 MiB single-file release. A clone can open the committed web build immediately, but a clean regeneration needs verified copies of the source PDF parts. Keep those source inputs and the standalone release in durable external storage before deleting the copies held in the working files.
