"""
lst_to_txt.py
-------------
.lst 파일의 [DATA] 섹션에서 8바이트 데이터를 추출하여
channel# tag# sweeps timedata 형식의 .txt 파일로 저장합니다.

비트 구조 (64bit):
  bit  0~2  : channel#  (3 bit)
  bit  3    : edge      (1 bit)  0=up / 1=dn
  bit  4~31 : timedata  (28 bit)
  bit 32~47 : sweeps    (16 bit)
  bit 48~62 : tag       (15 bit)
  bit 63    : data_lost  (1 bit)

사용법:
    python lst_to_txt.py <input.lst>
    python lst_to_txt.py <input.lst> <output.txt>   # 출력 파일명 직접 지정
"""

import sys

# ── 비트 마스크 ───────────────────────────────────────────────────────────────
CHBIT      = 0x0000000000000007   # bit  0~2
EDGEBIT    = 0x0000000000000008   # bit  3
DATABIT    = 0x00000000FFFFFFF0   # bit  4~31
SWEEPBIT   = 0x0000FFFF00000000   # bit 32~47
TAGBIT     = 0x7FFF000000000000   # bit 48~62
LOSTBIT    = 0x8000000000000000   # bit 63


def parse_line(a: int) -> dict:
    """64비트 정수 하나를 분해하여 각 필드를 반환합니다."""
    return {
        "channel"  : int(a & CHBIT),
        "edge"     : int((a & EDGEBIT)   >>  3),
        "timedata" : float((a & DATABIT) >>  4)*0.1,
        "sweeps"   : int((a & SWEEPBIT)  >> 32),
        "tag"      : int((a & TAGBIT)    >> 48),
        "data_lost": int((a & LOSTBIT)   >> 63),
    }


def convert(infile: str, outfile: str):
    in_data_section = False
    entries = []
    skipped = 0

    with open(infile, "r") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            # [DATA] 섹션 시작 감지
            if line.upper() == "[DATA]":
                in_data_section = True
                continue

            # [DATA] 이전은 모두 건너뜀
            if not in_data_section:
                continue

            # 섹션이 바뀌면 종료 (예: [NEXT_SECTION])
            if line.startswith("[") and line.endswith("]"):
                break

            # 주석·헤더 줄 건너뜀
            if not line[0].isdigit() and line[0] not in "abcdefABCDEF":
                continue

            # 16진수 파싱
            try:
                a = int(line, 16)
            except ValueError:
                skipped += 1
                continue

            entries.append(parse_line(a))

    if not entries:
        print("추출된 데이터가 없습니다. [DATA] 섹션을 확인해 주세요.")
        return

    # ── 출력 ──────────────────────────────────────────────────────────────────
    with open(outfile, "w") as f:
        # 헤더
        f.write("# channel\ttag\tsweeps\ttimedata\tedge\tdata_lost\n")
        for e in entries:
            f.write(
                f"{e['channel']}\t"
                f"{e['tag']}\t"
                f"{e['sweeps']}\t"
                f"{e['timedata']:.2f}\t"
                f"{e['edge']}\t"
                f"{e['data_lost']}\n"
            )

    print(f"완료: {len(entries)}개 항목 저장 → {outfile}")
    if skipped:
        print(f"  (파싱 실패로 건너뛴 줄: {skipped}개)")


def main():
    if len(sys.argv) < 2:
        print("사용법: python lst_to_txt.py <input.lst> [output.txt]")
        sys.exit(1)

    infile  = sys.argv[1]
    outfile = sys.argv[2] if len(sys.argv) >= 3 else infile.replace(".lst", ".txt")

    print(f"{infile} → {outfile}")

    try:
        convert(infile, outfile)
    except FileNotFoundError:
        print(f"오류: 파일을 열 수 없습니다 → {infile}")
        sys.exit(1)


if __name__ == "__main__":
    main()
