"""
plot_timedata.py
----------------
lst_to_txt.py 로 생성된 txt 파일에서
지정한 channel / tag 조건으로 필터링한 뒤
timedata 히스토그램을 그립니다.

사용법:
    python plot_timedata.py <input.txt> --ch <channel> --tag <tag> --bins <bins>

예시:
    python plot_timedata.py input.txt --ch 3 --tag 12 --bins 512
    python plot_timedata.py input.txt --ch 3               # tag 전체, bins=256 (기본값)
    python plot_timedata.py input.txt --tag 5  --bins 1024 # channel 전체

옵션:
    --ch    필터링할 channel 번호 (생략 시 전체 channel)
    --tag   필터링할 tag 번호    (생략 시 전체 tag)
    --bins  히스토그램 bin 개수  (기본값: 256)
    --save  그래프를 PNG 파일로 저장 (생략 시 화면 출력)

Requirements:
    pip install numpy matplotlib
"""

import argparse
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


# ── 데이터 로드 ───────────────────────────────────────────────────────────────
def load_data(filepath: str) -> np.ndarray:
    """
    탭 구분 txt 파일을 읽어 numpy structured array로 반환합니다.
    '#'으로 시작하는 행은 주석으로 무시합니다.
    """
    dtype = np.dtype([
        ("channel",   np.int32),
        ("tag",       np.int32),
        ("sweeps",    np.int64),
        ("timedata",  np.int64),
        ("edge",      np.int32),
        ("data_lost", np.int32),
    ])

    rows = []
    with open(filepath, "r") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 6:
                continue
            try:
                rows.append(tuple(int(p) for p in parts[:6]))
            except ValueError:
                continue

    if not rows:
        print("오류: 유효한 데이터가 없습니다.")
        sys.exit(1)

    return np.array(rows, dtype=dtype)

# ── 필터링 ────────────────────────────────────────────────────────────────────
def filter_data(data: np.ndarray, ch: int | None, tag: int | None) -> np.ndarray:
    mask = np.ones(len(data), dtype=bool)
    if ch is not None:
        mask &= (data["channel"] == ch)
    if tag is not None:
        mask &= (data["tag"] == tag)
    return data[mask]


# ── 히스토그램 플롯 ───────────────────────────────────────────────────────────
def plot_histogram(
    timedata: np.ndarray,
    bins: int,
    ch: int | None,
    tag: int | None,
    total: int,
    save_path: str | None,
):
    if len(timedata) == 0:
        print("조건에 맞는 데이터가 없습니다. channel / tag 값을 확인해 주세요.")
        return

    center_ion = 12972179
    roi_range = 10000
    roi_min = center_ion - roi_range*0.5
    roi_max = center_ion + 2*roi_range*0.5
    No_bins = int((roi_max-roi_min)/6.4+0.5)
 #   timedata = timedata*0.1

    fig, ax = plt.subplots(figsize=(10, 5))

    counts, edges, patches = ax.hist(
        timedata,
        bins=No_bins,
        range=(roi_min,roi_max),
        color="#3a86ff",
        edgecolor="none",
        linewidth=0.4,
        alpha=0.85,
    )

    # 축 레이블
    ax.set_xlabel("Timedata (ns)", fontsize=12)
    ax.set_ylabel("Counts (counts/6.4ns)", fontsize=12)

    # 타이틀 구성
    cond_parts = []
    if ch is not None:
        cond_parts.append(f"Channel = {ch}")
    else:
        cond_parts.append("Channel = All")
    if tag is not None:
        cond_parts.append(f"Tag = {tag}")
    else:
        cond_parts.append("Tag = All")
    cond_str = ",  ".join(cond_parts)

    ax.set_title(
        f"Timedata Spectrum  |  {cond_str}  |  Bins = {bins}",
        fontsize=13,
        pad=12,
    )

    # 통계 박스
    stats_text = (
        f"Total entries : {total:,}\n"
        f"Filtered      : {len(timedata):,}\n"
        f"Min           : {int(timedata.min()):,}\n"
        f"Max           : {int(timedata.max()):,}\n"
        f"Mean          : {timedata.mean():.1f}\n"
        f"Std           : {timedata.std():.1f}"
    )
    ax.text(
        0.97, 0.97, stats_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.7, edgecolor="#cccccc"),
        fontfamily="monospace",
    )

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"저장 완료: {save_path}")
    else:
        plt.show()


# ── 메인 ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="timedata 히스토그램 플롯 (channel / tag / bins 조건 지정)"
    )
    parser.add_argument("input",         help="입력 txt 파일 경로")
    parser.add_argument("--ch",   type=int, default=None, help="channel 번호 (생략 시 전체)")
    parser.add_argument("--tag",  type=int, default=None, help="tag 번호    (생략 시 전체)")
    parser.add_argument("--bins", type=int, default=256,  help="bin 개수    (기본값: 256)")
    parser.add_argument("--save", type=str, default=None, help="PNG 저장 경로 (생략 시 화면 출력)")
    args = parser.parse_args()

    if args.bins < 1:
        print("오류: --bins 는 1 이상이어야 합니다.")
        sys.exit(1)

    try:
        data = load_data(args.input)
    except FileNotFoundError:
        print(f"오류: 파일을 열 수 없습니다 → {args.input}")
        sys.exit(1)

    total = len(data)
    filtered = filter_data(data, args.ch, args.tag)

    print(f"전체 항목    : {total:,}")
    print(f"필터 후 항목 : {len(filtered):,}  (ch={args.ch}, tag={args.tag})")

    plot_histogram(
        timedata  = filtered["timedata"].astype(np.float64),
        bins      = args.bins,
        ch        = args.ch,
        tag       = args.tag,
        total     = total,
        save_path = args.save,
    )


if __name__ == "__main__":
    main()
