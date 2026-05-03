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
    python lst_to_txt.py <input.lst> --ch <ch> --tag1 <tag1> --tag2 <tag2>
    python lst_to_txt.py <input.lst> --ch 1 --tag1 0 --tag2 1
"""

import sys
import argparse

# ── 비트 마스크 ───────────────────────────────────────────────────────────────
CHBIT      = 0x0000000000000007
EDGEBIT    = 0x0000000000000008
DATABIT    = 0x00000000FFFFFFF0
SWEEPBIT   = 0x0000FFFF00000000
TAGBIT     = 0x7FFF000000000000
LOSTBIT    = 0x8000000000000000


def parse_line(a: int) -> dict:
    """64비트 정수 하나를 분해하여 각 필드를 반환합니다."""
    return {
        "channel"  : int(a & CHBIT),
        "edge"     : int((a & EDGEBIT)  >>  3),
        "timedata" : float((a & DATABIT) >>  4)*0.1,
        "sweeps"   : int((a & SWEEPBIT) >> 32),
        "tag"      : int((a & TAGBIT)   >> 48),
        "data_lost": int((a & LOSTBIT)  >> 63),
    }


def convert(infile: str, ch: int, tag1: int, tag2: int):
    in_data_section = False
    entries_tag1 = []
    entries_tag2 = []
    skipped = 0

    with open(infile, "r") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            if line.upper() == "[DATA]":
                in_data_section = True
                continue

            if not in_data_section:
                continue

            if line.startswith("[") and line.endswith("]"):
                break

            if not line[0].isdigit() and line[0] not in "abcdefABCDEF":
                continue

            try:
                a = int(line, 16)
            except ValueError:
                skipped += 1
                continue

            e = parse_line(a)

            # ch 필터 후 tag1 / tag2 분류
            if e["channel"] != ch:
                continue
            if e["tag"] == tag1:
                entries_tag1.append(e)
            elif e["tag"] == tag2:
                entries_tag2.append(e)

    # ── 출력 파일명 생성 ──────────────────────────────────────────────────────
    base = infile.rsplit(".", 1)[0]
    outfile1 = f"{base}_ch_{ch}_tag_{tag1}.txt"
    outfile2 = f"{base}_ch_{ch}_tag_{tag2}.txt"

    for outfile, entries, tag in [
        (outfile1, entries_tag1, tag1),
        (outfile2, entries_tag2, tag2),
    ]:
        if not entries:
            print(f"경고: ch={ch}, tag={tag} 에 해당하는 데이터가 없습니다 → {outfile} 생성 생략")
            continue

        with open(outfile, "w") as f:
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
    parser = argparse.ArgumentParser(
        description="lst → txt 변환 (ch 1개, tag 2개 필터)"
    )
    parser.add_argument("input",        help="입력 .lst 파일 경로")
    parser.add_argument("--ch",   type=int, required=True, help="channel 번호")
    parser.add_argument("--tag1", type=int, required=True, help="첫 번째 tag 번호")
    parser.add_argument("--tag2", type=int, required=True, help="두 번째 tag 번호")
    args = parser.parse_args()

    print(f"입력 파일 : {args.input}")
    print(f"필터 조건 : ch={args.ch}, tag={args.tag1} / tag={args.tag2}")

    try:
        convert(args.input, args.ch, args.tag1, args.tag2)
    except FileNotFoundError:
        print(f"오류: 파일을 열 수 없습니다 → {args.input}")
        sys.exit(1)


if __name__ == "__main__":
    main()