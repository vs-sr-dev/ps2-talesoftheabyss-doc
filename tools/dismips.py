"""A small MIPS disassembler for PlayStation 2 code, EE and IOP alike.

The EE is an R5900 and the IOP an R3000A, but the decompressors this
pipeline cares about are written in plain MIPS I / II, which both decode
identically -- which is the whole point: it is what lets a routine compiled
for the PlayStation in 1997 be compared instruction by instruction with the
same routine compiled for the PlayStation 2 in 2002.

Usage:
    python tools/dismips.py FILE --header
    python tools/dismips.py FILE 0x4954 60           # file offset, N words
    python tools/dismips.py FILE --va 0x00100B1BC 60 # virtual address
    python tools/dismips.py FILE --find-prologue 0x4DC4   # back up to addiu sp
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ps2elf import ELF

REG = ['zero', 'at', 'v0', 'v1', 'a0', 'a1', 'a2', 'a3',
       't0', 't1', 't2', 't3', 't4', 't5', 't6', 't7',
       's0', 's1', 's2', 's3', 's4', 's5', 's6', 's7',
       't8', 't9', 'k0', 'k1', 'gp', 'sp', 'fp', 'ra']

SPECIAL = {0x00: 'sll', 0x02: 'srl', 0x03: 'sra', 0x04: 'sllv', 0x06: 'srlv',
           0x07: 'srav', 0x08: 'jr', 0x09: 'jalr', 0x0C: 'syscall',
           0x0D: 'break', 0x10: 'mfhi', 0x11: 'mthi', 0x12: 'mflo',
           0x13: 'mtlo', 0x18: 'mult', 0x19: 'multu', 0x1A: 'div',
           0x1B: 'divu', 0x20: 'add', 0x21: 'addu', 0x22: 'sub',
           0x23: 'subu', 0x24: 'and', 0x25: 'or', 0x26: 'xor', 0x27: 'nor',
           0x2A: 'slt', 0x2B: 'sltu', 0x2C: 'dadd', 0x2D: 'daddu'}

OPS = {0x02: 'j', 0x03: 'jal', 0x04: 'beq', 0x05: 'bne', 0x06: 'blez',
       0x07: 'bgtz', 0x08: 'addi', 0x09: 'addiu', 0x0A: 'slti',
       0x0B: 'sltiu', 0x0C: 'andi', 0x0D: 'ori', 0x0E: 'xori', 0x0F: 'lui',
       0x14: 'beql', 0x15: 'bnel', 0x16: 'blezl', 0x17: 'bgtzl',
       0x19: 'daddiu',
       0x20: 'lb', 0x21: 'lh', 0x22: 'lwl', 0x23: 'lw', 0x24: 'lbu',
       0x25: 'lhu', 0x26: 'lwr', 0x28: 'sb', 0x29: 'sh', 0x2A: 'swl',
       0x2B: 'sw', 0x2E: 'swr', 0x2F: 'cache', 0x37: 'ld', 0x3F: 'sd',
       # R5900 quadword load/store.  The Emotion Engine's registers are 128
       # bits wide and its compiler spills them with these, so an EE routine
       # that is not decoded here reads as a wall of .word in its prologue --
       # which matters, because the 2004 dictionary clear is a quadword store.
       0x1E: 'lq', 0x1F: 'sq'}

MEM = set('lb lh lwl lw lbu lhu lwr sb sh swl sw swr ld sd lq sq'.split())


def s16(x):
    return x - 0x10000 if x & 0x8000 else x


def disasm(w, pc):
    op = w >> 26
    rs, rt, rd = (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31
    sa, fn, imm = (w >> 6) & 31, w & 63, w & 0xFFFF
    if w == 0:
        return 'nop'
    if op == 0:
        m = SPECIAL.get(fn)
        if not m:
            return '.word 0x%08X' % w
        if m in ('sll', 'srl', 'sra'):
            return '%-8s %s, %s, %d' % (m, REG[rd], REG[rt], sa)
        if m in ('sllv', 'srlv', 'srav'):
            return '%-8s %s, %s, %s' % (m, REG[rd], REG[rt], REG[rs])
        if m == 'jr':
            return '%-8s %s' % (m, REG[rs])
        if m == 'jalr':
            return '%-8s %s, %s' % (m, REG[rd], REG[rs])
        if m in ('mfhi', 'mflo'):
            return '%-8s %s' % (m, REG[rd])
        if m in ('mthi', 'mtlo'):
            return '%-8s %s' % (m, REG[rs])
        if m in ('mult', 'multu', 'div', 'divu'):
            return '%-8s %s, %s' % (m, REG[rs], REG[rt])
        return '%-8s %s, %s, %s' % (m, REG[rd], REG[rs], REG[rt])
    if op == 1:
        m = {0: 'bltz', 1: 'bgez', 16: 'bltzal', 17: 'bgezal'}.get(rt, 'regimm')
        return '%-8s %s, 0x%08X' % (m, REG[rs], pc + 4 + s16(imm) * 4)
    m = OPS.get(op)
    if not m:
        return '.word 0x%08X' % w
    if m in ('j', 'jal'):
        return '%-8s 0x%08X' % (m, (pc & 0xF0000000) | ((w & 0x3FFFFFF) << 2))
    if m in ('beq', 'bne', 'beql', 'bnel'):
        return '%-8s %s, %s, 0x%08X' % (m, REG[rs], REG[rt],
                                        pc + 4 + s16(imm) * 4)
    if m in ('blez', 'bgtz', 'blezl', 'bgtzl'):
        return '%-8s %s, 0x%08X' % (m, REG[rs], pc + 4 + s16(imm) * 4)
    if m == 'lui':
        return '%-8s %s, 0x%04X' % (m, REG[rt], imm)
    if m in MEM:
        return '%-8s %s, %d(%s)' % (m, REG[rt], s16(imm), REG[rs])
    if m in ('andi', 'ori', 'xori'):
        return '%-8s %s, %s, 0x%04X' % (m, REG[rt], REG[rs], imm)
    return '%-8s %s, %s, %d' % (m, REG[rt], REG[rs], s16(imm))


def load(path):
    """(bytes, file_offset -> virtual address) for an ELF, a PS-EXE or a blob.

    PlayStation 1 executables are not ELF: they carry Sony's own 0x800-byte
    PS-EXE header, whose load address sits at offset 0x18 and whose text
    begins at 0x800.  Supporting them here is what lets this tool put a 1997
    routine and a 2002 routine side by side."""
    head = open(path, 'rb').read(0x20)
    if head[:8] == b'PS-X EXE':
        d = open(path, 'rb').read()
        org = struct.unpack_from('<I', d, 0x18)[0]
        return d, (lambda o: org + o - 0x800), None
    try:
        e = ELF(path)
        d = e.d
        segs = [(p[1], p[2], p[4]) for p in e.phdrs if p[0] == 1 and p[4]]

        def va(off):
            for fo, v, fsz in segs:
                if fo <= off < fo + fsz:
                    return v + off - fo
            return off
        return d, va, e
    except Exception:
        d = open(path, 'rb').read()
        return d, (lambda o: o), None


def find_prologue(d, off, limit=512):
    """Walk back to the nearest `addiu sp, sp, -N`."""
    o = off & ~3
    while o >= 0 and off - o < limit:
        w = struct.unpack_from('<I', d, o)[0]
        if (w >> 26) == 0x09 and ((w >> 21) & 31) == 29 and ((w >> 16) & 31) == 29 \
                and s16(w & 0xFFFF) < 0:
            return o
        o -= 4
    return None


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    path = argv[1]
    rest = argv[2:]
    d, va, e = load(path)

    if '--header' in rest:
        from ps2elf import cmd_header
        cmd_header(e)
        return 0

    if '--find-prologue' in rest:
        off = int(rest[rest.index('--find-prologue') + 1], 0)
        p = find_prologue(d, off)
        print('nearest prologue before 0x%X: 0x%X (va 0x%08X)'
              % (off, p, va(p)) if p is not None else 'none found')
        return 0

    if '--va' in rest:
        target = int(rest[rest.index('--va') + 1], 0)
        off = None
        if e is None:
            org = struct.unpack_from('<I', d, 0x18)[0] if d[:8] == b'PS-X EXE' else 0
            if org and org <= target:
                off = 0x800 + target - org
        else:
            for p in e.phdrs:
                if p[0] == 1 and p[2] <= target < p[2] + p[4]:
                    off = p[1] + target - p[2]
        if off is None:
            print('0x%08X is not in any LOAD segment' % target)
            return 1
        n = int(rest[rest.index('--va') + 2]) if len(rest) > rest.index('--va') + 2 else 32
    else:
        off = int(rest[0], 0)
        n = int(rest[1]) if len(rest) > 1 else 32

    for i in range(n):
        o = off + i * 4
        if o + 4 > len(d):
            break
        w = struct.unpack_from('<I', d, o)[0]
        print('0x%08X  0x%08X  %08x  %s' % (va(o), o, w, disasm(w, va(o))))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
