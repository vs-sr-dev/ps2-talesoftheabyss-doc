"""Turn a raw image offset into "which file, and what is around it".

A signature sweep over a whole disc image produces counts, and a count on its
own is not a result.  A four-byte pattern occurs about once by chance in 4 GB
and a three-byte pattern about 260 times, so every non-zero line in a sweep has
to be read before it can be called a hit or dismissed as noise -- and reading
it means knowing which of the disc's files the offset fell in, and whether the
bytes around it look like a header or like the middle of a video stream.

This does both.  It builds the extent table once from the ISO 9660 directory
and, for the nine `CVM` volumes, from their inner directories as well, so an
offset inside `TO7EV.CVM` is reported as the member it landed in rather than as
the gigabyte-sized container.

    python tools/locate.py IMAGE.iso 0x12B20754 [0x...]
    python tools/locate.py IMAGE.iso --pattern "CPS\\x00"
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import iso9660

SECTOR = 2048


def extents(path):
    """[(start, end, label)] over the whole image, innermost last."""
    img = iso9660.Image(path)
    out = []
    inner = []
    for e in img.walk():
        if e.is_dir:
            continue
        start = e.lba * SECTOR
        out.append((start, start + e.size, e.path))
        if e.path.endswith('.CVM'):
            inner.append((start, e.path))
    # The CVM inner volumes are read directly rather than through cvm.CVM,
    # because each container is embedded in a larger image here.
    for base, name in inner:
        f = open(path, 'rb')
        f.seek(base)
        if f.read(4) != b'CVMH':
            continue
        iso_base = base + 0x1800
        sub = _walk_embedded(f, iso_base)
        for lba, size, p in sub:
            s = iso_base + lba * SECTOR
            out.append((s, s + size, '%s:/%s' % (name, p)))
        f.close()
    out.sort()
    return out


def _walk_embedded(f, base):
    """(lba, size, path) for an ISO 9660 volume starting at byte `base`."""
    f.seek(base + 16 * SECTOR)
    pvd = f.read(SECTOR)
    if pvd[1:6] != b'CD001':
        return []
    root = iso9660.Entry(pvd[156:190])
    out = []
    stack = [(root.lba, root.size, '')]
    seen = set()
    while stack:
        lba, size, prefix = stack.pop()
        if (lba, size) in seen:
            continue
        seen.add((lba, size))
        f.seek(base + lba * SECTOR)
        blob = f.read(size)
        o = 0
        while o < len(blob):
            ln = blob[o]
            if ln == 0:
                o = (o // SECTOR + 1) * SECTOR
                continue
            e = iso9660.Entry(blob[o:o + ln])
            o += ln
            if e.name in ('.', '..'):
                continue
            p = prefix + e.name.split(';')[0]
            if e.is_dir:
                stack.append((e.lba, e.size, p + '/'))
            else:
                out.append((e.lba, e.size, p))
    return out


def find(ext, off):
    best = None
    for s, e, label in ext:
        if s <= off < e:
            if best is None or (e - s) <= (best[1] - best[0]):
                best = (s, e, label)
    return best


def main(argv):
    if len(argv) < 3:
        raise SystemExit(__doc__)
    path = argv[1]
    ext = extents(path)
    f = open(path, 'rb')
    for a in argv[2:]:
        off = int(a, 0)
        hit = find(ext, off)
        f.seek(max(0, off - 16))
        ctx = f.read(48)
        print('0x%010X  %s' % (off, hit[2] if hit else '(outside every file)'))
        if hit:
            print('              +0x%X into a %d-byte member'
                  % (off - hit[0], hit[1] - hit[0]))
        print('              %s' % ctx.hex(' '))
        print('              %s' % ''.join(
            chr(c) if 32 <= c < 127 else '.' for c in ctx))


if __name__ == '__main__':
    main(sys.argv)
