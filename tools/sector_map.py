"""Account for every sector of the PlayStation 2 DVD.

A PS2 disc image is a flat array of 2,048-byte sectors, so a file's extent
is exactly LBA .. LBA + ceil(size / 2048).  Anything not covered by the
volume descriptors, the path tables or a file is slack, and slack is where
the mastering tool's leftovers live.

Usage:
    python tools/sector_map.py IMAGE.iso            # the layout
    python tools/sector_map.py IMAGE.iso --slack    # only what nothing claims
    python tools/sector_map.py IMAGE.iso --dump N   # one sector, in hex
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso9660 import Image, SECTOR


def claim(img):
    """[(first_lba, last_lba, what)] for everything the volume describes."""
    out = [(0, 15, '<system area>')]
    for lba, d in img.descriptors():
        out.append((lba, lba, '<volume descriptor type %d>' % d[0]))
    pvd = img.pvd()
    import struct
    ptl = struct.unpack_from('<I', pvd, 140)[0]
    ptm = struct.unpack_from('>I', pvd, 148)[0]
    ptsize = struct.unpack_from('<I', pvd, 132)[0]
    n = max(1, (ptsize + SECTOR - 1) // SECTOR)
    out.append((ptl, ptl + n - 1, '<path table, L>'))
    out.append((ptm, ptm + n - 1, '<path table, M>'))
    for e in img.walk():
        span = max(1, e.sectors)
        out.append((e.lba, e.lba + span - 1,
                    e.path + ('/' if e.is_dir else '')))
    return sorted(out)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    img = Image(argv[1])
    rest = argv[2:]

    if '--dump' in rest:
        lba = int(rest[rest.index('--dump') + 1], 0)
        d = img.read(lba)
        for i in range(0, SECTOR, 32):
            row = d[i:i + 32]
            print('%08X  %-64s %s'
                  % (lba * SECTOR + i, row.hex(),
                     ''.join(chr(c) if 32 <= c < 127 else '.' for c in row)))
        return 0

    claims = claim(img)
    slack = []
    cursor = 0
    for first, last, what in claims:
        if first > cursor:
            slack.append((cursor, first - 1))
        cursor = max(cursor, last + 1)
    if cursor < img.sectors:
        slack.append((cursor, img.sectors - 1))

    if '--slack' not in rest:
        print('%-9s %-9s %-9s %s' % ('FIRST', 'LAST', 'SECTORS', 'WHAT'))
        for first, last, what in claims:
            print('%-9d %-9d %-9d %s' % (first, last, last - first + 1, what))
        print()

    print('%-9s %-9s %-9s %s' % ('FIRST', 'LAST', 'SECTORS', 'CONTENT'))
    total = 0
    for first, last in slack:
        n = last - first + 1
        total += n
        d = img.read(first, min(n, 1))
        kind = 'all zero' if not any(d) else ('all 0x%02X' % d[0]
                                              if len(set(d)) == 1
                                              else 'data: ' + d[:16].hex())
        print('%-9d %-9d %-9d %s' % (first, last, n, kind))
    print()
    print('image      %d sectors (%d bytes)' % (img.sectors, img.bytes))
    print('slack      %d sectors (%.4f%% of the disc)'
          % (total, 100 * total / img.sectors))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
