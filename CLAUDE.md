# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

BGM（インスト）の上に複数のボーカルをセクション単位で割り当て、1曲に再構成する音声編集プロジェクト。ボーカルは将来最大5人規模まで増える前提で設計されている。元素材は Suno 製の同一楽曲（"controlla"）から派生しており、全トラックが完全同期・同尺（約292.75秒 / 44.1kHz / 16bit）。

## コマンド

```bash
# 音源を書き出す（arrangement.json を読んで build/ へ出力）
python3 scripts/build_mix.py [arrangement.json]

# パート名テロップ付きの YouTube 用動画を書き出す
python3 scripts/build_video.py [arrangement.json]

# 歌唱/無音の区間を解析し直す（素材が変わったとき）
# analysis/vocal_sections.csv を再生成する。閾値 -45dB、0.5秒刻み。
```

依存: `build_mix.py` は `numpy` のみ（WAV 入出力は標準ライブラリ `wave`）。`build_video.py` は `Pillow` と `ffmpeg`。

**重要な環境制約**: このマシンの ffmpeg（Homebrew 8.0.1）は libfreetype 無しでビルドされており `drawtext` フィルタが使えない。そのため `build_video.py` はテロップを Pillow で画像化し、concat demuxer で動画化している（drawtext には戻さない）。`-t {音源長}` で映像尺を音源に揃えている（concat 末尾フレームの伸びを防ぐため）。

## アーキテクチャ

中心は **データ駆動の設計**：編集作業はコード（`scripts/build_mix.py`）ではなく `arrangement.json` の編集で完結する。スクリプトは汎用エンジンで、楽曲固有の判断はすべて JSON 側に置く。

- **`arrangement.json`** — 単一の真実の源（source of truth）。音源・動画の両方がこれを読む。
  - `vocalists`（名前→ `file`/`gain_db`/`pan`/`display`）。`display` は動画のテロップ表示名。
  - `sections`（`label`/`start`/`end`/`vocals`配列、任意で `gain_db`）。`vocals` に名前を並べた数だけユニゾンで重なる。`gain_db` はセクション単位の音量（重ね数の多いサビを下げて正規化を弱める用途）。
  - `video`（`audio`/`output`/`resolution`/`fps`/`fontsize`/`fontfile`/`unison_label`）。
- **`scripts/build_mix.py`** — `arrangement.json` を読み、BGM をステレオ float32 で土台にして各セクションのボーカルを加算合成する。処理の要点:
  - モノラル音源はステレオに複製、`apply_pan()` で等パワー定位
  - 各セクション境界に `crossfade_sec` のフェード窓（`fade_window()`）をかけて段差・ノイズを防ぐ
  - セクション単位の `gain_db` を適用後、全トラック合成。ピークが0.99超なら全体を正規化して音割れを防止
- **`scripts/build_video.py`** — `arrangement.json` を読み、黒背景に全メンバー名を横一列で常時表示する動画を書き出す。各区間で歌っている人(`active`)だけを白(255)、他は明度 `video.dim_level` の灰で描き、「歌っている人をハイライト」する。歌唱区間の隙間は全員薄い。`active` の組み合わせ（frozenset）ごとにフレームを1枚キャッシュして concat。
- **`stems/`** — 入力素材。原則いじらない。`bgm/` と `vocals/`（`NN_name.wav` の連番命名）。
- **`analysis/vocal_sections.csv`** — 歌唱(`sing`)/無音(`gap`)の区間データ。セクション境界を決める参考値。
- **`build/`** — 書き出し生成物。

## 編集時の鉄則

- **ボーカルを増やす／割り当てを変える作業は `arrangement.json` のみ編集する。** `build_mix.py` は触らない（人数・構成に非依存な汎用エンジンとして保つ）。
- `arrangement.json` の `start`/`end` は秒。これは解析推定ベースの暫定値であり、正確なAメロ/Bメロ/サビの切れ目は試聴で確定する必要がある（機械判定は歌唱/無音の区間までしか分からない）。
- 全ボーカルトラックは同一楽曲由来で完全同期している前提。タイムアライメント処理は不要だが、同期していない素材を足す場合はこの前提が崩れる。
- 現行の割り当てルール: Aメロ=オリジナル / Bメロ=instant / サビ=両者ユニゾン。
