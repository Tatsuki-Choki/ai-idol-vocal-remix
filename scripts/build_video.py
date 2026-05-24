#!/usr/bin/env python3
"""arrangement.json を読み、黒背景＋パート名テロップの YouTube 用動画を書き出す。

各セクションの区間に、歌っている人の名前を白いゴシック体で中央表示する:
  - ソロ（1人）  -> その人の display 名（例「ミク」）
  - 全員ユニゾン  -> video.unison_label（例「全員」）
  - 一部複数      -> 名前を「・」で連結
歌唱区間の外（イントロ・間奏・アウトロ）は真っ黒（文字なし）。

このマシンの ffmpeg は drawtext 非対応のため、テロップは Pillow で
フレーム画像に焼いてから concat で動画化する。表示名・区間・フォント等は
すべて arrangement.json 側で管理する。

依存: Pillow, ffmpeg。使い方: python3 scripts/build_video.py [arrangement.json]
"""
import sys, json, os, subprocess, tempfile, shutil
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def label_for(vocals, vocalists, unison_label):
    if len(vocals) == 1:
        return vocalists[vocals[0]]["display"]
    if len(vocals) == len(vocalists):
        return unison_label
    return "・".join(vocalists[v]["display"] for v in vocals)


def audio_duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path])
    return float(out.strip())


def make_frame(text, w, h, font, path):
    img = Image.new("RGB", (w, h), "black")
    if text:
        d = ImageDraw.Draw(img)
        d.text((w / 2, h / 2), text, fill="white", font=font, anchor="mm")
    img.save(path)


def main(arr_path):
    with open(arr_path, encoding="utf-8") as f:
        arr = json.load(f)
    v = arr["video"]
    audio = os.path.join(ROOT, v["audio"])
    out = os.path.join(ROOT, v["output"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    w, h = (int(x) for x in v["resolution"].split("x"))
    font = ImageFont.truetype(v["fontfile"], v["fontsize"])
    unison = v.get("unison_label", "全員")

    # 歌唱セクションと、その隙間（イントロ/間奏/アウトロ=空白）でタイムラインを埋める
    secs = sorted(arr["sections"], key=lambda s: s["start"])
    dur = audio_duration(audio)
    timeline, t = [], 0.0
    for sec in secs:
        if sec["start"] > t:
            timeline.append((sec["start"] - t, ""))  # 直前セクションとの隙間（間奏）
        timeline.append((sec["end"] - sec["start"],
                         label_for(sec["vocals"], arr["vocalists"], unison)))
        t = sec["end"]
    if t < dur:
        timeline.append((dur - t, ""))

    # ユニークなラベルごとにフレーム画像を1枚だけ生成して使い回す
    tmp = tempfile.mkdtemp()
    frames = {}
    for _, text in timeline:
        if text not in frames:
            p = os.path.join(tmp, f"f{len(frames)}.png")
            make_frame(text, w, h, font, p)
            frames[text] = p

    # concat demuxer 用リスト（最後のフレームは duration なしでもう一度書く）
    listf = os.path.join(tmp, "list.txt")
    with open(listf, "w", encoding="utf-8") as f:
        for d, text in timeline:
            f.write(f"file '{frames[text]}'\nduration {d:.3f}\n")
        f.write(f"file '{frames[timeline[-1][1]]}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", listf,
        "-i", audio,
        "-vf", f"fps={v.get('fps',30)},format=yuv420p",
        "-c:v", "libx264", "-preset", "medium",
        "-c:a", "aac", "-b:a", "320k",
        "-t", f"{dur:.3f}",  # 音声長で映像を切る（末尾に余分な黒が残らないように）
        "-shortest", out,
    ]
    print("ffmpeg 実行中...")
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"書き出し完了: {v['output']}  ({dur:.1f}秒)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "arrangement.json"))
