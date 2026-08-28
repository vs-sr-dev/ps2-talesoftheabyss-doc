# 01 — Overview

**SLPS-25586**, `VER = 1.05`, NTSC. One single-layer DVD, 2,127,840 sectors,
4,357,816,320 bytes, volume stamped **2005-11-25 23:56:52 +9**. Sixteen files in
a flat root; nine of them are CRI `ROFS` volumes holding 3,047 members.

This repository is documentation and analysis only. No disc image, no extracted
asset, no executable, no patch, no translation. Every number below was produced
by a tool in [`tools/`](../tools/) and its output is committed under
[`reports/`](../reports/).

---

## The disc in one screen

| | |
|---|---|
| Product code | **SLPS-25586**, `VER = 1.05`, NTSC — from `SYSTEM.CNF` |
| Media | one **single-layer** DVD — 2,127,840 sectors, **4,357,816,320 bytes** |
| Volume | ISO 9660 + UDF bridge; publisher `NAMCO LTD.`, **volume identifier blank** |
| File system | **16 files, 0 directories**; no interior gap, 0.4939% slack |
| Executable | `SLPS_255.86`, R5900, 5,086,288 bytes, `.comment` = `MW MIPS C Compiler (2.4.1.01)` |
| I/O processor | Sony's `IOPRP300.IMG` + `IRXARC.BIN`, and **three Metrowerks-built modules of the studio's own** |
| Graphics | **RenderWare** — the only disc in this corpus that uses it |
| Containers | nine CRI **`CVM`/`ROFS`** volumes → `AFS` and in-house **`FPS3`/`FPS2`** |
| Compressed member | the corpus's **nine-byte header**, methods 0/1/3, called `.slz` by the game |
| Block codec | **yes**, Emotion Engine only — **47,513 of 47,513 blocks decode** |
| Ring clear | inline byte loop **unrolled by eight**, cursors **4078 / 4079** |
| Decoder vs *Symphonia* PS2 | **69 bytes**, against **632** of shared C runtime |
| Decoder vs *Legendia* | **18 bytes**, against **632** of shared C runtime |
| Per-asset timestamps | **yes**, on all 3,047 members and 15,689 `AFS` members |
| Cross-title data | **no** — 109 sound effects carry *Tales of Rebirth*'s prefix |
| Disc used | 99.50% named, no interior gap, no unreferenced file |

---

## Six answers

### 1 — The code line is alive, and *Legendia* was the deviation

The question this disc was opened to settle had three possible answers.
*Tales of Legendia*, four months earlier, had the format complete and shared no
code with anything: 21 bytes against *Symphonia*, 20 against *Rebirth*, and
**20 against an executable that contains no decoder at all**. That made the
corpus say the codec had propagated as a specification rather than as a file.

872 bytes of Abyss's decoder, same tool, same needle length, searched through
whole executables:

| against | run |
|---|---:|
| ***Symphonia*, PlayStation 2, 2004** | **69 bytes** |
| *Legendia*, 2005 | 18 |
| *Rebirth*, 2004 | 14 |
| *Destiny 2*, 2002 | 12 |
| ***Venus & Braves*, 2003 — no decoder in it** | **14** |

Five times the noise floor. The source file was on hand and was compiled.
[→ 06](06-decoder-lineage.md)

### 2 — And it is *Symphonia*'s **unedited** copy, not the one everyone quotes

`SLPS_254.00` carries the codec four times, in two pairs that share 2 identical
words in 276 with each other. The corpus's 2004 headline — "somebody edited the
decoder, a quadword `bzero` with **4080**" — is about the first pair. Abyss
scores **4 bytes** against that pair and **69** against the other one, the copy
in the same file that still clears the ring the 1997 way and still writes the
synthetic preload.

Aligned on the clear loop: **31 identical words in 200, a 68-byte run, 56.5%
same opcode**, diverging on register allocation and nothing else. The dispatcher
that reads the nine-byte header matches for 10 words out of 44 in a routine
where most words are `jal` targets and branch offsets. [→ 06](06-decoder-lineage.md)

### 3 — The envelope reverted completely

*Legendia* replaced the nine-byte header with a sixteen-byte `CPS` chunk, no
method byte, no run escape, no synthetic preload. **None of that is here.** The
dispatcher reads `+0` method, assembles `+1` packed size from four `lbu`s,
dispatches on **0, 1 and 3 used directly**, and rebuilds a 4,096-byte ring on
the stack on every call. The preload is written, both halves, 3,840 bytes. The
run escape is there with its `+3` and its `+19`.

`CPS ` and `CPS\0` together return seven hits across 4,357,816,320 bytes against
a chance rate of about one each; all seven were located and every one is inside
a Sofdec or ADX payload. [→ 05](05-block-codec.md)

### 4 — 47,513 of 47,513, and 97.5% of them were nearly missed

The unmodified reference decoder — md5 `e2dcd6b8dc717b84f67bf8a46568298c` —
reads every block on the disc: **1,069,278,379 packed → 2,643,327,828
unpacked**, ratio 2.472×, zero method-0, nothing expanding.

But 46,345 of the 47,513 are inside twenty-seven members that have **no
container header at all** — flat runs of sector-aligned blocks, `F3.PKF` alone
holding 4,634. A census that stops at the member level sees `F0.PKF` as one
block, decodes 163,176 bytes out of 37,951,488, gets a length match, and reports
success. Profiling the big files before writing them off was the right call
again. [→ 05](05-block-codec.md), [→ 03](03-containers.md)

### 5 — The disc is not clean, and what it carries is traceable

*Rebirth* was the first clean disc and *Legendia* the second. This is not the
third. `SE.AFS` holds 1,025 sound effects and **109 of them are prefixed
`tor_`** — *Tales of Rebirth*'s project tag. Strip the prefix and all **105**
distinct names are present on *Rebirth*'s own disc, whose effect table reads
`no_se_mp_steps00 … no_se_mp_steps12`. The audio was re-encoded, not copied: no
64-byte body needle and no ADX header from any of them appears in that image.

And three battle models are named for characters of three earlier titles —
`FIRIA`, `RID`, `NANARI` — which are the **three oldest game assets on the
disc**, dated February and March 2005, four months before the protagonist's.
Nothing on the disc names them. [→ 08](08-cross-title.md)

### 6 — A quarter of the disc is geometry, and it is the largest single class

| | bytes | of the image |
|---|---:|---:|
| compressed game data | 1,069,195,048 | **24.54%** |
| voice (AHX) | 985,237,321 | 22.61% |
| video (Sofdec) | 981,364,736 | 22.52% |
| audio (ADX) | 720,509,996 | 16.53% |

**video + voice = 45.13%**, all media **61.66%** — against *Rebirth*'s 67.2%
and *Legendia*'s 37.70%. This is the first disc here whose biggest class is not
media. 13.60 hours of voice in 12,643 AHX streams, 4.62 hours of ADX, 27 Sofdec
streams, and — like *Legendia* and unlike anything before it — a MIDI player on
the I/O processor, for six sequences totalling 77,584 bytes.
[→ 07](07-media-and-budget.md)

---

## And the archaeology

**Twenty-five absolute source paths** under `C:\TO7\prog\`, because three
Metrowerks-built I/O processor modules kept one `.comment` per object file —
113, 85 and 74 of them — and the paths came with them; a **complete BGM track
list in English** in a Japan-only release, next to a `CSoundMode*` sound-test
class family, in which the single occurrence of the word `abyss` anywhere on
the disc is track one; **nine Visual SourceSafe `VSSVER.SCC` files**, one per
volume, five of them the newest member of their volume; **36 Metrowerks `MWo3`
overlays in nine unexplained configurations**, all distinct; **611 copies of one
13,810-byte `dummy.adx`** filling the unused slots of the sound-effect archive;
five `AFS` archives holding nothing but their dummy; a **monster encyclopedia
that says it is not implemented**; a debug string reading *"debug-only?
`comp_dict_XXX` does not work"*; **CRI's whole library stamped inside a
twenty-nine-second build** on 28 February 2005; `ROFSBLD Ver.1.52 2003-06-09`,
the same builder to the day that made *Symphonia*'s volumes eighteen months
earlier, still shipping `SAMPLE_GAME_TITLE`; a **Sony SDK module from
2000-04-25** five years older than everything else; and the **staff credit roll
shipped as plain Shift-JIS text** anyone could open.
[→ 09](09-leftovers.md)

---

Continue at [02 — The disc and the volume](02-disc-and-volume.md).
