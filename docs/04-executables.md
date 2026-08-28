# 04 — The executables

Reproduce with:

```
python tools/dismips.py SLPS_255.86 --header
python tools/leftovers.py SLPS_255.86
python tools/ring_sites.py <each image> --mips --imm 4078,4079,4080
```

Output: [`reports/leftovers.txt`](../reports/leftovers.txt),
[`reports/ring-sites.txt`](../reports/ring-sites.txt).

---

## The Emotion Engine side

```
file            SLPS_255.86  (5,086,288 bytes)
type            2 (EXEC)
machine         0x0008  MIPS (EE, R5900)
entry           0x00100008
program headers 6
load            file 0x100 -> VA 0x00100000, 0x4D9900 bytes
                (five more PT_LOAD entries, all filesz 0 -- BSS regions)
sections        .shstrtab .strtab .symtab .comment .reginfo
.comment        MW MIPS C Compiler (2.4.1.01)
                PlayStation2
```

**`MW MIPS C Compiler (2.4.1.01)`** — the same compiler string, character for
character, that `SLPS_254.00` (*Symphonia*, 2004) and `SLPS_255.33`
(*Legendia*, 2005) carry. That is what makes section
[06](06-decoder-lineage.md) a measurement rather than an argument: the toolchain
is excluded by the file's own stamp before the byte comparison starts.

It is not the *only* toolchain in the file. Three strings read
`Append: GCC2096 SCE3020` — Sony's `ee-gcc` 2.96 under SDK 3.0.2.0 — so at
least some objects came in from the GNU chain and were linked into a Metrowerks
build. And the 36 overlays in `TO7ROOT.CVM` are `MWo3`, Metrowerks CodeWarrior's
overlay format, each carrying its own build name (`ov_D_btl.ovl` and so on) in
its header.

1,271,360 instruction words. The block codec occupies 1,896 of the 4,981,632
bytes of loaded image — 0.04% of it.

### Middleware, and the disc's first RenderWare

Three source paths survive from the graphics SDK's own build tree:

```
c:/daily/rwsdk/plugin/pds/sky2/G3_2DStroke/G3_2DStroke_Node.c
c:/daily/rwsdk/plugin/pds/sky2/G3_2DFont/G3_2DFont_Node.c
c:/daily/rwsdk/plugin/pds/sky2/G3_2DFill/G3_2DFill_Node.c
```

with `Core built at Jul 16 2004 17:14:46` and the pipeline diagnostics
`PS2 material pipes`, `PS2 sector pipes`, `PS2 atomic pipes` and
`Only rendering sub system` beside them, plus twenty-seven `PS2*.csl` node
names (`PS2PTank.csl`, `PS2DMAChain.csl`, `PS2Im3DFastTransform.csl`, …).
`rwsdk` and `pds` are RenderWare Graphics' own directory names; the word
"RenderWare" itself does not appear, so the identification is from the SDK
layout rather than from a banner. **No other disc in this corpus carries it** —
*Destiny 2*, *Symphonia*, *Rebirth* and *Legendia* are all in-house engines.

CRI is here in force, and stamped to the second:

```
ADXPS2  Ver.2.60   Build:Feb 28 2005 19:25:21
ADXT/PS2EE Ver.9.44 Build:Feb 28 2005 19:25:20
AHX/PS2EE  Ver.1.44 Build:Feb 28 2005 19:25:26
...
ROFS    Ver.1.77   Build:Mar  2 2005 11:30:59
ROCI    Ver.1.15   Build:Mar  2 2005 11:31:01
RSU     Ver.1.10   Build:Mar  2 2005 11:31:01
```

Twenty-four components inside a **twenty-nine-second window** on 28 February
2005, and three `ROFS` components from a second, two-second build on 2 March.
*Legendia* carried the same habit — nine components in twenty-six seconds on
12 April 2004 — so this is now two discs showing one library build each.

---

## The I/O processor side

Five images, and the split between Sony's and the studio's is unusually clean.

| File | Bytes | What |
|---|---:|---|
| `IOPRP300.IMG` | 278,305 | Sony's boot image — `cdvd_driver`, `ROM_file_driver`, `IOP_SIF_manager`, `cdvdfsv.irx` |
| `IRXARC.BIN` | 386,048 | a bundle of eleven stock modules |
| `CEI.IRX` | 75,808 | the studio's, sound transport |
| `PFM.IRX` | 71,696 | the studio's, **MIDI sequencer** |
| `SDM.IRX` | 60,992 | the studio's, sound driver |

`IRXARC.BIN` names its members: `sio2man.irx`, `padman.irx`, `mtapman.irx`,
`mcman.irx`, `mcserv.irx`, `libsd.irx`, `sdrdrv.irx`, **`modhsyn.irx`**,
**`modmidi.irx`**, **`modsein.irx`**, and `cri_adxi.irx` with its
`CRI_ADX_Driver` banner.

`modhsyn`, `modmidi` and `modsein` are Sony's sequence and MIDI modules, and
`PFM.IRX` calls into them: `sceMidi_Init`, `sceMidi_Load`, `sceMidi_SelectMidi`,
`sceMidi_MidiPlaySwitch`, `sceMidi_MidiSetVolume`, `sceMidi_MidiSetLocation`,
`sceMidi_ATick`. So **this disc plays MIDI sequences on the I/O processor**, as
*Legendia* did four months earlier — except Legendia used KORG's driver and its
own `KORGIVAG.IRX`/`KORGUMDI.IRX`, and the string `KORG` does not occur once in
these 4.36 GB. Same architectural choice, different supplier. See
[07](07-media-and-budget.md).

### Three modules that kept their whole source tree

`CEI.IRX`, `PFM.IRX` and `SDM.IRX` were built with **Metrowerks**, which is
unusual on the I/O processor, and none of them merged its `.comment` sections:
they carry **113, 85 and 74 copies** of `MW MIPS C Compiler (2.4.1.01)`, one per
translation unit. With them come the translation units' absolute paths — twenty
five of them, and together they are a map of the sound subsystem's source tree
on the machine that built it:

```
C:\TO7\prog\CEI\COM_src\   CEI_sifque.c  CEI_sifque_ext.c
C:\TO7\prog\CEI\ETC_src\   ik_queue.c  ik_ringbuf.c  ik_vol.c
C:\TO7\prog\CEI\IOP\       CallTable.s  EntryTable.s  main.c
C:\TO7\prog\CEI\IOP_src\   CEI_IOP.c  CEI_IOP_timer.c  CEI_reverb.c
                           CEI_IS_trans.c  CEI_E2IS_trans_iop.c
C:\TO7\prog\snd\IOP\       CallTable.s  EntryTable.s  main.c
C:\TO7\prog\snd\IOP_src\   PFM_midi.c  PFM_tsp.c  PFM_tsq2.c
                           SDM_IOP.c  SDM_bgm_player_iop.c
                           SDM_combuf_IOP.c  SDM_se_port_iop.c
                           SDM_status_iop.c
```

`C:\TO7\prog\` is this project's root on that build machine, and `TO7` is the
tag the nine volumes, the C++ class names (`CTO7SystemSaveData`,
`CTO7GameSaveDataObj`) and the executable's own volume list (`to7ROOT.cvm`, …)
all use. *Legendia*'s equivalent was one path,
`host0:C:\tox\fieldwork\dev\field\`; this is twenty-five.

`ik_vol.c` appears in both `CEI.IRX` and `PFM.IRX`, so the two modules share at
least one object.

### The codec is not on this side

`ring_sites.py` returns **no 4078, 4079 or 4080** in `IOPRP300.IMG`, `CEI.IRX`,
`PFM.IRX` or `SDM.IRX`, and two innocent `4080`s in `IRXARC.BIN` (a hardware
register value stored beside a `4092`, and a buffer size in an argument list).
Both were disassembled.

That puts this disc with *Symphonia*'s PlayStation 2 port, which also kept the
codec on the main CPU only, and against *Destiny 2* (2002) and *Rebirth* (2004),
which each carried a second copy on the I/O processor. The corpus's standing
observation — that where CRI's `ROFS` ran on the I/O processor the codec left it,
and where the game read its own containers the codec stayed — now has a third
data point pointing the same way: this disc runs `ROFS`, and the codec is not
there.

### And two devkit paths that shipped

```
host0:ioprp300.img
host0:irxarc.bin
```

The fallback names the loader uses when the disc is not a disc. `IOPRP300.IMG`
carries a third `host0:` of its own.
