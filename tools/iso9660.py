"""ISO 9660 volume and directory walker for PlayStation 2 DVD images.

PS2 discs are plain ISO 9660 Level 1 (8.3 names, ";1" version suffix) in
2,048-byte user sectors with no subheader, so the image is a flat array of
logical blocks and LBA * 2048 is a file offset.  Unlike the PS1 discs in the
sibling pipelines there is no CD-XA signature at PVD+0x400 and no fourteen-byte
XA extension on the directory records.

Usage:
    python tools/iso9660.py IMAGE.iso            # tree listing
    python tools/iso9660.py IMAGE.iso --pvd      # volume descriptors
    python tools/iso9660.py IMAGE.iso --extract OUTDIR
    python tools/iso9660.py IMAGE.iso --csv      # name,lba,size,date
"""

import csv
import os
import struct
import sys

SECTOR = 2048


def u16(b, o):
    return struct.unpack_from('<H', b, o)[0]


def u32(b, o):
    return struct.unpack_from('<I', b, o)[0]


class Entry:
    __slots__ = ('name', 'lba', 'size', 'flags', 'date', 'path', 'unit', 'gap')

    def __init__(self, rec):
        self.lba = u32(rec, 2)
        self.size = u32(rec, 10)
        self.date = tuple(rec[18:25])
        self.flags = rec[25]
        self.unit = rec[26]
        self.gap = rec[27]
        nlen = rec[32]
        raw = rec[33:33 + nlen]
        if nlen == 1 and raw in (b'\x00', b'\x01'):
            self.name = '.' if raw == b'\x00' else '..'
        else:
            self.name = raw.decode('shift_jis', 'replace')
        self.path = self.name

    @property
    def is_dir(self):
        return bool(self.flags & 0x02)

    @property
    def base(self):
        return self.name.split(';')[0]

    @property
    def sectors(self):
        return (self.size + SECTOR - 1) // SECTOR

    def stamp(self):
        y, m, d, hh, mm, ss, tz = self.date
        return '%04d-%02d-%02d %02d:%02d:%02d %+d' % (
            1900 + y, m, d, hh, mm, ss, tz - 256 if tz > 127 else tz)


class Image:
    """A PS2 disc image addressed by logical block."""

    def __init__(self, path):
        self.path = path
        self.f = open(path, 'rb')
        self.f.seek(0, 2)
        self.bytes = self.f.tell()
        self.sectors = self.bytes // SECTOR

    def read(self, lba, count=1):
        self.f.seek(lba * SECTOR)
        return self.f.read(count * SECTOR)

    def read_file(self, entry):
        self.f.seek(entry.lba * SECTOR)
        return self.f.read(entry.size)

    def descriptors(self):
        out = []
        lba = 16
        while lba < self.sectors:
            d = self.read(lba)
            if d[1:6] != b'CD001':
                break
            out.append((lba, d))
            if d[0] == 255:
                break
            lba += 1
        return out

    def pvd(self):
        for lba, d in self.descriptors():
            if d[0] == 1:
                return d
        raise ValueError('no primary volume descriptor')

    def walk(self):
        """Depth-first walk of the directory tree.  Yields Entry with .path."""
        pvd = self.pvd()
        root = Entry(pvd[156:190])
        root.path = ''
        stack = [root]
        while stack:
            d = stack.pop(0)
            for e in self.records(d):
                if e.name in ('.', '..'):
                    continue
                e.path = (d.path + '/' + e.base) if d.path else e.base
                yield e
                if e.is_dir:
                    stack.append(e)

    def records(self, direntry):
        data = self.read(direntry.lba, direntry.sectors)
        out = []
        for s in range(direntry.sectors):
            o = s * SECTOR
            end = min(o + SECTOR, len(data))
            while o < end:
                ln = data[o]
                if ln == 0:
                    break
                out.append(Entry(data[o:o + ln]))
                o += ln
        return out


def cmd_pvd(img):
    for lba, d in img.descriptors():
        kind = {0: 'boot record', 1: 'primary', 2: 'supplementary',
                3: 'partition', 255: 'terminator'}.get(d[0], '?')
        print('LBA %-5d  type %-3d  %s' % (lba, d[0], kind))
        if d[0] != 1:
            continue
        print('  system id      %s' % d[8:40].decode('ascii', 'replace').rstrip())
        print('  volume id      %s' % d[40:72].decode('ascii', 'replace').rstrip())
        print('  volume space   %d sectors (%d bytes)'
              % (u32(d, 80), u32(d, 80) * SECTOR))
        print('  block size     %d' % u16(d, 128))
        print('  path table     %d bytes at LBA %d (L) / %d (M)'
              % (u32(d, 132), u32(d, 140), struct.unpack_from('>I', d, 148)[0]))
        for label, off in (('publisher', 318), ('preparer', 446),
                           ('application', 574)):
            v = d[off:off + 128].decode('ascii', 'replace').rstrip()
            if v:
                print('  %-14s %s' % (label, v))
        for label, off in (('created', 813), ('modified', 830),
                           ('expires', 847), ('effective', 864)):
            print('  %-14s %s' % (label, d[off:off + 17].decode('ascii', 'replace')))
    print('image           %d bytes / %d sectors' % (img.bytes, img.sectors))


def cmd_list(img, as_csv=False):
    entries = sorted(img.walk(), key=lambda e: e.lba)
    if as_csv:
        w = csv.writer(sys.stdout, lineterminator='\n')
        w.writerow(['path', 'lba', 'size', 'sectors', 'dir', 'date'])
        for e in entries:
            w.writerow([e.path, e.lba, e.size, e.sectors,
                        int(e.is_dir), e.stamp()])
        return
    files = [e for e in entries if not e.is_dir]
    dirs = [e for e in entries if e.is_dir]
    print('%-8s %10s %12s  %s' % ('LBA', 'SECTORS', 'BYTES', 'PATH'))
    for e in entries:
        print('%-8d %10d %12d  %s%s'
              % (e.lba, e.sectors, e.size, e.path, '/' if e.is_dir else ''))
    print()
    print('%d files, %d directories, %d bytes'
          % (len(files), len(dirs), sum(e.size for e in files)))


def cmd_extract(img, outdir):
    n = 0
    for e in img.walk():
        dest = os.path.join(outdir, e.path.replace('/', os.sep))
        if e.is_dir:
            os.makedirs(dest, exist_ok=True)
            continue
        os.makedirs(os.path.dirname(dest) or '.', exist_ok=True)
        with open(dest, 'wb') as o:
            img.f.seek(e.lba * SECTOR)
            left = e.size
            while left:
                chunk = img.f.read(min(left, 1 << 22))
                if not chunk:
                    break
                o.write(chunk)
                left -= len(chunk)
        n += 1
        print('%-40s %10d' % (e.path, e.size))
    print('%d files -> %s' % (n, outdir))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    img = Image(argv[1])
    rest = argv[2:]
    if '--pvd' in rest:
        cmd_pvd(img)
    elif '--extract' in rest:
        cmd_extract(img, rest[rest.index('--extract') + 1])
    else:
        cmd_list(img, '--csv' in rest)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
