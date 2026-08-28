"""Longest identical byte run between one routine and a whole executable.

`xarch.py` answers a narrower question than it looks like it does.  It aligns
two routines the caller has already located and reports the longest identical
byte run *between those two windows*.  That is the right test when both
addresses are known and trusted, but it cannot distinguish "the decoder was
recompiled and moved" from "the decoder is not there at all", and it cannot
find a shared prefix that survived into some other routine.

This tool asks the whole-file version.  Take N bytes of A starting at a virtual
address, and find the longest run of those bytes that appears *anywhere* in B,
at any alignment, without being told where to look.  For the corpus's own
control -- Tales of Destiny 1997 against Tales of Eternia 2000 -- the answer is
212 bytes, which is the number tales-blockcodec-doc reports from a completely
different method, so a run of that magnitude is what a shared object looks like.

The search is a rolling hash over B's k-grams with a binary search on k, so it
is linear in the size of B per probe and finishes on a four-megabyte executable
in well under a second.  A match is verified against the actual bytes before it
is reported; the hash is only used to find candidates.

Controls are not optional.  Short runs occur by chance in any two MIPS
routines -- `nop` padding, common `addiu sp, sp, -N` prologues, `jr ra` -- so
every run this prints should be read against `--control`, which repeats the
search with an unrelated routine of the same length as the needle.  On this
corpus the noise floor is six to eight bytes.

    python tools/prefix_scan.py A.elf 0x0010CEB8 280 B.elf [B2.elf ...]
    python tools/prefix_scan.py A.elf 0x0010CEB8 280 B.elf --control 0x001BFC34
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dismips

BASE = 0x100000001B3
PRIME = (1 << 61) - 1


def load_image(path):
    """(bytes, mapper) where mapper(va) -> file offset or None."""
    data, _va, elf = dismips.load(path)
    if elf is not None:
        segs = [(p[2], p[2] + p[4], p[1]) for p in elf.phdrs if p[0] == 1]
        if not segs:
            # An IOP module is relocatable and carries no PT_LOAD, so its
            # addresses are section-relative; map through the section table.
            segs = [(sh[3], sh[3] + sh[5], sh[4]) for sh in elf.shdrs
                    if sh[1] == 1 and sh[5]]

        def mapper(va):
            for lo, hi, off in segs:
                if lo <= va < hi:
                    return off + va - lo
            return None
        return data, mapper
    if data[:8] == b'PS-X EXE':
        org = struct.unpack_from('<I', data, 0x18)[0]
        return data, lambda va: 0x800 + va - org
    return data, lambda va: va


def needle(path, va, n):
    data, mapper = load_image(path)
    off = mapper(va)
    if off is None:
        raise SystemExit('%s: 0x%08X is not in any loadable segment' % (path, va))
    return data[off:off + n], off


def kgram_index(hay, k):
    """{hash: [offset, ...]} over every k-byte window of hay."""
    if k <= 0 or len(hay) < k:
        return {}
    h = 0
    top = pow(BASE, k - 1, PRIME)
    idx = {}
    for i in range(k):
        h = (h * BASE + hay[i]) % PRIME
    idx.setdefault(h, []).append(0)
    for i in range(k, len(hay)):
        h = ((h - hay[i - k] * top) * BASE + hay[i]) % PRIME
        idx.setdefault(h, []).append(i - k + 1)
    return idx


def match_at_length(nee, hay, k):
    """(offset_in_needle, offset_in_hay) for some common k-gram, or None."""
    if k <= 0:
        return (0, 0)
    if len(nee) < k or len(hay) < k:
        return None
    idx = kgram_index(hay, k)
    h = 0
    top = pow(BASE, k - 1, PRIME)
    for i in range(k):
        h = (h * BASE + nee[i]) % PRIME
    for i in range(len(nee) - k + 1):
        if i:
            h = ((h - nee[i - 1] * top) * BASE + nee[i + k - 1]) % PRIME
        for j in idx.get(h, ()):
            if nee[i:i + k] == hay[j:j + k]:      # verify, never trust the hash
                return (i, j)
    return None


def longest_run(nee, hay):
    """Longest run of needle bytes appearing anywhere in hay."""
    lo, hi, best = 1, min(len(nee), len(hay)), (0, 0, 0)
    while lo <= hi:
        mid = (lo + hi) // 2
        m = match_at_length(nee, hay, mid)
        if m:
            best = (mid, m[0], m[1])
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def report(nee, path, label=''):
    data, _ = load_image(path)
    run, a, b = longest_run(nee, data)
    print('  %-18s %5d bytes  (needle+%d, %s+0x%X)%s'
          % (os.path.basename(path), run, a, os.path.basename(path), b,
             '  ' + label if label else ''))
    return run


def main(argv):
    skip = set()
    if '--control' in argv:
        skip.add(argv.index('--control') + 1)
    args = [x for i, x in enumerate(argv)
            if i and not x.startswith('--') and i not in skip]
    if len(args) < 4:
        raise SystemExit(__doc__)
    apath, va, n = args[0], int(args[1], 0), int(args[2], 0)
    nee, off = needle(apath, va, n)
    print('needle  %s  va 0x%08X  file 0x%X  %d bytes'
          % (os.path.basename(apath), va, off, len(nee)))
    print('longest run of those bytes appearing anywhere in:')
    for h in args[3:]:
        report(nee, h)
    if '--control' in argv:
        cva = int(argv[argv.index('--control') + 1], 0)
        cnee, _ = needle(apath, cva, n)
        print('control: an unrelated routine of the same length, va 0x%08X' % cva)
        for h in args[3:]:
            report(cnee, h)


if __name__ == '__main__':
    main(sys.argv)
