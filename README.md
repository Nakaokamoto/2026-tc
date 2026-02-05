# Excel Boxplot ツール

このリポジトリには、Excel ファイルから `xxth` と `期間` 列を抽出し、箱ひげ図を作成する CLI ツールが含まれています。

## 概要

処理の流れは以下のとおりです。

- **Pandas** で Excel シートを読み込みます。
- **ヘッダーの近似一致**で `xxth` と `期間` の列を特定します（軽微な誤認識を許容）。
- **Matplotlib** で箱ひげ図を描画し、箱の色を緑に設定します。

## 使い方

```bash
python tools/plot_xxth_boxplot.py \
  path/to/input_table.xlsx \
  output/xxth_period_boxplot.png
```

オプション引数:

```bash
python tools/plot_xxth_boxplot.py \
  path/to/input_table.xlsx \
  output/xxth_period_boxplot.png \
  --sheet Sheet1 \
  --min-similarity 0.7
```

## 入力と出力の期待仕様

### サンプル入力（例）

以下のようなヘッダーを持つシートを想定しています。

| xxth | 期間 | ... |
| ---- | ---- | --- |
| 7th_CR | 12 | ... |
| 8th_CR | 9 | ... |


### 期待される出力

作成される箱ひげ図の内容は以下の通りです。

- **X軸**: `xxth`（先頭の数字で並び替え、7th, 8th, 9th... の順）
- **Y軸**: `期間` の数値（数値以外や欠損は除外）
- **箱の色**: 緑

出力画像は指定したパス（例: `output/xxth_period_boxplot.png`）に保存されます。

