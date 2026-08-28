"""The two in-house archive headers on this disc: `FPS3` and `FPS2`.

Neither is CRI's.  Both are a magic, a slot count and a flat table of fixed
slots, and both allow a slot to be empty -- which is the point of documenting
them rather than guessing, because the empty marker is different in each and
reading past the table walks straight into the payload.

    FPS3                                 FPS2
    +0x00  "FPS3"                        +0x00  "FPS2"
    +0x04  u32  slot count               +0x04  u32  slot count
    +0x08  u32  table offset (0x1C)      +0x08  u32  zero
    +0x0C  u32  first data offset        +0x0C  u32  zero
    +0x10  ...  three more u32           +0x40  table
    +0x1C  table
    slot: u32 offset, u32 size, char[4]  slot: char[4], u32 offset, u32 size

`FPS3` marks an empty slot with an offset of `0xFFFFFFFF`; `FPS2` leaves the
tail of its table filled with `0xFE`, so a slot whose offset is `0xFEFEFEFE`
is not a slot.  In both, the table ends where the first payload begins, and
that -- not the count field -- is the bound to trust: on this disc every
`FPS2` declares 67 slots and none has more than seven real ones, so a reader
that believes the count reads the payload as though it were a directory.

Slots may repeat: an `FPS3` frequently lists the same (offset, size) twice
under the same extension, so member counts here are slots, not distinct
payloads, and both numbers are reported.

    python tools/fps.py FILE
"""

import struct
import sys

EMPTY = (0xFFFFFFFF, 0xFEFEFEFE, 0)


def members(d, base=0):
    """[(index, ext, offset, size)] for one FPS3/FPS2 archive in `d`."""
    if len(d) < 16:
        return []
    magic = d[:4]
    if magic == b'FPS3':
        n = struct.unpack_from('<I', d, 4)[0]
        table = struct.unpack_from('<I', d, 8)[0]
        first = struct.unpack_from('<I', d, 12)[0]
        order = 'ose'
    elif magic == b'FPS2':
        n = struct.unpack_from('<I', d, 4)[0]
        table, first, order = 0x40, None, 'eos'
    else:
        return []
    out = []
    for i in range(n):
        o = table + 12 * i
        if o + 12 > len(d):
            break
        if first is not None and o + 12 > first:
            break
        if order == 'ose':
            off, size, ext = struct.unpack_from('<II4s', d, o)
        else:
            ext, off, size = struct.unpack_from('<4sII', d, o)
        if off in EMPTY or size in EMPTY or not size:
            continue
        if off + size > len(d):
            continue
        # The table cannot extend past the payload it points at.
        if first is None and o + 12 > off:
            break
        out.append((i, ext.rstrip(b'\x00').decode('ascii', 'replace'),
                    base + off, size))
    return out


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    d = open(argv[1], 'rb').read()
    ms = members(d)
    print('%-5s %-6s %-12s %10s  %s' % ('SLOT', 'EXT', 'OFFSET', 'BYTES', 'HEAD'))
    for i, ext, off, size in ms:
        print('%-5d %-6s 0x%08X   %10d  %s'
              % (i, ext, off, size, d[off:off + 9].hex()))
    distinct = len({(o, s) for _, _, o, s in ms})
    print()
    print('%d slots used, %d distinct payloads' % (len(ms), distinct))


if __name__ == '__main__':
    main(sys.argv)
