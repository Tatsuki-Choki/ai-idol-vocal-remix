# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

BGM（インスト）の上に複数のボーカルをセクション単位で割り当て、1曲に再構成し、パート名テロップ付きの YouTube 用動画まで書き出す音声編集プロジェクト。ボーカルは最大5人規模まで増える前提。現行は3人（ミク / レン / リン）。

## コマンド

```bash
python3 scripts/build_mix.py [arrangement.json]    # 音源(WAV)を書き出す
python3 scripts/build_video.py [arrangement.json]  # パート名テロップ付き動画(MP4)を書き出す
```

## ルール / ドキュメント

- **データ駆動の設計** — 編集は `arrangement.json` の編集で完結。スクリプトは触らない → 詳細: [docs/rules/architecture.html](docs/rules/architecture.html)
- **依存と環境制約** — ffmpeg が drawtext 非対応のため Pillow+concat で動画化 → 詳細: [docs/rules/environment.html](docs/rules/environment.html)
- **編集の鉄則・ボーカル追加手順・現行構成** — `arrangement.json` のみ編集、区間は試聴で確定 → 詳細: [docs/rules/editing-rules.html](docs/rules/editing-rules.html)

## 技術スタック

- Python 3（`numpy`, `Pillow`）
- ffmpeg / ffprobe（Homebrew 8.0.1、libfreetype 無し＝drawtext 不可）
- 素材: Suno "controlla" 由来、全トラック完全同期・同尺（約292.75秒 / 44.1kHz / 16bit）
