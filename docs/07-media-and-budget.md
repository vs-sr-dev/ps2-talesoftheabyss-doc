# 07 — Media and the disc budget

Reproduce with:

```
python tools/media_census.py FILEDIR
python tools/media_census.py FILEDIR --voice
python tools/disc_budget.py IMAGE.iso FILEDIR
```

Output: [`reports/media-census.txt`](../reports/media-census.txt),
[`reports/disc-budget.txt`](../reports/disc-budget.txt).

---

## Where 4,357,816,320 bytes went

Every leaf is classified from its own first bytes, never from its name — the
same `.PKB` extension covers a raw codec block, an `FPS2` archive and a bespoke
index, and `SND`-style names inside the `AFS` directories would put a music cue
and a voice line in the same bucket.

| Class | Bytes | Of the image |
|---|---:|---:|
| **compressed game data** (codec blocks) | 1,069,195,048 | **24.54%** |
| **voice** (AHX) | 985,237,321 | **22.61%** |
| **video** (Sofdec) | 981,364,736 | **22.52%** |
| **audio** (ADX: music, ambience, effects) | 720,509,996 | 16.53% |
| other game data | 462,444,008 | 10.61% |
| texture (`TIM2`) | 18,538,720 | 0.43% |

```
named files            4336242202   99.50%
outside the volumes       5959194    0.14%
the nine CVM volumes   4330283008   99.37%
image slack              21574118   0.4951%
container/slack (inside the volumes)  92993179  2.13%
```

**video + voice = 45.13%. All media = 61.66%.**

### Beside the siblings

| Disc | Year | Size | video + voice | all media |
|---|---|---|---:|---:|
| *Tales of Rebirth* | 2004 | 4.51 GB | **67.2%** | — |
| *Tales of Tactics*, i-appli | 2004 | 369 KB | — | 63.3% |
| ***Tales of the Abyss*** | **2005** | **4.36 GB** | **45.13%** | **61.66%** |
| *Tales of Legendia* | 2005 | 4.08 GB | — | 37.70% |
| *Tales of Legendia*, less `CDVD.000` | 2005 | 3.01 GB | — | 51.54% |

Abyss sits between the two, and it is the first disc in this corpus where the
largest single class is **not** media: 24.54% of it is compressed game data,
1.07 GB packed expanding to 2.64 GB. *Rebirth* spent two thirds of its disc on
streams; *Legendia* spent a third; this one spends three fifths on media and a
quarter on geometry, and the quarter is the biggest single number on the disc.

The reason is where the media went rather than how much of it there is. This
disc has **more** voice than *Legendia* had audio of any kind — 985 MB of AHX
against Legendia's 399.8 MB of voice — and it has a full gigabyte of video.
What it does not have is *Rebirth*'s 1.30 GB of SPU-ADPCM.

---

## Video

27 Sofdec streams, 981,364,736 bytes, all in `TO7MOV.CVM`, all MPEG-2 program
streams read from their own sequence headers:

| Streams | Size | Aspect | Frame rate | Declared bit rate |
|---:|---|---|---|---|
| 9 | 512×448 | 4:3 | 29.97 | 1,800,000 |
| 8 | 512×448 | 4:3 | 30 | 3,600,000 |
| 1 | 512×448 | 4:3 | 30 | 4,500,000 |
| 4 | 512×448 | — | 29.97 | variable |
| 2 | 512×448 | — | 30 | variable |
| 3 | **640×480** | — | 29.97 | variable |

Nine of the twenty-seven set the bit-rate field to all ones — the MPEG
convention for "variable" — and an aspect-ratio code of 12, which is reserved.
They are reported as measured rather than repaired; the three 640×480 streams
are all in that group, and they are `OP.SFD` and the two largest cutscenes.

Compare *Legendia*: 22 streams at 640×320, 29.97 fps.

The largest single file on the disc is `TO7MOV.CVM:/AS_009.SFD` at 213,897,216
bytes. `TO7MOV.CVM` also carries the only `VSSVER.SCC` older than November.

---

## Voice: 13.60 hours of AHX

12,643 AHX streams, 985,237,321 bytes, every one of them inside an `AFS`
archive in `TO7EV.CVM`. And every one of the 12,643 has the **identical**
first frame header, `ff f5 e0 c0`:

```
MPEG-2 LSF, layer II, 160,000 bit/s, 22,050 Hz, mono
```

so the playing time is arithmetic on the frame size rather than an estimate:
`(size − 0x24) / 1044 × 1152 / 22050`, summed, is **13.60 hours**.

The 12,643 split into three groups by the archive they are in:

| Archive | Streams | What |
|---|---:|---|
| `SCE_01` … `SCE_10` | 12,072 | scenario dialogue, eight archives used of twelve |
| `CHT.AFS` | 505 | the skits |
| `SYS.AFS` | 27 | system voice — `JGL_*`, `MYU_*`, `FUKA_VO_*` |

*Legendia* measured 13.97 hours, but all of it as ADX, and only 399.8 MB of it
was voice. This disc puts 985 MB into voice alone and does it in a codec
*Legendia* used for 2.67 MB.

---

## Audio: 4.62 hours of ADX, and six MIDI sequences

3,182 ADX streams, 720,509,996 bytes, 4.62 hours by the headers' own sample
counts. 2,816 mono and 366 stereo; 1,877 at 24 kHz, 1,121 at 48 kHz, 184 at
22.05 kHz.

They are three different things:

| Where | Streams | Bytes | What |
|---|---:|---:|---|
| `TO7BGM.CVM`, loose | 136 | 621,249,286 | the music, streamed, `TOA_SFXBGM_*.ADX` |
| `BTL.AFS` | 2,006 | 58,652,662 | battle voice |
| `SE.AFS` | 1,025 | 40,347,248 | sound effects |

**The music is streamed and it is 621 MB** — 14.3% of the disc in 136 cues, the
largest of them 13.2 MB. That is the direct opposite of *Legendia*, whose entire
soundtrack was 136,763 bytes of MIDI played out of 25.8 MB of KORG sample banks.

But not entirely. `TO7BGM.CVM` also holds a small sequenced set, in Sony's own
format:

```
TOA_SFXBGM_MD00.SQ   9,008     .HD  3,424     .BD    842,272
TOA_SFXBGM_MD01.SQ  16,704     .HD  1,808     .BD    328,720
TOA_SFXBGM_MD02.SQ  11,424     .HD  3,392     .BD    817,264
TOA_SFXBGM_MD03.SQ  16,560
TOA_SFXBGM_MD05.SQ   3,440
TOA_SFXBGM_MD06.SQ  20,448
```

**Six sequences totalling 77,584 bytes**, with three sample banks of 1,988,256.
`PFM.IRX` on the I/O processor is the player — `PFM_midi.c`, `sceMidi_Init`,
`sceMidi_SelectMidi` — driving Sony's stock `modmidi.irx` and `modhsyn.irx` out
of `IRXARC.BIN` ([04](04-executables.md)).

So both 2005 discs ship a MIDI player on the I/O processor and both stream the
rest. The difference is the ratio: *Legendia* put **thirty** cues in sequences
and streamed none of its music; this one puts **six** in sequences and streams
136. `MD04` is missing from the numbering.

`SE.AFS` is worth one more line. It has 1,025 slots and **405 distinct
payloads**: 611 of the 1,025 are the same 13,810-byte `dummy.adx`, stored 611
separate times, which is 8,437,910 bytes of one placeholder. Across all
seventeen `AFS` archives, 15,689 members hold 14,944 distinct payloads, and the
repeats cost 10,199,882 bytes.

---

## Compressed game data

24.54% of the disc, and section [05](05-block-codec.md) has the census. In
budget terms:

| Volume | Packed on disc | Unpacked |
|---|---:|---:|
| `TO7FIELD` | 488,008,888 | — |
| `TO7MAP` | 459,730,429 | — |
| `TO7SE` | 110,196,939 | — |
| `TO7BTL` | 11,317,586 | — |
| all | **1,069,278,379** | **2,643,327,828** |

The disc holds 2.64 GB of field, map and battle data in 1.07 GB of space. A
4.36 GB disc is carrying 5.93 GB of content.

`TO7SE.CVM` is worth noting: it is named for sound effects, and 110 MB of it is
**compressed geometry** — 538 `.SKT` members, all codec blocks. The volume names
on this disc are not a reliable guide to what is in them, which is the same
lesson the `.PKB` extension teaches inside them.

---

## The disc is full and there is nothing hidden in it

`sector_map.py` finds no interior gap: the sixteen files run back to back from
LBA 282 to LBA 2,117,591, and the only slack is a 21 MB zero tail and the
239 sectors of system area. Inside the volumes, 2.13% of the image is container
overhead — `CVM` headers, ISO 9660 directories, `AFS` extent tables and the
padding between sector-aligned members — and it is reported on its own line
rather than charged to whatever it happens to sit beside.

There is no `CDVD.000` here. *Legendia*'s 1.07 GB unreferenced file, a year-old
build's asset set mastered along with the game, has no counterpart: every one of
this disc's sixteen files is named by `SYSTEM.CNF` or by the executable, and the
largest thing that looked like padding — the 27 header-less `.PKF` and `.BIN`
members, 745 MB between them — turned out to be 46,345 codec blocks. Profiling
before writing off was the right call again.
