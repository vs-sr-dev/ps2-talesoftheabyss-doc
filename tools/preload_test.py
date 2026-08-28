"""Does the packer that made this disc actually use the synthetic dictionary?

Section 4 of tales-blockcodec-doc measures 3,840 bytes of synthetic `(i, 0x00)`
and `(i, 0xFF)` pairs being written into the ring before the first token is
read, and section 7 warns that **a wrong dictionary still produces the right
length** -- a back-reference copies the same number of bytes whatever it copies,
so a length check cannot tell a correct ring from a garbage one.

Legendia (2005) dropped the preload from its decoder entirely, which meant its
packer had to have stopped emitting references into that region as well.  This
disc's decoder writes it -- both 256-iteration loops are in the disassembly at
`0x00122230` and `0x001225B0`.  This tool asks the other half of the question:
whether the *packer* put anything there to find.

It decodes a random sample of members twice, once with `tales_block.py`'s ring
as published and once with the same ring cleared to zeros, and reports how many
outputs differ -- and, separately, how many *lengths* differ, which is the
number that demonstrates section 7's warning on this disc rather than quoting
it.

`tales_block.py` itself is not modified.  Its `preload` function is rebound for
the duration of the second decode and put back.

    python tools/preload_test.py FILEDIR [--n 40] [--seed 7]
"""

import csv
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tales_block
from cvm import CVM
from cvm_census import members


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    d = argv[1]
    n = int(argv[argv.index('--n') + 1]) if '--n' in argv else 40
    seed = int(argv[argv.index('--seed') + 1]) if '--seed' in argv else 7

    rows = [r for r in members(d) if r[5] == 'codec block']
    random.Random(seed).shuffle(rows)
    rows = rows[:n]

    same = diff = badlen = 0
    for vol, path, off, size, stamp, kind, head in rows:
        c = CVM(os.path.join(d, vol + '.CVM'))
        c.f.seek(off)
        buf = c.f.read(size)
        a = tales_block.unpack(buf, 0, 'psx')
        keep = tales_block.preload
        tales_block.preload = lambda dialect: bytearray(tales_block.RING)
        try:
            b = tales_block.unpack(buf, 0, 'psx')
        finally:
            tales_block.preload = keep
        if a == b:
            same += 1
        else:
            diff += 1
        if len(a) != len(b):
            badlen += 1

    print('%d members decoded twice, preloaded ring vs empty ring' % len(rows))
    print('  byte-identical output      %d' % same)
    print('  different output           %d' % diff)
    print('  different *length*         %d' % badlen)
    print()
    print('A block whose output changes read the synthetic dictionary; a block')
    print('whose output does not may simply never have referenced it.  The last')
    print('line is the one section 7 warns about: a wrong dictionary still')
    print('produces the right length, so length alone proves nothing.')


if __name__ == '__main__':
    main(sys.argv)
