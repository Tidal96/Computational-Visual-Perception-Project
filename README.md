# Computational Visual Perception — Part 1

Source retrieved from the owner's Kaggle notebook `mantra26/compvp-part1-mooney` on 7 November 2026.

## Files

- `mooney_tool.py`: the original standalone image-to-Mooney command-line tool.
- `compvp_part1.ipynb`: the original project workflow, with saved outputs cleared.
- `requirements.txt`: core versions from the successful Kaggle environment and other notebook dependencies.

The workflow selects 100 LFW face images, generates paired Mooney images, runs Depth Anything V2 Small and CLIP ViT-B/32, evaluates the results and packages the generated artifacts. The ten-image subset is manually selected through the `SUBSET` setting.

## Run the standalone tool

Install NumPy and OpenCV, then run:

```sh
python mooney_tool.py Original/ Mooney/ --white 30 --blur-rel 0.04 --sigma 35 --log analysis/mooney_params.csv
```

Use `python mooney_tool.py --help` for blur, white-percentage, inversion and logging controls. Input can be one image or a directory of images.

## Run the full notebook on Kaggle

Import `compvp_part1.ipynb` and attach these inputs:

- Dataset: `jessicali9530/lfw-dataset`
- Dataset: `singhaltarun/openaiclip-vit-base-patch32`
- Model: `itsraininnnn/depth-anything-v2-small-hf/Transformers/default/1`

The notebook runs offline on CPU and checks the attached model files against the official release hashes before loading them. It writes `part1_output.zip` under `/kaggle/working`, including images, results, analysis files and `code/mooney_tool.py`. The assignment presentation is prepared separately.

## Evaluation definitions

- The mismatched depth control pairs original image i with Mooney image (i+1) modulo 100. Its mean correlation is approximately 0.33212.
- Depth matching resizes raw depth maps to 64 by 64, subtracts the per-image mean, and normalizes each vector. Seven distractors are sampled using `numpy.random.default_rng(0)` for each probe. The reported matching counts are 34/100 in both directions.
- CLIP uses eight text prompts and the sum of the two face-prompt softmax scores. Its matching counts are 42/100 original-to-Mooney and 22/100 in reverse.
- Matching uses two versions of the same photograph. It is not the cross-pose task used in the reference Mooney paper. Depth correlation measures output consistency; it is not a measurement of physical depth accuracy.

## Verification provenance

An additional private Kaggle verification run was prepared at:
https://www.kaggle.com/code/mantra26/compvp-part1-verification-20261107

It retains the original project calculations and adds a 101-image CLI batch check plus checks of the white-percentage and blur controls. The Kaggle rerun completed successfully: all 12 original checks passed, the 101-image CLI batch passed, and all nine tested white-percentage/blur settings passed. All 820 dataset/result files match the submitted ZIP byte-for-byte. The standalone original tool also passed the same batch/control checks locally. Credentials are supplied through the authenticated API session and are never part of these source files.
