#!/usr/bin/env python3
"""arrangement.json を読み、黒背景に全メンバー名を常時並べた YouTube 用動画を書き出す。

3人（vocalists 全員）の名前を横一列に常に表示し、各セクションで「歌っている人」
だけを白く（不透明）、歌っていない人を薄く（video.dim_level の明度）表示する。
  - ソロ区間   -> その人だけ濃く、他2人は薄い
  - 全員ユニゾン -> 全員濃い
  - イントロ/間奏/アウトロ -> 全員薄い
表示名・区間・フォント・薄さは arrangement.json 側で管理する。

このマシンの ffmpeg は drawtext 非対応のため、Pillow でフレーム画像を作り
concat で動画化する。依存: Pillow, ffmpeg。
使い方: python3 scripts/build_video.py [arrangement.json]
"""
import sys, json, os, subprocess, tempfile, shutil
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def audio_duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path])
    return float(out.strip())


def make_frame(active, vocalists, w, h, font, dim, path):
    """vocalists 全員を横一列に表示。active に含まれる人は白、他は明度 dim の灰。"""
    img = Image.new("RGB", (w, h), "black")
    d = ImageDraw.Draw(img)
    names = list(vocalists.items())
    n = len(names)
    for i, (key, cfg) in enumerate(names):
        x = w * (i + 0.5) / n
        v = 255 if key in active else dim  # 明度で「透明度」を表現（黒地に白〜灰）
        d.text((x, h / 2), cfg["display"], fill=(v, v, v), font=font, anchor="mm")
    img.save(path)


def main(arr_path):
    with open(arr_path, encoding="utf-8") as f:
        arr = json.load(f)
    v = arr["video"]
    vocalists = arr["vocalists"]
    audio = os.path.join(ROOT, v["audio"])
    out = os.path.join(ROOT, v["output"])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    w, h = (int(x) for x in v["resolution"].split("x"))
    font = ImageFont.truetype(v["fontfile"], v["fontsize"])
    dim = v.get("dim_level", 60)

    # 各区間で「誰が歌っているか」(active) を決める。隙間は誰もいない=全員薄い。
    secs = sorted(arr["sections"], key=lambda s: s["start"])
    dur = audio_duration(audio)
    timeline, t = [], 0.0
    for sec in secs:
        if sec["start"] > t:
            timeline.append((sec["start"] - t, frozenset()))
        timeline.append((sec["end"] - sec["start"], frozenset(sec["vocals"])))
        t = sec["end"]
    if t < dur:
        timeline.append((dur - t, frozenset()))

    # active 状態の組み合わせごとにフレーム画像を1枚だけ生成して使い回す
    tmp = tempfile.mkdtemp()
    frames = {}
    for _, active in timeline:
        if active not in frames:
            p = os.path.join(tmp, f"f{len(frames)}.png")
            make_frame(active, vocalists, w, h, font, dim, p)
            frames[active] = p

    listf = os.path.join(tmp, "list.txt")
    with open(listf, "w", encoding="utf-8") as f:
        for d_, active in timeline:
            f.write(f"file '{frames[active]}'\nduration {d_:.3f}\n")
        f.write(f"file '{frames[timeline[-1][1]]}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", listf,
        "-i", audio,
        "-vf", f"fps={v.get('fps',30)},format=yuv420p",
        "-c:v", "libx264", "-preset", "medium",
        "-c:a", "aac", "-b:a", "320k",
        "-t", f"{dur:.3f}",
        "-shortest", out,
    ]
    print("ffmpeg 実行中...")
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"書き出し完了: {v['output']}  ({dur:.1f}秒)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "arrangement.json"))
