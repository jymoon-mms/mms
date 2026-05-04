import matplotlib.pyplot as plt
import numpy as np
import os
import sys


def plot_with_error_bars(filepath, output_pdf="test.pdf"):
    """
    데이터 파일을 읽어 에러바 포함 그래프를 생성하고 PDF로 저장합니다.

    Parameters
    ----------
    filepath   : str  – 입력 데이터 파일 경로
    output_pdf : str  – 저장할 PDF 파일명 (기본값: "test.pdf")

    데이터 파일 형식
    ----------------
    - 공백(또는 탭) 구분
    - '#' 으로 시작하는 줄은 주석으로 처리
    - 빈 줄은 건너뜀
    - 최소 6개 열 필요: 1열(x), 5열(y), 6열(y_error)
    """

    # ── 1. 파일 존재 확인 ──────────────────────────────────────────────
    if not os.path.isfile(filepath):
        print(f"[Error] 파일을 찾을 수 없습니다: {filepath}")
        sys.exit(1)

    # ── 2. 데이터 읽기 ─────────────────────────────────────────────────
    x_data, y_data, y_error = [], [], []
    skipped = 0

    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, raw in enumerate(f, start=1):
            line = raw.strip()

            # 빈 줄 또는 주석 건너뛰기
            if not line or line.startswith("#"):
                continue

            parts = line.split()

            # 열 개수 부족
            if len(parts) < 6:
                print(f"  [경고] {line_num}행: 열이 부족합니다 ({len(parts)}개) → 건너뜁니다.")
                skipped += 1
                continue

            try:
                x_val   = float(parts[0])   # 1열
                y_val   = float(parts[4])   # 5열
                err_val = float(parts[5])   # 6열

                if err_val < 0:
                    print(f"  [경고] {line_num}행: 오차값이 음수입니다 ({err_val}) → 절댓값으로 처리합니다.")
                    err_val = abs(err_val)

                x_data.append(x_val)
                y_data.append(y_val)
                y_error.append(err_val)

            except ValueError:
                print(f"  [경고] {line_num}행: 숫자로 변환할 수 없는 데이터 → 건너뜁니다.")
                skipped += 1

    # ── 3. 데이터 유효성 검사 ──────────────────────────────────────────
    if len(x_data) == 0:
        print("[Error] 유효한 데이터가 없습니다. 파일 형식을 확인하세요.")
        sys.exit(1)

    print(f"[Info] 총 {len(x_data)}개의 데이터 포인트를 읽었습니다. (건너뜀: {skipped}행)")

    # ── 4. NumPy 배열 변환 ─────────────────────────────────────────────
    x   = np.array(x_data)
    y   = (np.array(y_data)-np.array(y_data[0]))/np.array(y_data[0])*1E6
    err = np.array(y_error)/np.array(y_data)*1E06

    # ── 5. 그래프 생성 ─────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.fill_between(
        x,
        y - err,
        y + err,
        color='royalblue',
        alpha=0.25,
        label='Error Range (±1σ)',
        zorder=2,
    )
 
    # 데이터 포인트 + 연결선
    ax.plot(
        x, y,
        color='royalblue',
        linewidth=1.5,
        linestyle='-',
        zorder=3,
    )
    ax.scatter(
        x, y,
        color='royalblue',
        s=30,
        zorder=4,
        label='Experimental Data',
    )

    # ── 6. 그래프 꾸미기 ───────────────────────────────────────────────
    ax.set_title("TOF shift as a function of time", fontsize=14, pad=12)
    ax.set_xlabel("Time (Arb.)", fontsize=12)
    ax.set_ylabel("TOF Shift (ppm)", fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(fontsize=11)

    # 통계 요약 텍스트 (우측 상단)
    stats_text = (
        f"N = {len(x)}\n"
        f"y mean = {y.mean():.4g}\n"
        f"y std  = {y.std():.4g}"
    )
    ax.text(
        0.98, 0.97, stats_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment='top',
        horizontalalignment='right',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', alpha=0.8),
    )

    # ── 7. 저장 및 출력 ────────────────────────────────────────────────
    plt.ylim(-20,20)
    plt.tight_layout()                          # 레이블 잘림 방지
    plt.savefig(output_pdf, format='pdf')       # PDF 먼저 저장
    print(f"[Info] 그래프가 저장되었습니다: {output_pdf}")
    plt.show()
    plt.close(fig)                              # 메모리 해제


# ── 실행부 ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # 명령줄 인수로 파일 경로를 받을 수 있도록 처리
    # 사용 예: python tof_shift_plot_v1.py check1.dat
    #          python tof_shift_plot_v1.py check1.dat output.pdf
    if len(sys.argv) >= 2:
        input_file  = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) >= 3 else "test.pdf"
    else:
        input_file  = "check1.dat"   # 기본 파일 경로
        output_file = "test.pdf"     # 기본 출력 파일명

    plot_with_error_bars(input_file, output_file)
