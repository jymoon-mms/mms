"""
lst_to_root.py
--------------
Convert .lst binary/hex data files to .root-compatible format.
Translated from C++ ROOT macro using uproot + numpy.

Requirements:
    pip install uproot awkward numpy

Usage:
    python lst_to_root.py <input.lst>
"""

import sys
import struct
import numpy as np
import uproot


# ─── Bit masks ────────────────────────────────────────────────────────────────
CHBIT    = 0x07
EDGEBIT  = 0x08
DATABIT  = 0xFFFFFFF0
SWEEPBIT = 0xFFFF00000000
TAGBIT   = 0x7FFF000000000000


def usage():
    print("Usage: python lst_to_root.py <input.lst>")


def replace_ext(path: str, old: str, new: str) -> str:
    """Replace the first occurrence of `old` with `new` in `path`."""
    return path.replace(old, new, 1)


def parse_header_line(line: str, ch_n: int, caloff: list, calfact: list, data_length: int):
    """Parse a header (non-data) line and update calibration state."""
    if line[1:4] == "CHN":
        ch_n = int(line[4])
    elif line.startswith("caloff="):
        caloff[ch_n] = float(line[7:])
    elif line.startswith("calfact="):
        calfact[ch_n] = float(line[8:])
    elif line.startswith(";datalength="):
        data_length = int(line[12:13])
    return ch_n, caloff, calfact, data_length


def parse_data_line(line: str, data_length: int, caloff: list):
    """
    Parse a hex data line according to data_length (4, 6, or 8 bytes).

    Returns a dict of branch values, or None if the line is invalid.
    """
    try:
        a = int(line.strip(), 16)
    except ValueError:
        return None

    ch        = float(a & CHBIT)
    edge      = float((a & EDGEBIT) >> 3)
    datalost  = 0.0
    sweepdata = 0.0
    tagdata   = 0.0

    if data_length == 4:
        data   = (a >> 4) * 0.1
        rtdata = data - caloff[int(ch)]

    elif data_length == 6:
        data      = ((a & DATABIT) >> 4) * 0.1
        rtdata    = data - caloff[int(ch)]
        sweepdata = float(a >> 32)

    elif data_length == 8:
        data      = ((a & DATABIT) >> 4) * 0.1
        rtdata    = data - caloff[int(ch)]
        sweepdata = float((a & SWEEPBIT) >> 32)
        tagdata   = float((a & TAGBIT) >> 48)
        datalost  = float(a >> 63)
        print(f"{ch:.0f}    {tagdata:.0f}      {sweepdata:.0f}      {data:.2f}     {rtdata:.2f}")

    else:
        return None

    return {
        "ch":        ch,
        "edge":      edge,
        "data":      data,
        "rtdata":    rtdata,
        "sweepdata": sweepdata,
        "tagdata":   tagdata,
        "datalost":  datalost,
    }


def convert(infile: str):
    outfile = replace_ext(infile, ".lst", ".root")
    print(f"{infile} -> {outfile}")

    # Calibration state
    ch_n        = 0
    caloff      = [0.0] * 4
    calfact     = [1.0] * 4
    data_length = 0

    # Accumulators for each branch
    branches: dict[str, list] = {
        "ch": [], "edge": [], "data": [],
        "rtdata": [], "sweepdata": [], "tagdata": [], "datalost": [],
    }
    loop = 0

    try:
        with open(infile, "r") as f:
            for raw_line in f:
                line = raw_line.rstrip("\n")
                if not line:
                    continue

                first_char = line[0] if line else ""

                # Header line: first character is not a digit
                if not first_char.isdigit():
                    ch_n, caloff, calfact, data_length = parse_header_line(
                        line, ch_n, caloff, calfact, data_length
                    )

                # Data line
                else:
                    row = parse_data_line(line, data_length, caloff)
                    if row is not None:
                        for key, val in row.items():
                            branches[key].append(val)
                        loop += 1

    except FileNotFoundError:
        print("File cannot be opened!")
        sys.exit(1)

    print(f"Total entries parsed: {loop}")

    # ── Write to ROOT file via uproot ──────────────────────────────────────
    np_branches = {k: np.array(v, dtype=np.float64) for k, v in branches.items()}

    with uproot.recreate(outfile) as root_file:
        root_file["data"] = np_branches

    print(f"Saved: {outfile}")


def main():
    if len(sys.argv) <= 1:
        usage()
        sys.exit(1)

    convert(sys.argv[1])


if __name__ == "__main__":
    main()
