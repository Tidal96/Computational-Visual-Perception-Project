# Computational Visual Perception — Part 1 (rebuilt)

Author: **Hadis Nouri**, individual project. This rebuild covers **Task 1, Task 2 and Task 3 of Project Part 1** in the supplied assignment brief.

## Download the completed rebuild

- **Course submission ZIP:** [Kaggle Output](https://www.kaggle.com/code/mantra26/compvp-part1-high-resolution-rebuild/output). Sign in as `mantra26` and download **CompVP_Part1_Hadis_Nouri.zip**. The notebook and its input dataset are private.
- [Download PowerPoint from Kaggle Output](https://www.kaggle.com/code/mantra26/compvp-part1-high-resolution-rebuild/output) — file: `CompVP_Part1_Hadis_Nouri.pptx`
- [View/download presentation PDF](https://raw.githubusercontent.com/Tidal96/Computational-Visual-Perception-Project/main/v2/deliverables/CompVP_Part1_Hadis_Nouri.pdf)
- [Download source and analysis ZIP](https://raw.githubusercontent.com/Tidal96/Computational-Visual-Perception-Project/main/v2/deliverables/CompVP_Part1_Source_Analysis.zip)
- [Requirement-by-requirement checklist](REQUIREMENTS_CHECKLIST.md) · [Results and verification](RESULTS.md)

Kaggle execution: **COMPLETE**, version 2. The downloaded submission ZIP passed CRC, SHA-256 and all 821 per-file checksum checks. Only the course submission ZIP is intended for StudOn; the companion ZIP is for reproducibility.

## Deliverables

- 100 FFHQ photographs and 100 binary Mooney PNGs, all supplied/exported at 1024 × 1024.
- The student's confirmed ten-pair subset: `022, 016, 046, 052, 082, 010, 028, 051, 084, 003`.
- Depth Anything V2 Small outputs for all 200 images: relative-depth 16-bit PNG + INFERNO JPEG per image.
- CLIP ViT-B/32 outputs for all 200 images: eight prompt scores, top prompt and combined face-prompt share per image.
- One 26-slide PowerPoint with approach, subset, models, results, actual tool/source screenshots, AI declaration and individual photograph credits.

The submission ZIP has exactly the folder structure required by the course. Source and analysis are supplied separately. The old root-level notebook/results belong to the previous LFW version; use this `v2` directory for the high-resolution rebuild.

## View the images

[100-pair review boards](review/README.md). [The student's confirmed ten pairs](review/suggested_10_pairs.jpg).

The boards are resized previews. Original and Mooney files in the submission ZIP retain 1024 × 1024 dimensions.

## Run the tool

```bash
python -m pip install -r requirements.txt
python src/mooney_tool.py Original/ Mooney/ --white 28 --sigma 8 --log params.csv
python src/mooney_tool.py Original/ Mooney/ --params analysis/settings.csv --log actual.csv
python src/mooney_gui.py --original Original/ --settings analysis/settings.csv
```

Open `http://127.0.0.1:8765` for the local GUI. Both controls operate on full-resolution images. The CLI accepts one image or a batch of any size. A 101-image batch and nine combinations of the two controls were checked.

## Reproduce the whole project

```bash
python src/reproduce_project.py --project-root . --output run
```

This downloads the 100 source files at a pinned mirror revision and checks every SHA-256 hash; generates Mooneys; runs both models; recomputes statistics and shared 8AFC galleries; builds slides; verifies all 821 required submission files; and creates the submission and source/analysis ZIPs. A new output directory is required to prevent mixing runs. Model weights/configs are pinned and hash-verified. Optional `--original`, `--depth-model` and `--clip-model` arguments allow local inputs. The included Kaggle notebook runs from a private input archive with attached, verified model copies.

`requirements.txt` describes the tested local stack's compatible dependencies. The exact execution versions, processors, weight files and hashes for each completed run are recorded in `analysis/run_info.json`; Kaggle uses its supplied environment and bundled PowerPoint wheels.

## Methods and interpretation

FFHQ provides aligned 1024 × 1024 exports. This project preserves their PNG bytes. After model-independent illumination/background screening of 512 candidates, the assistant visually reviewed 150 pairs and included 100. The student viewed and explicitly confirmed the proposed ten-pair board. Mooneys are grayscale + Gaussian blur (sigma 8 px, kernel 49) + a global threshold targeting 22% or 28% white pixels; deterministic handling of threshold ties is logged. No model predictions were used to choose stimuli. No generative-image model was used.

Depth-map Pearson correlations measure **consistency**, because no ground-truth depth is available. CLIP's face score is a **relative softmax share among eight prompts**, not a calibrated probability. Eight-alternative matching compares an original and a Mooney of the **same photograph**; it is not Paper 1's cross-pose identity test or a human comparison. Saved gallery positions are shuffled and identical across systems/directions, with seed 0. Binomial p values are descriptive because images are reused.

## Credits and AI disclosure

See [all photograph credits and licenses](analysis/ATTRIBUTION.md), also reproduced in the PowerPoint appendix. FFHQ exports retain their individual photo licenses; Mooney transformations and resized preview boards are derivatives. FFHQ collection terms: https://github.com/NVlabs/ffhq-dataset/blob/master/LICENSE.txt.

ChatGPT/Codex assisted with reading, coding, visual source screening, transformation parameters, execution, analysis, figures, presentation and validation. Hadis Nouri selected the final ten pairs by reviewing and confirming their board. No invented human 1–5 ratings are reported; that scale is not required by the supplied brief.

Automated verification establishes file completeness, reproducibility and numerical integrity. Visual quality and the instructor's final assessment remain judgment calls. This is a Part 1 submission; detailed briefs for Project Parts 2 and 3 were not supplied.
