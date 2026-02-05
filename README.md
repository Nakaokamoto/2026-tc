# Table OCR Boxplot Tool

This repository provides a CLI tool for extracting `xxth` and `期間` columns from a table image using OCR and table-structure detection, then plotting a boxplot.

## Overview

The workflow uses:

- **OpenCV** to detect table grid lines and segment cell regions.
- **Tesseract OCR (`pytesseract`)** to recognize text in each cell.
- **Fuzzy header matching** to locate the `xxth` and `期間` columns, even with minor OCR mistakes.
- **Matplotlib** to render a boxplot with green box fills.

## Usage

```bash
python tools/plot_xxth_boxplot.py \
  path/to/input_table.png \
  output/xxth_period_boxplot.png
```

Optional arguments:

```bash
python tools/plot_xxth_boxplot.py \
  path/to/input_table.png \
  output/xxth_period_boxplot.png \
  --min-similarity 0.7 \
  --tesseract-lang jpn+eng
```

## Expected Input & Output

### Sample input image (example)

A PNG/JPG containing a table with headers similar to:

| xxth | 期間 | ... |
| ---- | ---- | --- |
| 7th_CR | 12 | ... |
| 8th_CR | 9 | ... |

### Expected output

The tool creates a boxplot where:

- **X-axis**: `xxth` (sorted by the leading number, e.g., 7th, 8th, 9th, ...).
- **Y-axis**: `期間` numeric values (non-numeric or missing values are ignored).
- **Box fill color**: green.

The output image is saved to the path you specify (e.g. `output/xxth_period_boxplot.png`).
