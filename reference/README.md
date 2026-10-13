# Preserved reference HTML

The original reference was `Corebtr Elite.html` (7,044,945 bytes; SHA-256 `5288840455c6902ce46663a22f925f8077ee2758ab71ee01dd60984137e15ff5`). The GitHub connector could not send this 7 MB file as one request, so its exact text is preserved in numbered parts under `Corebtr Elite.html.parts/`.

To reconstruct the ordinary HTML file, run:

```sh
python reference/restore_reference.py
```

The script concatenates the parts in numeric order, checks the expected character count and SHA-256, and writes `reference/Corebtr Elite.html`.
