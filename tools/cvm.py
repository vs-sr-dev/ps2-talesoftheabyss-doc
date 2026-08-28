"""Read a CRI `CVM` container -- the PlayStation 2 release's file system.

The 2002 PlayStation 2 title in this corpus put its assets in `FILE.FPB`, a
headerless archive whose directory was compiled into the executable.  The 2004
one does not: its disc holds ten `CVM` files, and a `CVM` is CRI Middleware's
ROFS container -- a small header followed by an ordinary ISO 9660 volume.  So
the game's file system is a file system, with names and dates, and the index
trick of 2002 is gone.

The header is worth reading rather than skipping.  It carries the name and
version of the tool that built it and the date that tool was built, which is
the closest thing on either disc to a build stamp.

    python tools/cvm.py FILE.CVM --header
    python tools/cvm.py FILE.CVM --list
    python tools/cvm.py FILE.CVM --extract OUTDIR/
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import iso9660

SECTOR = 2048
# The ISO 9660 volume inside a CVM starts three sectors in: the container's
# own header occupies the first two and the volume's system area the rest.
ISO_BASE = 0x1800


class CVM(iso9660.Image):

    def __init__(self, path):
        iso9660.Image.__init__(self, path)
        self.f.seek(0)
        h = self.f.read(0x100)
        if h[:4] != b'CVMH':
            raise SystemExit('%s: no CVMH signature' % path)
        self.header_size = struct.unpack_from('>I', h, 8)[0]
        self.volume_size = struct.unpack_from('>I', h, 0x20)[0]
        end = h.find(b'\0', 0x36)
        self.fs_type = h[0x34:0x38].decode('ascii', 'replace')
        self.builder = h[0x38:end].decode('ascii', 'replace')
        self.base = ISO_BASE
        self.sectors = (self.bytes - self.base) // SECTOR

    def read(self, lba, count=1):
        self.f.seek(self.base + lba * SECTOR)
        return self.f.read(count * SECTOR)

    def read_file(self, entry):
        self.f.seek(self.base + entry.lba * SECTOR)
        return self.f.read(entry.size)

    def files(self):
        """[(path, absolute file offset, length)] -- offsets into the CVM
        itself, so the caller can hash without extracting."""
        out = []
        for e in self.walk():
            if not e.is_dir:
                out.append(('/' + e.path, self.base + e.lba * SECTOR, e.size))
        return out


def header(c):
    pvd = c.pvd()
    print('%-20s %s' % ('container', os.path.basename(c.path)))
    print('%-20s %d bytes' % ('file size', c.bytes))
    print('%-20s %d' % ('header size field', c.header_size))
    print('%-20s %d' % ('volume size field', c.volume_size))
    print('%-20s %s' % ('file system', c.fs_type))
    print('%-20s %s' % ('built by', c.builder))
    print('%-20s %s' % ('volume id',
                        pvd[40:72].decode('ascii', 'replace').strip()))
    print('%-20s %s' % ('publisher',
                        pvd[318:446].decode('ascii', 'replace').strip()))
    print('%-20s %s' % ('application',
                        pvd[574:702].decode('ascii', 'replace').strip()))
    print('%-20s %s' % ('created',
                        pvd[813:830].decode('ascii', 'replace')))
    print('%-20s %d sectors' % ('volume space',
                                struct.unpack_from('<I', pvd, 80)[0]))
    fs = c.files()
    print('%-20s %d files, %d bytes' %
          ('contents', len(fs), sum(x[2] for x in fs)))


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    c = CVM(argv[1])
    if '--header' in argv:
        header(c)
    elif '--list' in argv:
        print('%-12s %10s  %s' % ('OFFSET', 'BYTES', 'PATH'))
        for p, o, l in c.files():
            print('0x%08X   %10d  %s' % (o, l, p))
        fs = c.files()
        print()
        print('%d files, %d bytes' % (len(fs), sum(x[2] for x in fs)))
    elif '--extract' in argv:
        out = argv[argv.index('--extract') + 1]
        for p, o, l in c.files():
            dst = os.path.join(out, p.lstrip('/'))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            c.f.seek(o)
            with open(dst, 'wb') as g:
                left = l
                while left:
                    b = c.f.read(min(left, 1 << 20))
                    g.write(b)
                    left -= len(b)
        print('extracted %d files' % len(c.files()))
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main(sys.argv)
