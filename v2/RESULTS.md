# Rebuild results and verification

Canonical run: [Kaggle, version 2](https://www.kaggle.com/code/mantra26/compvp-part1-high-resolution-rebuild), completed 8 November 2026. The notebook's **Output** tab contains the final course-submission ZIP. The version-2 outputs were downloaded and checked locally.

## Task 1 — source images

100 intact FFHQ photographs at the provided 1024 × 1024 resolution. All 100 file MD5s and pixel MD5s match the official NVlabs FFHQ metadata, in addition to SHA-256 verification against the pinned mirror. All individual photo credits and licenses are in `analysis/ATTRIBUTION.csv` and the presentation appendix.

## Task 2 — generation and manual subset

100 binary Mooney PNGs, generated with sigma 8 px, kernel 49 and a per-image 22% or 28% white-pixel target. The tool controls were exercised in nine combinations; a real 101-image batch and GUI interactions passed. The student viewed and confirmed IDs **022, 016, 046, 052, 082, 010, 028, 051, 084, 003**. All 20 subset files match their full-set counterparts byte for byte.

## Task 3 — actual model outputs

| CLIP measure | Original (100) | Mooney (100) |
|---|---:|---:|
| Mean combined face-prompt share | 0.836379 | 0.913056 |
| Top-ranked prompt describes a face | 99/100 | 99/100 |

The score is a softmax share relative to the eight selected prompts. The set includes a specifically black-and-white face prompt; the higher Mooney share is not evidence of higher general recognition accuracy.

Depth-map mean paired Pearson correlation: **0.484441**. Cyclic next-image control: **0.284417**. Paired correlation exceeds the control for **79/100** images. There is no ground-truth depth; these measure output consistency.

| Same-photo 8AFC matching | Original → Mooney | Mooney → Original |
|---|---:|---:|
| CLIP embeddings | 57/100 | 43/100 |
| Depth-map representation | 39/100 | 37/100 |

Chance is 12.5%. One common saved gallery design, shuffled positions and seed 0 are used for both systems and directions. This is not Paper 1's cross-pose identity or human experiment. Trial scores, galleries and Wilson intervals are included in the analysis bundle.

## Reproducibility and delivery

- All 821 submission-file checksums and archive CRC passed after download.
- All 100 source photographs are identical in local and Kaggle runs.
- Every Mooney pixel is identical in the local and Kaggle runs.
- Maximum absolute CLIP prompt-share difference between the two platforms: 0.000002683. All reported matching counts and category top-1 counts agree.
- All 200 depth outputs are finite and nonconstant; all 200 CLIP JSON files contain complete scores for the same eight prompts.
- The PowerPoint has 26 slides and the 20 selected images on one slide. It was also rendered to PDF and visually inspected.
- The source ZIP contains all eight Python modules, configuration/provenance tables, actual results, embeddings, trial details, plots and tool screenshots. The Kaggle notebook is also committed separately.

Execution environment: Python 3.13.18, PyTorch 2.11.0+cpu, Transformers 5.20.2, NumPy 2.1.3, OpenCV 4.14.0, CPU. Both official model checkpoints and processor/tokenizer configurations were hash-verified. Full metadata: `analysis/run_info.json`.

Submission ZIP: **434,078,276 bytes** (about 414 MiB).

SHA-256: `34b3bff221d3856d6602752aa0421cc9fd88bc9740aa2deb20524c90e6c19199`

MD5: `78960fc2a70d6a7d13af9997e9a9ec9c`

This covers Tasks 1–3 of Project Part 1 in the supplied brief for a one-person team. Visual quality and the instructor's grading remain academic judgments; no automated check can guarantee a grade.
