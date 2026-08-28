"""Compare this build's block decoder against the PlayStation ones.

tales-blockcodec-doc already showed that the 1997 and 2000 PlayStation
builds share 212 bytes of *identical machine code*.  The 2002 build cannot,
because it is compiled for a different CPU: the EE is an R5900 and its
compiler emits `daddu` where the R3000A compiler emits `addu`.  Byte
equality is therefore the wrong question, and this tool asks the right one.

It aligns two routines word by word and reports three things:

    identical     the whole 32-bit word matches, registers included
    same opcode   the instruction is the same, the registers differ
    structural    the *sequence* of opcodes matches after ignoring
                  register numbers, immediates aside

A routine recompiled from the same source scores high on "same opcode" and
low on "identical".  A routine written independently scores low on both,
because nobody else unrolls a 256-iteration dictionary fill by eight.

Usage:
    python tools/decoder_lineage.py A.EXE 0x80023504 B.ELF 0x0010A1B0 [words]
"""

import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dismips import load, disasm

MNEM = None


def words(path, addr, n):
    d, va, e = load(path)
    off = None
    if e is None:
        if d[:8] == b'PS-X EXE':
            org = struct.unpack_from('<I', d, 0x18)[0]
            off = 0x800 + addr - org
        else:
            off = addr
    else:
        for p in e.phdrs:
            if p[0] == 1 and p[2] <= addr < p[2] + p[4]:
                off = p[1] + addr - p[2]
    if off is None:
        raise SystemExit('%s: 0x%08X not mapped' % (path, addr))
    return [struct.unpack_from('<I', d, off + 4 * i)[0] for i in range(n)], addr


def mnemonic(w, pc):
    return disasm(w, pc).split()[0]


def immediates(w):
    op = w >> 26
    if op == 0:
        return None
    if op in (2, 3):
        return None
    return w & 0xFFFF


def main(argv):
    if len(argv) < 5:
        print(__doc__)
        return 2
    pa, aa, pb, ab = argv[1], int(argv[2], 0), argv[3], int(argv[4], 0)
    n = int(argv[5]) if len(argv) > 5 else 140
    wa, basea = words(pa, aa, n)
    wb, baseb = words(pb, ab, n)

    ident = same_op = 0
    run = 0
    best_run = 0
    print('%-6s %-9s %-34s %-9s %-34s %s'
          % ('#', 'A', '', 'B', '', 'VERDICT'))
    for i in range(n):
        da = disasm(wa[i], basea + 4 * i)
        db = disasm(wb[i], baseb + 4 * i)
        ma, mb = da.split()[0], db.split()[0]
        if wa[i] == wb[i]:
            v = 'identical'
            ident += 1
            same_op += 1
            run += 1
            best_run = max(best_run, run)
        elif ma == mb:
            v = 'same opcode'
            same_op += 1
            run = 0
        else:
            v = ''
            run = 0
        if i < 48:
            print('%-6d 0x%08X %-34s 0x%08X %-34s %s'
                  % (i, basea + 4 * i, da, baseb + 4 * i, db, v))
    print()
    print('A                %s @ 0x%08X' % (pa, aa))
    print('B                %s @ 0x%08X' % (pb, ab))
    print('words compared   %d' % n)
    print('identical words  %d (%.1f%%)' % (ident, 100 * ident / n))
    print('longest identical run %d words / %d bytes' % (best_run, best_run * 4))
    print('same opcode      %d (%.1f%%)' % (same_op, 100 * same_op / n))
    # opcode sequence similarity, alignment-free
    sa = [mnemonic(w, basea + 4 * i) for i, w in enumerate(wa)]
    sb = [mnemonic(w, baseb + 4 * i) for i, w in enumerate(wb)]
    import difflib
    r = difflib.SequenceMatcher(None, sa, sb).ratio()
    print('opcode sequence  %.1f%% similar (ignoring registers and scheduling)'
          % (100 * r))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
