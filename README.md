# Tales of the Abyss (PlayStation 2, 2005, Japan) — structural documentation

Reverse-engineering notes on **SLPS-25586**, the Japanese PlayStation 2 release
of *Tales of the Abyss* (15 December 2005), whose disc is stamped
**2005-11-25 23:56:52**.

This repository is **documentation and analysis only**. It contains no disc
image, no extracted asset, no executable, no patch and no translation. There is
no porting, BYOA or modding intent. Every number quoted was produced by running
the tools in [`tools/`](tools/) on an image supplied separately, and their
output is committed under [`reports/`](reports/) so the claims can be checked
without owning the disc.

---

## TL;DR

| | |
|---|---|
| Product code | **SLPS-25586**, `VER = 1.05`, NTSC |
| Media | one **single-layer** DVD — 2,127,840 sectors, **4,357,816,320 bytes** |
| Volume | ISO 9660 + UDF bridge; publisher `NAMCO LTD.`, **volume identifier blank** |
| File system | **16 files, 0 directories**, no interior gap |
| Executable | `SLPS_255.86`, R5900, 5,086,288 bytes, `.comment` = `MW MIPS C Compiler (2.4.1.01)` |
| I/O processor | Sony's `IOPRP300.IMG` + `IRXARC.BIN`, plus three **Metrowerks-built** modules of the studio's own |
| Graphics | **RenderWare** — the only disc in this corpus that uses it |
| Containers | nine CRI **`CVM`/`ROFS`** volumes, 3,047 members, then `AFS` and in-house `FPS3`/`FPS2` |
| Compressed member | the corpus's **nine-byte header**, methods 0/1/3 — the game calls it `.slz` |
| Block codec | **yes**, Emotion Engine only — **47,513 of 47,513 blocks decode** |
| Ring clear | inline byte loop **unrolled by eight**, cursors **4078 / 4079** |
| Decoder vs *Symphonia* PS2 | **69 bytes**, against **632** of shared C runtime |
| Decoder vs *Legendia* | **18 bytes**, against **632** of shared C runtime |
| `CPS ` / `TLPS` / `TLPK` / `THEIRSCE` / `FILE.FPB` / `KORG` / `VAGp` | **at or below the chance rate in 4.36 GB; every hit located and read** |
| Cross-title data | **yes** — 109 sound effects carry *Tales of Rebirth*'s prefix |
| Disc used | 99.50% named, 0.4939% slack, **no unreferenced file** |

### Six answers

**1 — The line of code is alive, and *Legendia* was the deviation.** Four months
earlier *Tales of Legendia* had the format complete and shared no code with
anything — 21 bytes against *Symphonia*'s PlayStation 2 port, **20 against an
executable that contains no decoder at all** — which made the corpus say the
codec had propagated as a specification rather than as a file. 872 bytes of this
disc's decoder, same tool and same needle length, returns **69 bytes** against
*Symphonia*, against a **14-byte** floor from the same negative control. Byte
equality was available and is demonstrated: **632 bytes** of shared C runtime
between the same pair of files, and 632 against *Legendia* too, all three
stamping `MW MIPS C Compiler (2.4.1.01)`. Same toolchain, same runtime, and only
one of the two gives up decoder bytes. [→ 06](docs/06-decoder-lineage.md)

**2 — And it is the copy of *Symphonia*'s source that nobody edited.**
`SLPS_254.00` carries the codec four times, in two pairs that share 2 identical
words in 276 with each other. The corpus's 2004 headline — the quadword `bzero`
with **4080** — is the first pair, and this disc scores **4 bytes** against it.
It descends from the second: 31 identical words in 200, a **68-byte** run,
diverging on register allocation and nothing else, with a dispatcher that
matches for 10 words out of 44 in a routine that is mostly branch offsets. So
the picture at ten builds is a 1997 source that reaches 2005 intact, three edits
of it that went nowhere, and one format all of them agree on to the bit.
[→ 06](docs/06-decoder-lineage.md)

**3 — The envelope reverted completely, and the shortcut nearly walked past the
routine.** *Legendia*'s sixteen-byte `CPS` chunk is gone; the nine-byte header
is back with methods 0/1/3 used directly, a 4,096-byte ring rebuilt on the stack
every call, both preload loops, and the run escape with its `+3` and its `+19`.
But the ring clear here is unrolled by eight, so its bound is **4071/4070** and
only the *cursor* carries 4078/4079 — at +139 and +135 words into the routine.
Section 7's "disassemble forty instructions around the hit" lands past the whole
dictionary setup. One extra pass, `--imm 4070,4071`, puts the hit at +11.
[→ 05](docs/05-block-codec.md)

**4 — 47,513 of 47,513 decode, and 97.5% of them were nearly missed.**
1,069,278,379 packed → 2,643,327,828 unpacked, 2.472×, zero stored blocks,
nothing expanding. **46,345 of the blocks are inside twenty-seven members that
have no container header at all** — flat runs of sector-aligned blocks, `F3.PKF`
alone holding 4,634. `F0.PKF`'s first nine bytes are a valid header, so a census
that stops at the member level decodes 163,176 bytes out of 37,951,488, gets a
length match, and reports success. [→ 05](docs/05-block-codec.md)

**5 — The disc is not clean, and what it carries is traceable to the disc it
came from.** `SE.AFS` holds 1,025 sound effects and **109 are prefixed `tor_`**,
*Tales of Rebirth*'s tag. Strip the prefix and **all 105** distinct names are on
*Rebirth*'s own image, whose effect table reads
`no_se_mp_steps00 … no_se_mp_steps12`. The audio was re-encoded, not copied. And
three battle models are named `FIRIA`, `RID` and `NANARI` — one lead each from
1997, 2000 and 2002 — and they are the **three oldest game assets on the disc**,
four months older than the protagonist's, named nowhere in any code.
[→ 08](docs/08-cross-title.md)

**6 — A quarter of the disc is geometry, and that is the largest single class.**
Compressed game data 24.54%, voice 22.61%, video 22.52%, ADX 16.53%. **Video +
voice = 45.13%**, all media **61.66%** — between *Rebirth*'s 67.2% and
*Legendia*'s 37.70%, and the first disc here whose biggest class is not media.
13.60 hours of voice in 12,643 AHX streams at a frame header that is **identical
on all 12,643**; 4.62 hours of ADX; 27 Sofdec streams; and, like *Legendia* and
unlike anything before it, a MIDI player on the I/O processor — six sequences,
77,584 bytes, next to 621 MB of streamed music.
[→ 07](docs/07-media-and-budget.md)

### And the archaeology

**Twenty-five absolute source paths** under `C:\TO7\prog\`, because three
Metrowerks-built I/O processor modules kept one `.comment` per object file —
113, 85 and 74 of them; a **complete BGM track list in English** in a Japan-only
release, beside a `CSoundMode*` sound-test class family, in which the single
occurrence of the word `abyss` anywhere on the disc is track one; **nine Visual
SourceSafe `VSSVER.SCC` files**, one per volume, five of them the newest member
of their volume; **36 Metrowerks `MWo3` overlays in nine unexplained
configurations**; **611 copies of one 13,810-byte `dummy.adx`** filling the
unused slots of the sound-effect archive, and five `AFS` archives holding
nothing but their dummy; a monster encyclopedia that says it is not implemented,
and a debug string reading *"debug-only? `comp_dict_XXX` does not work"*;
**CRI's whole library stamped inside a twenty-nine-second build**; `ROFSBLD
Ver.1.52 2003-06-09`, the same builder to the day that made *Symphonia*'s
volumes eighteen months earlier, still shipping `SAMPLE_GAME_TITLE`; a Sony SDK
module from **2000-04-25**; and the staff credit roll shipped as plain
Shift-JIS text. [→ 09](docs/09-leftovers.md)

Start at [docs/01-overview.md](docs/01-overview.md).

---

## Claim status

| Claim | Status | Where |
|---|---|---|
| Single layer, 2,127,840 sectors, 4,357,816,320 bytes | **Verified** — from the volume descriptor, not the file size | [02](docs/02-disc-and-volume.md) |
| `SLPS-25586`, `VER = 1.05`, NTSC | **Verified** — from `SYSTEM.CNF`, corroborated by three save-data strings | [02](docs/02-disc-and-volume.md) |
| 16 files, 0 directories; 0.4939% slack, all after the last volume | **Verified** | [02](docs/02-disc-and-volume.md) |
| Nine CRI `ROFS` volumes, 3,047 members, all with real dates | **Verified** | [03](docs/03-containers.md) |
| `FPS3` and `FPS2` layouts; the `FPS2` count field cannot be trusted | **Verified** — every `FPS2` declares 67 slots and none has more than seven | [03](docs/03-containers.md) |
| Twenty-seven members are header-less runs of sector-aligned blocks | **Verified** — the walk reaches the end of the member in all 27 | [03](docs/03-containers.md) |
| The decoder is at `0x00122150`, 1,896 bytes, Emotion Engine only | **Verified** — disassembled | [05](docs/05-block-codec.md) |
| All six `4078`/`4079`/`4080` sites in the executable read, four innocent | **Verified** | [05](docs/05-block-codec.md) |
| Zero `4078`/`4079` on all five I/O processor images | **Verified** — the two `4080` in `IRXARC.BIN` disassembled | [05](docs/05-block-codec.md) |
| The nine-byte header, methods 0/1/3 used directly; stored path is the fixed one | **Verified** | [05](docs/05-block-codec.md) |
| The synthetic preload is written, both halves, 3,840 bytes | **Verified** — both 256-iteration loops disassembled | [05](docs/05-block-codec.md) |
| …and the packer uses it | **Verified** — 105 of 120 sampled members decode differently without it, and **0 decode to a different length** | [05](docs/05-block-codec.md) |
| 47,513 of 47,513 blocks decode to their declared length | **Verified** — unmodified `tales_block.py` | [05](docs/05-block-codec.md) |
| 69-byte run vs *Symphonia* PS2; `VENUS.ELF` control scores 14 | **Verified** | [06](docs/06-decoder-lineage.md) |
| 632 identical C-runtime bytes with *Symphonia* **and** with *Legendia* | **Verified** — needle widened to 8 KB, answer unchanged | [06](docs/06-decoder-lineage.md) |
| It descends from *Symphonia*'s second decoder pair, not the 4080 one | **Verified** — 31/200 words against 1/200 | [06](docs/06-decoder-lineage.md) |
| …and that this means the source file was on hand and compiled | *Consistent* — the strongest reading of the measurements, not a proof | [06](docs/06-decoder-lineage.md), [99](docs/99-open-questions.md) |
| The ×8 ring-clear unroll is the compiler's, not the source's | **Verified** — *Legendia* shares 18 bytes and unrolls identically; *Destiny 2*, with no compiler stamp, does not | [99](docs/99-open-questions.md) |
| Why this build compiles the *unedited* copy | *Open* — three readings fit | [99](docs/99-open-questions.md) |
| 109 `tor_` sound effects; all 105 distinct names present on *Rebirth*'s disc | **Verified** | [08](docs/08-cross-title.md) |
| …and that the audio was re-encoded rather than copied | **Verified** — six body needles and every ADX header absent from that image | [08](docs/08-cross-title.md) |
| `FIRIA`/`RID`/`NANARI` are the three oldest game assets and are named nowhere in code | **Verified** | [08](docs/08-cross-title.md) |
| …and that they are Philia, Reid and Nanaly | *Consistent* — the names match; the disc does not say so | [99](docs/99-open-questions.md) |
| What `TOL00.NPC` is | *Open* — one name of its kind among 877, and nothing more | [99](docs/99-open-questions.md) |
| 27 Sofdec streams; nine declare a reserved aspect code | **Verified** — from the sequence headers | [07](docs/07-media-and-budget.md) |
| 13.60 hours of AHX; identical frame header on all 12,643 | **Verified** — from the MPEG frame size | [07](docs/07-media-and-budget.md) |
| 4.62 hours of ADX; six MIDI sequences totalling 77,584 bytes | **Verified** — from the ADX headers' sample counts | [07](docs/07-media-and-budget.md) |
| 611 of `SE.AFS`'s 1,025 members are the same file | **Verified** — one md5 over 611 distinct extents | [09](docs/09-leftovers.md) |
| RenderWare | **Verified** for the SDK paths and diagnostics; the product name is inferred from `rwsdk`/`pds` | [04](docs/04-executables.md) |
| No `CPS`/`TLPS`/`TLPK`/`THEIRSCE`/`FILE.FPB`/`KORG`/`VAGp` envelope | **Verified** — every non-zero hit located, read, and shown to be at the chance rate | [08](docs/08-cross-title.md) |
| What the nine overlay prefixes mean | *Open* | [99](docs/99-open-questions.md) |
| What indexes the twenty-seven block runs | *Open* — not located | [99](docs/99-open-questions.md) |
| Whether *Legendia*'s team had this source file | *Open* — a disc records what was compiled | [99](docs/99-open-questions.md) |
| Opcode-sequence similarity across instruction sets | **Not used** — the corpus records that it does not discriminate | [06](docs/06-decoder-lineage.md) |

---

## Documents

| | |
|---|---|
| [01 — Overview](docs/01-overview.md) | the disc in one screen, the six answers |
| [02 — The disc and the volume](docs/02-disc-and-volume.md) | single layer from the volume, sixteen files, the product code |
| [03 — Containers](docs/03-containers.md) | `CVM`/`ROFS`, `AFS`, `FPS3`/`FPS2`, and the members with no header |
| [04 — The executables](docs/04-executables.md) | the ELF, the compiler stamps, RenderWare, the I/O processor side |
| [05 — The block codec on this disc](docs/05-block-codec.md) | the shortcut, the machine, the census, the preload |
| [06 — Decoder lineage](docs/06-decoder-lineage.md) | **the headline**: 69 against 632, and which of two copies |
| [07 — Media and the disc budget](docs/07-media-and-budget.md) | video, AHX, ADX, MIDI, and where 4.36 GB went |
| [08 — Cross-title carry](docs/08-cross-title.md) | *Rebirth*'s sound effects, and three models named for 1997, 2000 and 2002 |
| [09 — Leftovers](docs/09-leftovers.md) | the archaeology, in full |
| [99 — Open questions](docs/99-open-questions.md) | twelve, each with its measurement |

## Reports

Committed output of every tool run: [`reports/`](reports/) — the volume
descriptors and file listing, the sector map, the nine `CVM` headers and the
member census, the full block census, the ring-site scan across all six
executables with every hit read, the decoder disassembly, the prefix scans with
all seven controls, the preload test, the whole-image signature sweep with every
non-zero line located, the cross-title evidence, the media census, the disc
budget, the reference decoder's self-test with its md5, and two CSVs — one row
per volume member and one per compressed member.

## Tools

Python 3, standard library only, one file per job: [`tools/`](tools/) — see
[`tools/README.md`](tools/README.md).

`tales_block.py` is copied from
[tales-blockcodec-doc](https://github.com/vs-sr-dev/tales-blockcodec-doc)
without a single edit — md5 **`e2dcd6b8dc717b84f67bf8a46568298c`**, identical to
the corpus copy and to *Legendia*'s and *Rebirth*'s.

## Related

* [tales-blockcodec-doc](https://github.com/vs-sr-dev/tales-blockcodec-doc) — the
  shared codec specification and lineage, across ten builds and five platforms
* [ps2-talesoflegendia-doc](https://github.com/vs-sr-dev/ps2-talesoflegendia-doc) — 2005, four months earlier
* [ps2-talesofrebirth-doc](https://github.com/vs-sr-dev/ps2-talesofrebirth-doc) — 2004
* [keitai-talesoftactics-doc](https://github.com/vs-sr-dev/keitai-talesoftactics-doc) — 2004 i-appli, the negative
* [gc-talesofsymphonia-doc](https://github.com/vs-sr-dev/gc-talesofsymphonia-doc) — 2003 GameCube + 2004 PlayStation 2
* [ps2-talesofdestiny2-doc](https://github.com/vs-sr-dev/ps2-talesofdestiny2-doc) — 2002, `FILE.FPB` and `SCPK`
* [ps1-talesofeternia-doc](https://github.com/vs-sr-dev/ps1-talesofeternia-doc) — 2000
* [ps1-talesofdestiny-doc](https://github.com/vs-sr-dev/ps1-talesofdestiny-doc) — 1997
* [snes-talesofphantasia-doc](https://github.com/vs-sr-dev/snes-talesofphantasia-doc) — 1995 + GBA 2003
* [android-talesofcrestoria-doc](https://github.com/vs-sr-dev/android-talesofcrestoria-doc) — 2020

## Licence

Tools under [MIT](LICENSE). Documentation and reports under
[CC BY 4.0](LICENSE-DOCS).

*Tales of the Abyss* is a trademark of BANDAI NAMCO Entertainment. This project
is unaffiliated with and unendorsed by Bandai Namco, Namco Tales Studio, CRI
Middleware, Criterion Software or Sony Interactive Entertainment.
