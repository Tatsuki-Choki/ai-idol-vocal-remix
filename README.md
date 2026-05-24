# AIアイドル ボーカル再構成プロジェクト

BGM（インスト）の上に、複数のボーカルをセクション単位で割り当てて1曲に再構成する。
ボーカルは将来最大5人規模まで増える前提。**割り当ては `arrangement.json` の編集だけで完結**する。

## ディレクトリ構成

```
.
├── arrangement.json        # ★編集の中心：誰がどのセクションを歌うか
├── stems/                  # 素材（入力・原則いじらない）
│   ├── bgm/instrumental.wav
│   └── vocals/
│       ├── 01_original.wav   # オリジナルの歌声
│       └── 02_instant.wav    # クリエイトした歌声（instant）
├── analysis/
│   └── vocal_sections.csv  # 歌唱/無音の区間データ（構成決めの参考）
├── build/                  # 書き出し（生成物）
└── scripts/build_mix.py    # arrangement.json を読んでミックスする
```

## 書き出し方法

```bash
python3 scripts/build_mix.py     # 音源（WAV）を書き出す
python3 scripts/build_video.py   # 音源＋パート名テロップの動画（MP4）を書き出す
```

- 音源は `arrangement.json` の `output` に指定したパスへ書き出す。
- 動画は `video` ブロックの設定（音源・出力・解像度・フォント）で、黒背景に白いゴシック体でパート名を表示する。ソロはそのキャラの `display` 名、全員ユニゾンは `unison_label`（「全員」）、歌唱区間外は黒画面。
- このマシンの ffmpeg は `drawtext` 非対応のため、`build_video.py` は Pillow でテロップ画像を作り concat で動画化している。

## ボーカルを増やすとき

1. 音源を `stems/vocals/03_xxxx.wav` のように置く（44.1kHz/16bit 推奨、尺は他と同じ曲）
2. `arrangement.json` の `vocalists` に1行足す
   ```json
   "name3": { "file": "stems/vocals/03_xxxx.wav", "gain_db": 0, "pan": 0 }
   ```
3. 歌わせたい `sections` の `vocals` 配列にその名前を入れる

## arrangement.json の項目

| 項目 | 意味 |
|---|---|
| `bgm` | 土台のインスト |
| `output` | 書き出し先 |
| `crossfade_sec` | 切り替え点のフェード秒数（段差・ノイズ防止） |
| `master_gain_db` | 全体音量 |
| `vocalists[].gain_db` | その声の音量（dB） |
| `vocalists[].pan` | 定位 -1.0=左 / 0=中央 / 1.0=右 |
| `sections[].start`/`end` | 区間（秒） |
| `sections[].vocals` | その区間で鳴らす声の配列（並べた数だけ重なる＝ユニゾン） |

## 割り当てルール（現行）

- Aメロ → オリジナル
- Bメロ → クリエイト（instant）
- サビ → 両方をユニゾンで重ねる

区間は `analysis/vocal_sections.csv` の解析推定をベースにした暫定値。試聴して `start`/`end` を微調整する。
