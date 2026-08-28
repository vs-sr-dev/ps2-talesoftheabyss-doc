"""Decode every block on this disc with the unmodified reference decoder.

The census walks the containers rather than sweeping bytes, because on this
disc the containers are readable: nine CRI `ROFS` volumes, then `AFS` archives
and the in-house `FPS3` / `FPS2` archives inside them, then the leaves.  Every
leaf is offered to `tales_block.py` exactly as it sits, and a leaf counts as a
block only if the decoded length equals the length its own header declares.

`tales_block.py` is the corpus copy, md5 e2dcd6b8dc717b84f67bf8a46568298c, with
no edit of any kind.  If it needed one, that would be the result.

Three things this deliberately does not do.  It does not decide what a member
is from its name -- the same `.PKB` extension covers a raw codec block, an
`FPS2` archive and a bespoke index.  It does not trust the unpacked size field:
that field is what is being *checked*, and section 1 of the specification warns
it is advisory.  And it does not stop at the first level: 51% of the blocks
here are nested one or two containers deep, so a top-level census undercounts
by half.

    python tools/codec_census.py FILEDIR                # totals
    python tools/codec_census.py FILEDIR --csv          # one line per block
    python tools/codec_census.py FILEDIR --limit N      # first N leaves
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tales_block
import fps
from cvm import CVM

VOLUMES = ['TO7ROOT', 'TO7FIELD', 'TO7MAP', 'TO7BTL', 'TO7NPC',
           'TO7EV', 'TO7MOV', 'TO7BGM', 'TO7SE']
SECTOR = 2048


def afs_members(d):
    """[(index, name, offset, size)] for a CRI AFS archive held in `d`."""
    if d[:4] != b'AFS\x00':
        return []
    n = struct.unpack_from('<I', d, 4)[0]
    if n > 1 << 20:
        return []
    ext = []
    for i in range(n):
        o, s = struct.unpack_from('<II', d, 8 + 8 * i)
        ext.append((o, s))
    dir_off, dir_size = struct.unpack_from('<II', d, 8 + 8 * n)
    names = {}
    if dir_off and dir_off + dir_size <= len(d) and dir_size >= 48 * n:
        for i in range(n):
            rec = d[dir_off + 48 * i:dir_off + 48 * i + 48]
            names[i] = rec[:32].rstrip(b'\x00').decode('shift_jis', 'replace')
    out = []
    for i, (o, s) in enumerate(ext):
        if s and o + s <= len(d):
            out.append((i, names.get(i, ''), o, s))
    return out


def is_block(head, size):
    if size < 9 or len(head) < 9 or head[0] not in (0, 1, 3):
        return False
    packed = struct.unpack_from('<I', head, 1)[0]
    unpacked = struct.unpack_from('<I', head, 5)[0]
    if not packed or not unpacked or unpacked >= (1 << 28):
        return False
    return 9 + packed <= size


def block_run(d):
    """[(offset, packed)] if `d` is a flat run of sector-aligned blocks.

    Several of this disc's largest members carry no header of their own: they
    are simply one nine-byte block after another, each starting on a 2,048-byte
    boundary so the loader can seek to one without reading the ones before it.
    `F0.PKF` is 37,951,488 bytes and 292 blocks, and a census that stops at the
    member level misses 545 MB that way.  A run is accepted only if the walk
    reaches the end of the member, which is what stops an ordinary file whose
    first byte happens to be 1 or 3 from being mistaken for one.
    """
    off, out = 0, []
    while off + 9 <= len(d):
        m = d[off]
        packed = struct.unpack_from('<I', d, off + 1)[0]
        unpacked = struct.unpack_from('<I', d, off + 5)[0]
        if m not in (0, 1, 3) or not packed or not unpacked:
            return []
        if off + 9 + packed > len(d) or unpacked >= (1 << 28):
            return []
        out.append((off, packed))
        nxt = off + 9 + packed
        off = (nxt + SECTOR - 1) // SECTOR * SECTOR
        if off >= len(d):
            break
    return out if len(out) > 1 and off >= len(d) - SECTOR else []


def leaves(d, path, depth=0):
    """Yield (path, bytes) for every payload inside `d`, containers opened."""
    if depth > 3:
        yield (path, d)
        return
    if d[:4] == b'AFS\x00':
        ms = afs_members(d)
        if ms:
            for i, name, o, s in ms:
                sub = d[o:o + s]
                for r in leaves(sub, '%s/[%d]%s' % (path, i, name), depth + 1):
                    yield r
            return
    if d[:4] in (b'FPS3', b'FPS2'):
        ms = fps.members(d)
        if ms:
            seen = set()
            for i, ext, o, s in ms:
                if (o, s) in seen:
                    continue
                seen.add((o, s))
                for r in leaves(d[o:o + s], '%s/[%d].%s' % (path, i, ext),
                                depth + 1):
                    yield r
            return
    run = block_run(d)
    if run:
        for i, (o, packed) in enumerate(run):
            yield ('%s#%d' % (path, i), d[o:o + 9 + packed])
        return
    yield (path, d)


def census(d, limit=None, emit=None):
    tot = {'leaves': 0, 'blocks': 0, 'ok': 0, 'bad': 0,
           'packed': 0, 'unpacked': 0, 'stored': 0, 'm1': 0, 'm3': 0}
    for v in VOLUMES:
        p = os.path.join(d, v + '.CVM')
        if not os.path.exists(p):
            continue
        c = CVM(p)
        for e in c.walk():
            if e.is_dir:
                continue
            c.f.seek(c.base + e.lba * SECTOR)
            data = c.f.read(e.size)
            for path, buf in leaves(data, '%s:/%s' % (v, e.path)):
                tot['leaves'] += 1
                if not is_block(buf[:9], len(buf)):
                    continue
                m = buf[0]
                packed = struct.unpack_from('<I', buf, 1)[0]
                declared = struct.unpack_from('<I', buf, 5)[0]
                tot['blocks'] += 1
                try:
                    out = tales_block.unpack(buf, 0, 'psx')
                    good = len(out) == declared
                except Exception:
                    out, good = b'', False
                tot['ok' if good else 'bad'] += 1
                if good:
                    tot['packed'] += packed
                    tot['unpacked'] += declared
                    tot[{0: 'stored', 1: 'm1', 3: 'm3'}[m]] += 1
                if emit:
                    emit(path, m, packed, declared, len(out), good)
                if limit and tot['blocks'] >= limit:
                    return tot
    return tot


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    d = argv[1]
    limit = int(argv[argv.index('--limit') + 1]) if '--limit' in argv else None
    emit = None
    if '--csv' in argv:
        print('path,method,packed,declared,got,ok')
        emit = lambda p, m, pk, de, go, ok: print(
            '%s,%d,%d,%d,%d,%d' % (p, m, pk, de, go, 1 if ok else 0))
    t = census(d, limit, emit)
    if '--csv' in argv:
        return
    print('leaves examined      %d' % t['leaves'])
    print('codec blocks         %d' % t['blocks'])
    print('  decode to declared %d' % t['ok'])
    print('  do not             %d' % t['bad'])
    print('  method 0 / stored  %d' % t['stored'])
    print('  method 1           %d' % t['m1'])
    print('  method 3           %d' % t['m3'])
    print('packed bytes         %d' % t['packed'])
    print('unpacked bytes       %d' % t['unpacked'])
    if t['packed']:
        print('ratio                %.2fx' % (t['unpacked'] / t['packed']))


if __name__ == '__main__':
    main(sys.argv)
