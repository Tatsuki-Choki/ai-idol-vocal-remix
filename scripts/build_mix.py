#!/usr/bin/env python3
"""arrangement.json を読み、BGM の上に各セクションのボーカルを重ねて 1 曲に書き出す。

人を増やすときはスクリプトではなく arrangement.json を編集する:
  - vocalists に { "name": {"file":..., "gain_db":0, "pan":0} } を足す
  - sections の "vocals" 配列に名前を並べる（並べた数だけユニゾンで重なる）

依存: numpy のみ（WAV は標準ライブラリ wave で読み書き）。
使い方: python3 scripts/build_mix.py [arrangement.json]
"""
import sys, json, wave, os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_wav(path):
    """WAV を読み、(samples[N,2] float32 -1..1, sr) を返す。モノはステレオに複製。"""
    w = wave.open(path, "rb")
    sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
    d = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    w.close()
    d = d.reshape(-1, ch)
    if ch == 1:
        d = np.repeat(d, 2, axis=1)
    elif ch > 2:
        d = d[:, :2]
    return d, sr


def apply_pan(stereo, pan):
    """pan: -1=左 0=中央 1=右（等パワー）。"""
    if pan == 0:
        return stereo
    angle = (pan + 1) * 0.25 * np.pi  # 0..pi/2
    l, r = np.cos(angle), np.sin(angle)
    out = stereo.copy()
    out[:, 0] *= l * np.sqrt(2)
    out[:, 1] *= r * np.sqrt(2)
    return out


def fade_window(n, fade_samp):
    """両端に fade_samp のフェードを持つ窓を作る。"""
    win = np.ones(n)
    f = min(fade_samp, n // 2)
    if f > 0:
        ramp = np.linspace(0, 1, f)
        win[:f] = ramp
        win[-f:] = ramp[::-1]
    return win[:, None]


def main(arr_path):
    with open(arr_path, encoding="utf-8") as f:
        arr = json.load(f)

    bgm, sr = load_wav(os.path.join(ROOT, arr["bgm"]))
    out = bgm.copy()
    total = len(out)

    voc = {}
    for name, cfg in arr["vocalists"].items():
        data, vsr = load_wav(os.path.join(ROOT, cfg["file"]))
        if vsr != sr:
            raise SystemExit(f"サンプルレート不一致: {name} {vsr} != BGM {sr}")
        gain = 10 ** (cfg.get("gain_db", 0) / 20.0)
        data = apply_pan(data, cfg.get("pan", 0)) * gain
        voc[name] = data

    fade = int(arr.get("crossfade_sec", 0.3) * sr)

    for sec in arr["sections"]:
        s = int(sec["start"] * sr)
        e = min(int(sec["end"] * sr), total)
        win = fade_window(e - s, fade)
        sgain = 10 ** (sec.get("gain_db", 0) / 20.0)  # セクション単位の音量（重ね数の多いサビを抑える等）
        for name in sec["vocals"]:
            v = voc[name]
            seg = v[s:e]
            if len(seg) < e - s:  # ボーカルが短い場合は無音で埋める
                seg = np.vstack([seg, np.zeros((e - s - len(seg), 2), np.float32)])
            out[s:e] += seg * win * sgain

    out *= 10 ** (arr.get("master_gain_db", 0) / 20.0)

    # クリップ防止: ピークが 1 を超えたら全体を縮める
    peak = np.max(np.abs(out))
    if peak > 0.99:
        out *= 0.99 / peak
        print(f"ピーク {peak:.2f} を 0.99 に正規化（音割れ防止）")

    out_path = os.path.join(ROOT, arr["output"])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    o16 = (np.clip(out, -1, 1) * 32767).astype(np.int16)
    w = wave.open(out_path, "wb")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(sr)
    w.writeframes(o16.tobytes())
    w.close()
    print(f"書き出し完了: {arr['output']}  ({total/sr:.1f}秒)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "arrangement.json"))
