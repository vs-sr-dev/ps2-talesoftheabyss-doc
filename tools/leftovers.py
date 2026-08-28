"""What the executables say that the shipped game does not need them to say.

A retail disc is a build, and a build carries the parts of itself nobody
deleted: debug printf strings, placeholder identifiers, names for things that
are not there, and the version stamps of whatever libraries were linked in.
This tool pulls the printable runs out of an image and sorts them into the
categories that have paid off across this corpus, rather than dumping every
byte that happens to be in ASCII range.

The filter matters more than it looks.  MIPS code is dense with bytes in the
printable range, so a naive `strings` over a 1.2 MB executable returns about
three times as many lines of noise as of text.  Everything here has to be at
least eight characters, at least half letters, and drawn from a restricted
alphabet; `--raw` turns that off when you want to audit what it threw away.

`--sweep` is a different job in the same spirit: search the *whole disc image*,
byte by byte, for a fixed list of format signatures and cross-title names.  It
exists because several of this repository's results are negative -- no `MSCF`,
no CRI middleware, no other game's name anywhere -- and a negative is only worth
anything if the search that produced it is published with it.  The list is in
the source, the whole image is read, and the count is printed for every pattern
including the ones that are zero.

    python tools/leftovers.py FILE [FILE ...]
    python tools/leftovers.py FILE --raw
    python tools/leftovers.py FILE --category debug
    python tools/leftovers.py IMAGE.iso --sweep
"""

import os
import re
import sys

RUN = re.compile(rb'[\x20-\x7e]{8,}')
CLEAN = re.compile(rb'^[A-Za-z0-9 _.:%\-/\\()\[\]#,+*=!?\'"&@]+$')

CATEGORIES = [
    ('devkit', (r'host0:', r'hostfs', r'mass:', r'cdrom0:', r'\bDebug\b',
                r'debug window', r'\.elf\b', r'\.obj\b', r'\.c\b', r'\.cpp\b')),
    ('debug', (r'fatal', r'error', r'ERROR', r'assert', r'ASSERT', r'over!!',
               r'total : ', r'not found', r'illegal', r'Illegal', r'faild',
               r'failed')),
    ('placeholder', (r'00000', r'99X9', r'SAMPLE', r'sample', r'dummy',
                     r'DUMMY', r'test', r'TEST', r'XXX', r'TODO')),
    ('sdk', (r'PsII', r'sce[A-Z]', r'libpad', r'libmc', r'libmtap', r'libipu',
             r'libmpeg', r'libcdvd', r'libdma', r'libgraph', r'libkernl',
             r'libvu0', r'Sce[A-Z]', r'rom0:')),
    ('toolchain', (r'GCC', r'gcc', r'CodeWarrior', r'Metrowerks', r'MW MIPS',
                   r'Compiler', r'compiler', r'SN Systems', r'GNU')),
    ('save', (r'BISLPS', r'BASLUS', r'icon\.', r'\.sys\b', r'save', r'SAVE',
              r'POCKET', r'UNFORMAT', r'NOCARD')),
    ('section', (r'^\.[a-z]', )),
]


def strings(data, raw=False):
    for m in RUN.finditer(data):
        s = m.group()
        if not raw:
            if not CLEAN.match(s):
                continue
            letters = sum(1 for c in s if 65 <= c <= 90 or 97 <= c <= 122)
            if letters * 2 < len(s):
                continue
        yield m.start(), s.decode('latin1')


def categorise(s):
    out = []
    for name, pats in CATEGORIES:
        for p in pats:
            if re.search(p, s):
                out.append(name)
                break
    return out


SWEEP = [
    # container and middleware signatures this corpus has met before
    (b'MSCF', 'Microsoft Cabinet header -- 45 per disc on Symphonia GC, 53 on its PS2'),
    (b'CVMH', 'CRI ROFS volume header -- 9 on Symphonia PS2'),
    (b'ROFSBLD', 'the CVM builder stamp'),
    (b'SAMPLE_GAME_TITLE', "CRI's unfilled default, on all nine Symphonia volumes"),
    (b'PUBLISHER_NAME', "CRI's other unfilled default"),
    (b'CRI ', 'any CRI middleware banner'),
    (b'SCPK', 'the 2002 bundle container'),
    (b'THEIRSCE', "Rebirth's per-bundle scenario chunk, 2004"),
    (b'h4m', 'Hudson h4m video, met on the Symphonia GameCube discs'),
    (b'AFS' + bytes([0]), "CRI's plain archive -- what this disc indexes with"),
    (b'CPS' + bytes([0]), "this disc's own compressed-member envelope"),
    (b'ADX', 'CRI ADX audio'),
    (b'@UTF', 'CRI UTF table, the later middleware generation'),
    (b'KORG', 'the sound driver this disc ships on the I/O processor'),
    (b'FILE.FPB', "Destiny 2's container name, 2002"),
    (b'TIM2', 'PlayStation 2 texture'),
    (b'VAGp', 'headered SPU audio'),
    (bytes([0, 0, 1, 0xBA]), 'MPEG program stream pack header'),
    # devkit and build traces
    (b'host0:', "the devkit's host file system"),
    (b'hostfs', 'ditto'),
    (b'mass:', 'devkit mass storage'),
    (b'MW MIPS', 'Metrowerks compiler stamp -- present in Symphonia PS2'),
    (b'CodeWarrior', 'ditto'),
    (b'GCC', 'GNU toolchain stamp'),
    # other titles: this corpus has a habit of cross-contamination
    (b'Symphonia', 'Tales of Symphonia, 2003/2004'),
    (b'symphonia', 'ditto, lower case'),
    (b'destiny', 'Tales of Destiny, 1997 / Destiny 2, 2002'),
    (b'DESTINY', 'ditto, upper case'),
    (b'TOD2', "Destiny 2's project tag"),
    (b'tod2', 'ditto, lower case'),
    (b'TOP2', "Symphonia's project tag"),
    (b'top2', 'ditto, lower case'),
    (b'eternia', 'Tales of Eternia, 2000'),
    (b'phantasia', 'Tales of Phantasia, 1995'),
    (b'Venus', 'Venus & Braves, shipped whole on the 2002 disc'),
    (b'rebirth', 'Tales of Rebirth, 2004'),
    (b'REBIRTH', 'ditto, upper case'),
    (b'ToR', "Rebirth's project tag"),
    (b'legendia', 'Tales of Legendia, 2005 -- four months before this disc'),
    (b'LEGENDIA', 'ditto, upper case'),
    (b'Legendia', 'ditto, mixed case'),
    (b'ToL', "Legendia's project tag"),
    (b'TOL', 'ditto, upper case'),
    (b'tox', "Legendia's devkit project root, host0:C:\tox\fieldwork\\"),
    (b'TLPS', "Legendia's AHX wrapper chunk"),
    (b'TLPK', "Legendia's package tag, found inside its CDVD.000"),
    (b'CPS ', "Legendia's sixteen-byte compressed-member envelope"),
    (b'abyss', "this game's own name, lower case"),
    (b'ABYSS', 'ditto, upper case'),
    (b'Abyss', 'ditto, mixed case'),
    (b'TO7', "this disc's own project tag, from its nine volume names"),
    (b'to7', 'ditto, lower case'),
    (b'TO8', 'the next tag in the same sequence'),
    (b'FPS3', "this disc's in-house archive header"),
    (b'FPS2', 'ditto, the older revision'),
    (b'FPS4', 'the revision this disc does not use'),
    (b'VSSVER', 'Visual SourceSafe status file'),
    (b'SourceSafe', 'ditto, spelled out'),
    (b'.pdb', 'a debugger symbol path'),
    (b'Namco', 'the publisher, mixed case'),
    (b'NAMCO', 'ditto, upper case'),
]


def sweep(path):
    """Count every SWEEP pattern across the whole image."""
    import time
    size = os.path.getsize(path)
    over = max(len(p) for p, _ in SWEEP) - 1
    counts = {p: 0 for p, _ in SWEEP}
    first = {p: [] for p, _ in SWEEP}
    t0 = time.time()
    pos = 0
    prev = b''
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(1 << 24)
            if not chunk:
                break
            buf = prev + chunk
            base = pos - len(prev)
            for pat, _ in SWEEP:
                i = buf.find(pat)
                while i != -1:
                    counts[pat] += 1
                    if len(first[pat]) < 4:
                        first[pat].append(base + i)
                    i = buf.find(pat, i + 1)
            prev = chunk[-over:]
            pos += len(chunk)
    print('swept %d bytes of %s in %.1f s' % (pos, os.path.basename(path),
                                              time.time() - t0))
    print('(%d bytes on disc)' % size)
    print()
    print('%-20s %9s  %s' % ('PATTERN', 'HITS', 'FIRST OFFSETS / WHAT IT WOULD MEAN'))
    for pat, what in SWEEP:
        show = ' '.join('0x%X' % x for x in first[pat]) if first[pat] else what
        print('%-20s %9d  %s' % (repr(pat.decode('latin1'))[1:-1], counts[pat], show))


def main(argv):
    paths = [a for a in argv[1:] if not a.startswith('--')]
    raw = '--raw' in argv
    want = argv[argv.index('--category') + 1] if '--category' in argv else None
    if not paths:
        raise SystemExit(__doc__)
    if '--sweep' in argv:
        for p in paths:
            sweep(p)
        return
    for path in paths:
        data = open(path, 'rb').read()
        rows = list(strings(data, raw))
        print('=== %s  %d bytes, %d text runs of 8+ characters'
              % (os.path.basename(path), len(data), len(rows)))
        buckets = {}
        for off, s in rows:
            cs = categorise(s) or ['other']
            for c in cs:
                buckets.setdefault(c, []).append((off, s))
        for name, _ in CATEGORIES + [('other', ())]:
            if name not in buckets:
                continue
            if want and name != want:
                continue
            print('--- %s (%d)' % (name, len(buckets[name])))
            for off, s in buckets[name]:
                print('    %08X  %s' % (off, s))
        print()


if __name__ == '__main__':
    main(sys.argv)
