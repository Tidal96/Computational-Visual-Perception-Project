# Part 1 requirement-by-requirement check

Scope: the supplied `26_10_27_Project_Part1.pdf`, Tasks 1–3 of **Project Part 1**. Team: **Hadis Nouri, one student**. This does not claim completion of Project Parts 2 or 3, whose detailed briefs were not supplied.

| Requirement in the brief | Rebuilt implementation / evidence |
|---|---|
| Choose an idea | Face perception after loss of grayscale shading; approach slide 2 |
| Select/generate 100 suitable originals | 100 intact, hash-verified FFHQ PNGs at the provided 1024 × 1024 resolution; `dataset_manifest.json` |
| Write a GUI or CLI Mooney tool | `src/mooney_tool.py` and `src/mooney_gui.py` |
| Control blur strength | Gaussian sigma slider / `--sigma`, including no blur |
| Control percentage of white pixels | Percentage slider / `--white`; exact target count with logged deterministic boundary ties |
| Batch-process 100+ images | Actual 101-image batch run, checked for counts, dimensions and white-pixel targets; `batch101_log.txt` |
| Generate 100 good Mooney images | 100 full-resolution binary PNGs, all reproducible from logged settings; visual screening and final pair-board review performed |
| Manually select the top ten | Student viewed the ten-pair board and explicitly selected/confirmed IDs `022,016,046,052,082,010,028,051,084,003`; `manual_selection.json` |
| Select/install two vision systems | Official hash-verified Depth Anything V2 Small and CLIP ViT-B/32; `run_info.json` |
| Process every original with each system | 100 depth maps + visualizations and 100 CLIP JSONs |
| Process every Mooney with each system | 100 depth maps + visualizations and 100 CLIP JSONs |
| `Original/` folder | Exactly 100 PNGs |
| `Mooney/` folder | Exactly 100 PNGs |
| `Subset/Original/` and `Subset/Mooney/` | Exactly ten PNGs each; byte-identical to the corresponding full-set files |
| `Result1/Original/` and `Result1/Mooney/` | Every ID has a 16-bit depth PNG and an INFERNO JPEG |
| `Result2/Original/` and `Result2/Mooney/` | Every ID has eight CLIP scores, the top prompt and face-prompt share |
| One PowerPoint in the ZIP root | `CompVP_Part1_Hadis_Nouri.pptx`, 26 slides |
| Title and all team names | Slide 1, Hadis Nouri |
| One-page description of the approach | Slide 2 |
| One slide with ten originals + ten Mooneys | Slide 6, 20 pictures and the confirmed IDs |
| Declaration of vision systems | Slide 7, model IDs and preprocessing |
| Results for each vision system | Slides 8–12, actual computed figures including weaker examples |
| Screenshot showing the tool | Slide 3; actual running GUI captured in Chromium |
| Screenshot of Mooney generation code | Slide 4; actual source endpoint screenshot |
| Declaration of AI usage | Slide 15, explicit ChatGPT/Codex assistance and student subset decision |
| One ZIP with the required layout | 821 files total; automated coverage, checksums and CRC verification |

For an individual project, the supplied brief does **not** require four systems or rendering from 3D scenes. It does **not** prescribe a 1–5 image-rating scale. Same-photo 8AFC matching, correlations, galleries and detailed credits are additional documented analysis.

The automated checks establish completeness, reproducibility and numeric/file integrity. “Good Mooney images” and the instructor's final grading remain visual/academic judgments; this checklist is not a guarantee of a grade.
