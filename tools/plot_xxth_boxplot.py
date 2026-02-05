#!/usr/bin/env python3
"""Extract xxth/期間 columns from a table image and plot a boxplot."""
from __future__ import annotations

import argparse
import difflib
import os
import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pytesseract


@dataclass
class TableExtractionResult:
    headers: List[str]
    rows: List[List[str]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract xxth/期間 columns from a table image using OCR and plot a boxplot."
        )
    )
    parser.add_argument("input", help="Path to input image (PNG/JPG).")
    parser.add_argument(
        "output", help="Path to output image file (e.g. output/xxth_period_boxplot.png)."
    )
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.6,
        help="Minimum similarity for fuzzy header match.",
    )
    parser.add_argument(
        "--tesseract-lang",
        default="jpn+eng",
        help="Languages for Tesseract OCR.",
    )
    return parser.parse_args()


def normalize_header(text: str) -> str:
    return re.sub(r"[^\w]", "", text.lower())


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def select_column(headers: Sequence[str], target: str, min_similarity: float) -> int:
    normalized_headers = [normalize_header(h) for h in headers]
    normalized_target = normalize_header(target)
    scores = [similarity(h, normalized_target) for h in normalized_headers]
    best_idx = int(np.argmax(scores)) if scores else -1
    if best_idx == -1 or scores[best_idx] < min_similarity:
        raise ValueError(
            f"Header '{target}' not found. Best match '{headers[best_idx] if best_idx >= 0 else ''}'"
        )
    return best_idx


def extract_numeric_prefix(value: str) -> int | None:
    match = re.match(r"^(\d+)", value.strip())
    return int(match.group(1)) if match else None


def parse_period(value: str) -> float | None:
    cleaned = re.sub(r"[^0-9.\-]", "", value)
    try:
        return float(cleaned)
    except ValueError:
        return None


def sort_rows_by_xxth(rows: Iterable[Tuple[str, float]]) -> List[Tuple[str, float]]:
    def sort_key(item: Tuple[str, float]) -> Tuple[int, str]:
        num = extract_numeric_prefix(item[0])
        return (num if num is not None else 1_000_000, item[0])

    return sorted(rows, key=sort_key)


def read_image(path: str) -> np.ndarray:
    image = cv2.imread(path)
    if image is None:
        raise FileNotFoundError(f"Unable to read image: {path}")
    return image


def detect_table_cells(image: np.ndarray) -> List[Tuple[int, int, int, int, np.ndarray]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 4
    )

    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))

    horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)
    vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel)

    table_mask = cv2.add(horizontal_lines, vertical_lines)
    contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    cells = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < 20 or h < 20:
            continue
        cell = image[y : y + h, x : x + w]
        cells.append((x, y, w, h, cell))

    return sorted(cells, key=lambda c: (c[1], c[0]))


def group_cells_into_rows(
    cells: Sequence[Tuple[int, int, int, int, np.ndarray]],
) -> List[List[np.ndarray]]:
    if not cells:
        return []

    heights = [h for _, _, _, h, _ in cells]
    row_threshold = int(np.median(heights) * 0.8)

    rows: List[List[np.ndarray]] = []
    current_row: List[np.ndarray] = []
    last_y = None

    for x, y, w, h, cell in cells:
        if last_y is None:
            current_row = [cell]
            last_y = y
            continue
        if y is not None and last_y is not None and abs(y - last_y) > row_threshold:
            rows.append(current_row)
            current_row = [cell]
            last_y = y
        else:
            current_row.append(cell)
    if current_row:
        rows.append(current_row)

    return rows


def ocr_cell(cell: np.ndarray, lang: str) -> str:
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    config = "--psm 6"
    return pytesseract.image_to_string(thresh, lang=lang, config=config).strip()


def extract_table(image: np.ndarray, lang: str) -> TableExtractionResult:
    cells = detect_table_cells(image)
    if not cells:
        raise ValueError("No table cells detected. Ensure the image has visible grid lines.")

    rows = group_cells_into_rows(cells)
    table_rows: List[List[str]] = []
    for row in rows:
        texts = [ocr_cell(cell, lang) for cell in row]
        table_rows.append(texts)

    headers = table_rows[0]
    data_rows = table_rows[1:]
    return TableExtractionResult(headers=headers, rows=data_rows)


def create_boxplot(xxth_values: Sequence[str], period_values: Sequence[float], output: str) -> None:
    grouped: dict[str, List[float]] = {}
    for xxth, period in zip(xxth_values, period_values):
        grouped.setdefault(xxth, []).append(period)

    sorted_items = sort_rows_by_xxth([(xxth, 0.0) for xxth in grouped.keys()])
    labels = [item[0] for item in sorted_items]
    data = [grouped[label] for label in labels]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot(data, labels=labels, patch_artist=True, boxprops={"facecolor": "green"})
    ax.set_xlabel("xxth")
    ax.set_ylabel("期間")
    ax.set_title("xxth vs 期間 Boxplot")
    fig.tight_layout()

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    image = read_image(args.input)
    result = extract_table(image, args.tesseract_lang)

    xxth_idx = select_column(result.headers, "xxth", args.min_similarity)
    period_idx = select_column(result.headers, "期間", args.min_similarity)

    xxth_values: List[str] = []
    period_values: List[float] = []

    for row in result.rows:
        if xxth_idx >= len(row) or period_idx >= len(row):
            continue
        xxth = row[xxth_idx]
        period = parse_period(row[period_idx])
        if period is None:
            continue
        xxth_values.append(xxth)
        period_values.append(period)

    if not xxth_values:
        raise ValueError("No valid data extracted for xxth/期間 columns.")

    create_boxplot(xxth_values, period_values, args.output)


if __name__ == "__main__":
    main()
