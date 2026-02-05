#!/usr/bin/env python3

"""Extract xxth/期間 columns from an Excel file and plot a boxplot."""

from __future__ import annotations

import argparse
import difflib
import os
import re

from typing import Iterable, List, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(

            "Extract xxth/期間 columns from an Excel file and plot a boxplot."
        )
    )
    parser.add_argument("input", help="Path to input Excel file (.xlsx/.xls).")

    parser.add_argument(
        "output", help="Path to output image file (e.g. output/xxth_period_boxplot.png)."
    )
    parser.add_argument(

        "--sheet",
        default=None,
        help="Excel sheet name or index (default: first sheet).",
    )
    parser.add_argument(

        "--min-similarity",
        type=float,
        default=0.6,
        help="Minimum similarity for fuzzy header match.",
    )


    return parser.parse_args()


def normalize_header(text: str) -> str:
    return re.sub(r"[^\w]", "", text.lower())


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()



def select_column(headers: Sequence[str], target: str, min_similarity: float) -> str:

    normalized_headers = [normalize_header(h) for h in headers]
    normalized_target = normalize_header(target)
    scores = [similarity(h, normalized_target) for h in normalized_headers]
    best_idx = int(np.argmax(scores)) if scores else -1
    if best_idx == -1 or scores[best_idx] < min_similarity:

        best_match = headers[best_idx] if best_idx >= 0 else ""
        raise ValueError(f"Header '{target}' not found. Best match '{best_match}'")
    return headers[best_idx]


def extract_numeric_prefix(value: str) -> int | None:
    match = re.match(r"^(\d+)", str(value).strip())
    return int(match.group(1)) if match else None


def parse_period(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^0-9.\-]", "", str(value))

    try:
        return float(cleaned)
    except ValueError:
        return None


def sort_rows_by_xxth(rows: Iterable[Tuple[str, float]]) -> List[Tuple[str, float]]:
    def sort_key(item: Tuple[str, float]) -> Tuple[int, str]:
        num = extract_numeric_prefix(item[0])
        return (num if num is not None else 1_000_000, item[0])

    return sorted(rows, key=sort_key)



def load_excel(path: str, sheet: str | None) -> pd.DataFrame:
    sheet_name = None
    if sheet is not None:
        try:
            sheet_name = int(sheet)
        except ValueError:
            sheet_name = sheet
    return pd.read_excel(path, sheet_name=sheet_name)



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

    df = load_excel(args.input, args.sheet)

    headers = [str(col) for col in df.columns]
    xxth_col = select_column(headers, "xxth", args.min_similarity)
    period_col = select_column(headers, "期間", args.min_similarity)


    xxth_values: List[str] = []
    period_values: List[float] = []


    for _, row in df.iterrows():
        xxth = row.get(xxth_col)
        period = parse_period(row.get(period_col))
        if xxth is None or period is None:
            continue
        xxth_values.append(str(xxth))

        period_values.append(period)

    if not xxth_values:
        raise ValueError("No valid data extracted for xxth/期間 columns.")

    create_boxplot(xxth_values, period_values, args.output)


if __name__ == "__main__":
    main()
