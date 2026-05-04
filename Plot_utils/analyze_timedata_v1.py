"""
analyze_timedata.py
-------------------
test.txt 파일에서 sweeps 기준으로 전체 측정 시간을 구간으로 나누고
각 구간에서 peak ± roi/2 범위의 timedata 평균값, 전체 평균 및 표준편차를 계산합니다.

사용법:
    python analyze_timedata.py <input.txt> --peak <peak> --roi <roi>
    python analyze_timedata.py test.txt --peak 13276000 --roi 10000
"""

import sys
import argparse
import numpy as np


# ── 데이터 로드 ───────────────────────────────────────────────────────────────
def load_data(filepath: str) -> np.ndarray:
    dtype = np.dtype([
        ("channel",   np.int32),
        ("tag",       np.int32),
        ("sweeps",    np.int64),
        ("timedata",  np.float64),
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
                rows.append((
                    int(parts[0]),
                    int(parts[1]),
                    int(parts[2]),
                    float(parts[3]),
                    int(parts[4]),
                    int(parts[5]),
                ))
            except ValueError:
                continue

    if not rows:
        print("오류: 유효한 데이터가 없습니다.")
        sys.exit(1)

    return np.array(rows, dtype=dtype)


# ── 구간 분석 ─────────────────────────────────────────────────────────────────
def analyze(data: np.ndarray, n_segments: int, peak: float, roi: float):
    """
    전체 sweeps 범위를 n_segments개로 나누어 각 구간에서
    peak ± roi/2 범위의 timedata 평균을 구하고
    그 평균들의 평균과 표준편차를 반환합니다.

    반환값: (전체평균, 표준편차, 구간별_결과_리스트)
    구간별_결과: (sweep_start, sweep_end, count, segment_mean)
    """
#    sweep_min  = int(data["sweeps"].min())
    sweep_min = 0	
    sweep_max  = int(data["sweeps"].max())
    sweep_range = sweep_max - sweep_min

    roi_min = peak - roi / 2
    roi_max = peak + roi / 2

    # ROI 필터를 전체 데이터에 먼저 적용
    roi_mask   = (data["timedata"] >= roi_min) & (data["timedata"] <= roi_max)
    data_roi   = data[roi_mask]

    segment_means = []
    segment_info  = []

    for i in range(n_segments):
        s_start = sweep_min + i       * (sweep_range / n_segments)
        s_end   = sweep_min + (i + 1) * (sweep_range / n_segments)

        if i < n_segments - 1:
            mask = (data_roi["sweeps"] >= s_start) & (data_roi["sweeps"] < s_end)
        else:
            mask = (data_roi["sweeps"] >= s_start) & (data_roi["sweeps"] <= s_end)

        seg_data = data_roi["timedata"][mask]

        if len(seg_data) == 0:
           seg_mean = np.nan
           seg_std  = np.nan
        elif len(seg_data) == 1:
           seg_mean = float(np.mean(seg_data[0]))
           seg_std = np.pan
        else:
           seg_mean = seg_mean = float(np.mean(seg_data))
           seg_std  = float(np.std(seg_data, ddof=1))

        segment_means.append(seg_mean)
        segment_info.append((s_start, s_end, len(seg_data), seg_mean, seg_std))

    valid_means = [m for m in segment_means if not np.isnan(m)]
    if not valid_means:
        return np.nan, np.nan, segment_info

    overall_mean = float(np.mean(valid_means))
    overall_std  = float(np.std(valid_means, ddof=1))

    return overall_mean, overall_std, segment_info


# ── check.dat 출력 (100개 구간 검증용) ────────────────────────────────────────
def write_check(data: np.ndarray, segment_info: list, peak: float, roi: float, check: int,
                outfile: str = "check.dat"):
#    sweep_min   = int(data["sweeps"].min())
    sweep_min = 0	
    sweep_max   = int(data["sweeps"].max())
    sweep_range = sweep_max - sweep_min
    n_segments  = len(segment_info)

    roi_min = peak - roi / 2
    roi_max = peak + roi / 2
    roi_mask  = (data["timedata"] >= roi_min) & (data["timedata"] <= roi_max)
    data_roi  = data[roi_mask]

    with open(outfile, "w") as f:
        f.write("# check.dat — 구간 검증용\n")
        f.write(f"# 전체 sweeps 범위 : {sweep_min} ~ {sweep_max}  (range={sweep_range})\n")
        f.write(f"# ROI 범위         : {roi_min:.2f} ~ {roi_max:.2f}  "
                f"(peak={peak}, roi={roi})\n")
        f.write("# segment\tsweep_start\tsweep_end\tsweeps\ttimedata\n")

        for i, (s_start, s_end, count, seg_mean, seg_std) in enumerate(segment_info):
            if i < n_segments - 1:
                mask = (data_roi["sweeps"] >= s_start) & (data_roi["sweeps"] < s_end)
            else:
                mask = (data_roi["sweeps"] >= s_start) & (data_roi["sweeps"] <= s_end)

            for row in data_roi[mask]:
                f.write(
                    f"{i+1}\t"
                    f"{s_start:.1f}\t"
                    f"{s_end:.1f}\t"
                    f"{row['sweeps']}\t"
                    f"{row['timedata']:.2f}\n"
                )

    print(f"검증 파일 저장 완료 → {outfile}")


# ── 메인 ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="timedata 구간 분석 (peak ± roi/2 범위 필터 적용)"
    )
    parser.add_argument("input",        help="입력 .txt 파일 경로")
    parser.add_argument("--peak", type=float, required=True, help="ROI 중심값")
    parser.add_argument("--roi",  type=float, required=True, help="ROI 폭 (peak ± roi/2)")
    parser.add_argument("--check", type=int, required=True, help="상세출력 및 check.dat 저장에 사용할 구간 수")
    args = parser.parse_args()

    try:
        data = load_data(args.input)
    except FileNotFoundError:
        print(f"오류: 파일을 열 수 없습니다 → {args.input}")
        sys.exit(1)

#    sweep_min = int(data["sweeps"].min())
    sweep_min = 0	
    sweep_max = int(data["sweeps"].max())
    roi_min   = args.peak - args.roi / 2
    roi_max   = args.peak + args.roi / 2
    roi_count = int(np.sum((data["timedata"] >= roi_min) & (data["timedata"] <= roi_max)))

    print(f"파일          : {args.input}")
    print(f"전체 항목     : {len(data):,}개")
    print(f"sweeps 범위   : {sweep_min} ~ {sweep_max}  (전체 측정 시간 = {sweep_max - sweep_min})")
    print(f"peak          : {args.peak}")
    print(f"ROI 범위      : {roi_min:.2f} ~ {roi_max:.2f}  (폭 = {args.roi})")
    print(f"ROI 내 항목   : {roi_count:,}개")
    print()
    print(f"{'구간 수':>8}  {'평균값':>18}  {'표준편차':>18}  {'유효구간':>8}")
    print("-" * 62)

    segment_counts = [10, 100, 200, 300, 400, 500, 1000]
    result_check = None

    for n in segment_counts:
        mean, std, seg_info = analyze(data, n, args.peak, args.roi)
        valid = sum(1 for _, _, c, _, _ in seg_info if c > 0)

        if np.isnan(mean):
            print(f"{n:>8}  {'데이터 없음':>18}  {'—':>18}  {valid:>8}")
        else:
            print(f"{n:>8}  {mean:>18.4f}  {std:>18.4f}  {valid:>8}")

        if n == args.check:
            result_check = seg_info

    # 구간 검증 파일 출력
    print()
    if result_check:
        write_check(data, result_check, args.peak, args.roi, args.check)

    # 100개 구간 상세 출력
    print()
    print("100개 구간 상세:")
    print(f"{'구간':>5}  {'sweep 시작':>12}  {'sweep 끝':>12} "
          f"{'데이터 수':>10}  {'구간 평균':>18}  {'구간 표준편차':>14}\n")
    print("-" * 80)
    for i, (s_start, s_end, count, seg_mean, seg_std) in enumerate(result_check):
        mean_str = f"{seg_mean:>18.4f}" if not np.isnan(seg_mean) else f"{'데이터 없음':>18}"
        std_str  = f"{seg_std:>14.4f}"  if not np.isnan(seg_std)  else f"{'—':>14}"
        print(f"{i+1:>5}  {s_start:>12.1f}  {s_end:>12.1f}  "
              f"{count:>10}  {mean_str}  {std_str}")

    # 구간 검증 요약 출력
    with open("check1.dat", "w") as f:
        f.write("100개 구간 상세:"+"\n")
        f.write(f"{'구간':>5}  {'sweep 시작':>12}  {'sweep 끝':>12} "
                f"{'데이터 수':>10}  {'구간 평균':>18}  {'구간 표준편차':>14}" + "\n")
        f.write("-" * 80 + "\n")
        for i, (s_start, s_end, count, seg_mean, seg_std) in enumerate(result_check):
            mean_str = f"{seg_mean:>18.4f}" if not np.isnan(seg_mean) else f"{'데이터 없음':>18}"
            std_str  = f"{seg_std:>14.4f}"  if not np.isnan(seg_std)  else f"{'—':>14}"
            f.write(f"{i+1:>5}  {s_start:>12.1f}  {s_end:>12.1f}  "
                    f"{count:>10}  {mean_str}  {std_str}\n")

if __name__ == "__main__":
    main()
