"""Find the block codec's ring cursors in an executable, on either CPU.

Section 7 of tales-blockcodec-doc gives the shortcut: scan for the immediates
4078 and 4079.  They are RING - 18 and RING - 17, they are written by the
packer rather than chosen by the programmer, and nothing else in a game has a
reason to load 4,078.  It works in the negative too: an executable with no
4078 anywhere does not contain the decoder.

The shortcut was written for MIPS.  This file also does PowerPC, because the
2003 GameCube build is the first time the question has been asked of a
big-endian machine.  On MIPS the constant is the low half of an I-type word;
on PowerPC it is the low half of a D-form word, and the word itself is stored
big-endian.  The constant does not change -- only the envelope does.

    python tools/ring_sites.py FILE --mips [--base VA --off FILEOFF]
    python tools/ring_sites.py FILE --ppc  [--base VA --off FILEOFF]
    python tools/ring_sites.py FILE --mips --imm 4078,4079,4080

The default set is 4078 and 4079, which is what the sibling pipelines ran and
what section 7 of the specification describes.  `--imm` widens it.  From 2004
the constant is no longer stable -- Symphonia's PlayStation 2 port clears the
ring with 4080 and Tales of Rebirth with 4079 -- so on a 2005 build all three
are worth asking for at once, and which one answers tells you which copy of the
source the build descends from.  The immediate is printed for every hit so the
three never blur together.
"""

import struct
import sys

# MIPS primary opcodes that carry a 16-bit immediate we care about.
MIPS_IMM = {
    4: 'beq', 5: 'bne', 6: 'blez', 7: 'bgtz', 8: 'addi', 9: 'addiu',
    10: 'slti', 11: 'sltiu', 12: 'andi', 13: 'ori', 14: 'xori',
    15: 'lui', 24: 'daddi', 25: 'daddiu',
}
MIPS_SKIP = {4, 5, 6, 7, 15}          # branches and lui are noise

PPC_IMM = {
    7: 'mulli', 8: 'subfic', 10: 'cmplwi', 11: 'cmpwi', 12: 'addic',
    13: 'addic.', 14: 'addi', 15: 'addis', 24: 'ori', 25: 'oris',
    28: 'andi.', 29: 'andis.',
}
PPC_SKIP = {15, 25, 29}               # the "upper half" forms


def scan(data, arch, base, off, size, wanted=(4078, 4079)):
    fmt = '<I' if arch == 'mips' else '>I'
    hits = []
    for i in range(0, size - 3, 4):
        w = struct.unpack_from(fmt, data, off + i)[0]
        imm = w & 0xFFFF
        if imm not in wanted:
            continue
        op = w >> 26
        if arch == 'mips':
            if op not in MIPS_IMM or op in MIPS_SKIP:
                continue
            name = MIPS_IMM[op]
        else:
            if op not in PPC_IMM or op in PPC_SKIP:
                continue
            name = PPC_IMM[op]
        hits.append((base + i, w, name, imm))
    return hits


def routine_start(data, arch, base, off, va, limit=4096):
    """Walk back to the first instruction after the previous return."""
    fmt = '<I' if arch == 'mips' else '>I'
    ret = 0x03E00008 if arch == 'mips' else 0x4E800020   # jr ra / blr
    a = va
    for _ in range(limit // 4):
        a -= 4
        if a < base:
            return None
        w = struct.unpack_from(fmt, data, off + a - base)[0]
        if w == ret:
            return a + (8 if arch == 'mips' else 4)
    return None


def main(argv):
    if len(argv) < 3:
        raise SystemExit(__doc__)
    path = argv[1]
    arch = 'mips' if '--mips' in argv else 'ppc' if '--ppc' in argv else None
    if arch is None:
        raise SystemExit('say --mips or --ppc')
    data = open(path, 'rb').read()
    base = int(argv[argv.index('--base') + 1], 0) if '--base' in argv else 0
    off = int(argv[argv.index('--off') + 1], 0) if '--off' in argv else 0
    size = len(data) - off
    if '--size' in argv:
        size = int(argv[argv.index('--size') + 1], 0)
    wanted = (4078, 4079)
    if '--imm' in argv:
        wanted = tuple(int(x, 0) for x in argv[argv.index('--imm') + 1].split(','))

    hits = scan(data, arch, base, off, size, wanted)
    print('%s, %s, %d words scanned, looking for %s'
          % (path, arch, size // 4, '/'.join(str(x) for x in wanted)))
    if not hits:
        print()
        print('no %s immediate anywhere in this image.'
              % ' or '.join(str(x) for x in wanted))
        print('by section 7 of the codec specification that is evidence the')
        print('decoder is not present, not merely that it was not found.')
        return
    print()
    print('%-12s %-10s %-8s %6s  %s' %
          ('ADDRESS', 'WORD', 'FORM', 'IMM', 'ROUTINE'))
    for va, w, name, imm in hits:
        s = routine_start(data, arch, base, off, va)
        print('0x%08X   0x%08X %-8s %6d  %s' %
              (va, w, name, imm,
               ('0x%08X (+%d words)' % (s, (va - s) // 4)) if s else '?'))
    print()
    print('%d sites' % len(hits))


if __name__ == '__main__':
    main(sys.argv)
