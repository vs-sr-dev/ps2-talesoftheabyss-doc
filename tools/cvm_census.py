"""Every member of every `CVM` on this disc, classified by its own bytes.

The nine `.CVM` files are CRI `ROFS` volumes -- a 0x1800-byte container header
followed by an ordinary ISO 9660 volume -- so unlike the `AFS` directories of
the 2005 sibling title they carry real per-member directory records, with real
dates.  That makes this disc the first in the corpus where the asset timeline
can be read off the container instead of being inferred from middleware build
stamps.

Classification is by magic, never by extension.  Several of this disc's own
container types are not distinguished by their names at all, and the codec
block has no magic either -- it is recognised by the shape section 1 of
tales-blockcodec-doc describes: a method byte of 0, 1 or 3, a packed size that
lands on the end of the member, and an unpacked size that is not absurd.  That
test is applied here rather than assumed, and members that fail every test are
reported as `?` with their first four bytes, so nothing is silently binned.

    python tools/cvm_census.py FILEDIR            # per-volume summary
    python tools/cvm_census.py FILEDIR --csv      # one line per member
    python tools/cvm_census.py FILEDIR --kinds    # totals by class
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cvm import CVM

VOLUMES = ['TO7ROOT', 'TO7FIELD', 'TO7MAP', 'TO7BTL', 'TO7NPC',
           'TO7EV', 'TO7MOV', 'TO7BGM', 'TO7SE']

# (magic bytes, offset, label) -- checked in order.
MAGIC = [
    (b'FPS4', 0, 'FPS4'),
    (b'FPS3', 0, 'FPS3'),
    (b'FPS2', 0, 'FPS2'),
    (b'PAC!', 0, 'PAC!'),
    (b'RCP!', 0, 'RCP!'),
    (b'DBS!', 0, 'DBS!'),
    (b'HAD!', 0, 'HAD!'),
    (b'MWo3', 0, 'MWo3 overlay'),
    (b'SB7 ', 0, 'SB7'),
    (b'iSE2', 0, 'iSE2'),
    (b'SCEI', 0, 'SCEI sound bank'),
    (b'TO8SCEL', 0, 'TO8SCEL'),
    (b'CPS ', 0, 'CPS'),
    (b'AFS\x00', 0, 'AFS'),
    (b'SCPK', 0, 'SCPK'),
    (b'THEIRSCE', 0, 'THEIRSCE'),
    (b'\x00\x00\x01\xba', 0, 'MPEG-PS (Sofdec)'),
    (b'TIM2', 0, 'TIM2'),
    (b'VAGp', 0, 'VAGp'),
    (b'MSCF', 0, 'MSCF'),
    (b'CVMH', 0, 'CVMH'),
    (b'\x7fELF', 0, 'ELF'),
    (b'TLPS', 0, 'TLPS'),
    (b'TLPK', 0, 'TLPK'),
    (b'h4m', 0, 'h4m'),
]

VSSVER = bytes([0x34, 0x12, 0x01, 0x00])


def cri_stream(head):
    """ADX and AHX both begin 0x80 0x00 <u16be data offset>; byte +4 is the
    codec id.  The `(c)CRI` string sits just before the data, not at +4, so a
    census keyed on it at a fixed offset misses every stream on this disc."""
    if len(head) < 8 or head[0] != 0x80 or head[1] != 0x00:
        return None
    return {2: 'ADX', 3: 'ADX', 0x10: 'AHX', 0x11: 'AHX'}.get(head[4])


def block_shape(head, size):
    """True if `head` looks like a nine-byte codec block filling the member."""
    if size < 9 or len(head) < 9:
        return False
    if head[0] not in (0, 1, 3):
        return False
    packed = struct.unpack_from('<I', head, 1)[0]
    unpacked = struct.unpack_from('<I', head, 5)[0]
    if packed == 0 or unpacked == 0:
        return False
    if 9 + packed > size or 9 + packed + 2047 < size:
        return False
    return unpacked < (1 << 28)


def sniff(head, size):
    k = cri_stream(head)
    if k:
        return k
    for m, o, label in MAGIC:
        if head[o:o + len(m)] == m:
            return label
    if head[:4] == VSSVER:
        return 'VSSVER.SCC'
    if block_shape(head, size):
        return 'codec block'
    if head[:4] == b'\x00\x00\x00\x00':
        return 'zero-lead'
    return '?'


def members(d):
    """(volume, path, offset, size, stamp, kind, head4) over all volumes."""
    for v in VOLUMES:
        p = os.path.join(d, v + '.CVM')
        if not os.path.exists(p):
            continue
        c = CVM(p)
        for e in c.walk():
            if e.is_dir:
                continue
            off = c.base + e.lba * 2048
            c.f.seek(off)
            head = c.f.read(32)
            yield (v, '/' + e.path, off, e.size, e.stamp(),
                   sniff(head, e.size), head[:4].hex())


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    d = argv[1]
    rows = list(members(d))
    if '--csv' in argv:
        print('volume,path,offset,size,date,kind,head4')
        for r in rows:
            print('%s,%s,%d,%d,%s,%s,%s' % r)
        return
    if '--kinds' in argv:
        agg = {}
        for v, p, o, s, st, k, h in rows:
            n, b = agg.get(k, (0, 0))
            agg[k] = (n + 1, b + s)
        print('%-18s %7s %16s' % ('KIND', 'MEMBERS', 'BYTES'))
        for k in sorted(agg, key=lambda x: -agg[x][1]):
            print('%-18s %7d %16d' % (k, agg[k][0], agg[k][1]))
        print('%-18s %7d %16d' % ('TOTAL', len(rows), sum(r[3] for r in rows)))
        return
    print('%-10s %7s %14s  %-19s  %s' %
          ('VOLUME', 'MEMBERS', 'BYTES', 'EARLIEST', 'LATEST'))
    for v in VOLUMES:
        sub = [r for r in rows if r[0] == v]
        if not sub:
            continue
        ds = sorted(r[4] for r in sub)
        print('%-10s %7d %14d  %-19s  %s' %
              (v, len(sub), sum(r[3] for r in sub), ds[0][:19], ds[-1][:19]))
    print('%-10s %7d %14d' % ('TOTAL', len(rows), sum(r[3] for r in rows)))


if __name__ == '__main__':
    main(sys.argv)
