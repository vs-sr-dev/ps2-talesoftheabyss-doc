"""ELF reader for PlayStation 2 executables (EE, R5900) and IOP modules.

Both CPUs use 32-bit little-endian ELF.  The EE side is EM_MIPS (8) with
EF_MIPS_ARCH flags 0x20924001; IOP modules are the same class but declare
machine 0xFF80 and carry a `.iopmod` section with the module's name and
version instead of a normal entry point.

Usage:
    python tools/ps2elf.py FILE --header
    python tools/ps2elf.py FILE --sections
    python tools/ps2elf.py FILE --segments
    python tools/ps2elf.py FILE --symbols [--sort addr|name|size]
    python tools/ps2elf.py FILE --iopmod
    python tools/ps2elf.py FILE --map            # what lives where in memory
"""

import struct
import sys

EM = {8: 'MIPS (EE, R5900)', 0xFF80: 'IOP (R3000A, Sony)'}
PT = {0: 'NULL', 1: 'LOAD', 2: 'DYNAMIC', 3: 'INTERP', 4: 'NOTE',
      5: 'SHLIB', 6: 'PHDR', 0x70000080: 'PS2_IOPMOD'}
SHT = {0: 'NULL', 1: 'PROGBITS', 2: 'SYMTAB', 3: 'STRTAB', 4: 'RELA',
       5: 'HASH', 6: 'DYNAMIC', 7: 'NOTE', 8: 'NOBITS', 9: 'REL',
       10: 'SHLIB', 11: 'DYNSYM', 0x70000080: 'IOPMOD',
       0x70000000: 'MIPS_LIBLIST', 0x7000000D: 'MIPS_DEBUG',
       0x70000006: 'MIPS_REGINFO'}
STT = {0: 'NOTYPE', 1: 'OBJECT', 2: 'FUNC', 3: 'SECTION', 4: 'FILE'}
STB = {0: 'LOCAL', 1: 'GLOBAL', 2: 'WEAK'}


class Sym:
    __slots__ = ('name', 'value', 'size', 'type', 'bind', 'shndx')


class ELF:
    def __init__(self, path):
        self.path = path
        self.d = open(path, 'rb').read()
        d = self.d
        if d[:4] != b'\x7fELF':
            raise ValueError('%s: not an ELF' % path)
        (self.type, self.machine) = struct.unpack_from('<HH', d, 16)
        (self.entry, self.phoff, self.shoff, self.flags) = \
            struct.unpack_from('<IIII', d, 24)
        (self.ehsize, self.phentsize, self.phnum,
         self.shentsize, self.shnum, self.shstrndx) = \
            struct.unpack_from('<6H', d, 40)
        self.phdrs = [struct.unpack_from('<8I', d, self.phoff + i * self.phentsize)
                      for i in range(self.phnum)]
        self.shdrs = [struct.unpack_from('<10I', d, self.shoff + i * self.shentsize)
                      for i in range(self.shnum)] if self.shoff else []
        self.shnames = []
        if self.shdrs:
            strtab = self.shdrs[self.shstrndx]
            base = strtab[4]
            for sh in self.shdrs:
                e = d.index(b'\x00', base + sh[0])
                self.shnames.append(d[base + sh[0]:e].decode('ascii', 'replace'))

    def section(self, name):
        for i, n in enumerate(self.shnames):
            if n == name:
                sh = self.shdrs[i]
                return sh, self.d[sh[4]:sh[4] + sh[5]]
        return None, None

    def symbols(self):
        sh, data = self.section('.symtab')
        if sh is None:
            return []
        _, strdata = self.section('.strtab')
        out = []
        for o in range(0, len(data), 16):
            name, value, size, info, other, shndx = \
                struct.unpack_from('<IIIBBH', data, o)
            s = Sym()
            e = strdata.index(b'\x00', name)
            s.name = strdata[name:e].decode('ascii', 'replace')
            s.value, s.size = value, size
            s.type = info & 0xF
            s.bind = info >> 4
            s.shndx = shndx
            if s.name:
                out.append(s)
        return out

    def iopmod(self):
        """Sony's .iopmod section: module name, version, entry, bss size."""
        sh, data = self.section('.iopmod')
        if sh is None:
            for i, ph in enumerate(self.phdrs):
                if ph[0] == 0x70000080:
                    data = self.d[ph[1]:ph[1] + ph[5]]
                    break
            else:
                return None
        moduleinfo, entry, gp, text, data_sz, bss = \
            struct.unpack_from('<6I', data, 0)
        version = struct.unpack_from('<H', data, 24)[0]
        name = data[26:].split(b'\x00')[0].decode('ascii', 'replace')
        return dict(name=name, version='%d.%d' % (version >> 8, version & 0xFF),
                    entry=entry, gp=gp, text=text, data=data_sz, bss=bss)

    def vaddr_range(self):
        lo, hi = None, 0
        for p in self.phdrs:
            if p[0] != 1:
                continue
            if lo is None or p[2] < lo:
                lo = p[2]
            hi = max(hi, p[2] + p[5])
        return lo or 0, hi

    def read_vaddr(self, addr, n):
        """Bytes at a virtual address, from whichever LOAD segment holds it."""
        for p in self.phdrs:
            if p[0] != 1:
                continue
            _, off, va, _, filesz, memsz, _, _ = p
            if va <= addr < va + filesz:
                o = off + (addr - va)
                return self.d[o:o + n]
        return b''


def fmt_flags(f):
    return ('%s%s%s' % ('r' if f & 4 else '-', 'w' if f & 2 else '-',
                        'x' if f & 1 else '-'))


def cmd_header(e):
    print('file            %s (%d bytes)' % (e.path, len(e.d)))
    print('type            %d (%s)' % (e.type, {2: 'EXEC', 1: 'REL'}.get(e.type, '?')))
    print('machine         0x%04X  %s' % (e.machine, EM.get(e.machine, '?')))
    print('flags           0x%08X' % e.flags)
    print('entry           0x%08X' % e.entry)
    print('program headers %d at 0x%X' % (e.phnum, e.phoff))
    print('section headers %d at 0x%X' % (e.shnum, e.shoff))
    lo, hi = e.vaddr_range()
    print('load span       0x%08X .. 0x%08X  (%d bytes)' % (lo, hi, hi - lo))
    m = e.iopmod()
    if m:
        print('iopmod          %s version %s, entry 0x%X, bss %d'
              % (m['name'], m['version'], m['entry'], m['bss']))


def cmd_segments(e):
    print('%-12s %-10s %-10s %-10s %-10s %-5s %s'
          % ('TYPE', 'OFFSET', 'VADDR', 'FILESZ', 'MEMSZ', 'FLAGS', 'ALIGN'))
    for p in e.phdrs:
        t, off, va, pa, fsz, msz, fl, al = p
        print('%-12s 0x%08X 0x%08X 0x%08X 0x%08X %-5s 0x%X'
              % (PT.get(t, '0x%X' % t), off, va, fsz, msz, fmt_flags(fl), al))


def cmd_sections(e):
    if not e.shdrs:
        print('no section headers')
        return
    print('%-3s %-18s %-14s %-10s %-10s %-9s %s'
          % ('#', 'NAME', 'TYPE', 'ADDR', 'OFFSET', 'SIZE', 'AL'))
    for i, sh in enumerate(e.shdrs):
        name, typ, flags, addr, off, size, link, info, align, entsz = sh
        print('%-3d %-18s %-14s 0x%08X 0x%08X %9d %d'
              % (i, e.shnames[i], SHT.get(typ, '0x%X' % typ), addr, off, size, align))


def cmd_symbols(e, order):
    syms = e.symbols()
    if not syms:
        print('no symbol table')
        return
    if order == 'name':
        syms.sort(key=lambda s: s.name)
    elif order == 'size':
        syms.sort(key=lambda s: -s.size)
    else:
        syms.sort(key=lambda s: s.value)
    print('%-10s %-9s %-8s %-7s %s' % ('VALUE', 'SIZE', 'TYPE', 'BIND', 'NAME'))
    for s in syms:
        print('0x%08X %9d %-8s %-7s %s'
              % (s.value, s.size, STT.get(s.type, '?'), STB.get(s.bind, '?'), s.name))
    print()
    print('%d symbols' % len(syms))


def cmd_map(e):
    lo, hi = e.vaddr_range()
    print('%-10s %-10s %-10s %-9s %s' % ('VADDR', 'END', 'FILEOFF', 'SIZE', 'WHAT'))
    for p in e.phdrs:
        t, off, va, pa, fsz, msz, fl, al = p
        if t != 1:
            continue
        print('0x%08X 0x%08X 0x%08X %9d  LOAD %s, file %d bytes'
              % (va, va + msz, off, msz, fmt_flags(fl), fsz))
        if msz > fsz:
            print('0x%08X 0x%08X %-10s %9d  .bss (zero-filled at load)'
                  % (va + fsz, va + msz, '-', msz - fsz))
    print()
    print('entry 0x%08X' % e.entry)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    e = ELF(argv[1])
    rest = argv[2:]
    if '--sections' in rest:
        cmd_sections(e)
    elif '--segments' in rest:
        cmd_segments(e)
    elif '--symbols' in rest:
        order = rest[rest.index('--sort') + 1] if '--sort' in rest else 'addr'
        cmd_symbols(e, order)
    elif '--iopmod' in rest:
        m = e.iopmod()
        print(m if m else 'no .iopmod')
    elif '--map' in rest:
        cmd_map(e)
    else:
        cmd_header(e)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
