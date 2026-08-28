# 03 — Containers

Reproduce with:

```
python tools/cvm.py TO7ROOT.CVM --header
python tools/cvm_census.py FILEDIR
python tools/cvm_census.py FILEDIR --kinds
python tools/fps.py SOMETHING.PKB
```

Output: [`reports/containers.txt`](../reports/containers.txt),
[`reports/codec-census.txt`](../reports/codec-census.txt).

---

## Four levels, and each one is a different house's format

```
ISO 9660                      Sony's, sixteen files, flat root
  TO7*.CVM        x9          CRI ROFS volume  -- middleware
    member        x3,047      an ordinary ISO 9660 directory entry, with a date
      AFS         x17         CRI archive      -- middleware
      FPS3/FPS2   x1,087      in-house archive -- the studio's
      block run   x27         no header at all: blocks laid end to end
        block                 the nine-byte codec block of section 1
```

Nothing here is *Legendia*'s. There is no `AFS_*.AFS` at the root, no parallel
`MBS` size table, no `CPS` envelope, no `TLPS` or `TLPK` wrapper. The whole-image
sweep in [09](09-leftovers.md) looked for all of them and found none.

---

## The nine CRI volumes

Every one of the nine is a `CVMH` container: a 0x1800-byte header followed by an
ordinary ISO 9660 volume. The headers are identical except for their size field:

```
file system          ROFS
built by             ROFSBLD Ver.1.52 2003-06-09
volume id            SAMPLE_GAME_TITLE
publisher            PUBLISHER_NAME
application          (blank)
created              2005112523440100$
```

Three things worth stopping on.

**`ROFSBLD Ver.1.52 2003-06-09` is the same builder, to the day, that produced
*Tales of Symphonia*'s nine CVMs eighteen months earlier.** The tool did not
change between the two discs. Symphonia's carried the same `SAMPLE_GAME_TITLE`
and `PUBLISHER_NAME` defaults too — CRI's placeholders, left in on both.

**All nine declare the same creation second**, `2005-11-25 23:44:01`, which is
the builder's timestamp rather than each volume's; the ISO 9660 directory
records in the outer volume give the real per-volume mastering times, spread
over five minutes.

**Nine volumes, 3,047 members:**

| Volume | Members | Bytes | Earliest member | Latest member |
|---|---:|---:|---|---|
| `TO7ROOT` | 216 | 38,732,384 | 2000-04-25 | 2005-11-25 |
| `TO7FIELD` | 75 | 566,476,350 | 2005-10-05 | 2005-11-24 |
| `TO7MAP` | 630 | 480,479,695 | 2005-10-05 | 2005-11-24 |
| `TO7BTL` | 56 | 271,730,686 | **2005-02-03** | 2005-11-24 |
| `TO7NPC` | 1,054 | 154,126,300 | 2005-09-01 | 2005-11-18 |
| `TO7EV` | 140 | 1,069,993,606 | 2005-10-05 | 2005-11-10 |
| `TO7MOV` | 28 | 981,365,136 | 2005-05-09 | 2005-10-24 |
| `TO7BGM` | 149 | 623,326,150 | 2005-10-05 | 2005-10-21 |
| `TO7SE` | 699 | 140,600,457 | 2005-07-15 | 2005-11-11 |
| | **3,047** | **4,326,830,764** | | |

## The dates are real, and that is new

On *Tales of Legendia* the `AFS` directory's date field was **zero on all 24,835
members**, and the disc's chronology had to be inferred from middleware build
stamps. Here the containers are ISO 9660 volumes, so every member carries a
directory record with a real stamp, and they are not all the same:

| Month | Members written |
|---|---:|
| 2000-04 | 1 |
| 2005-02 | 1 |
| 2005-03 | 2 |
| 2005-04 | 1 |
| 2005-05 | 3 |
| 2005-06 | 8 |
| 2005-07 | 65 |
| 2005-08 | 6 |
| 2005-09 | 78 |
| 2005-10 | **1,529** |
| 2005-11 | **1,353** |

94.5% of the disc's members were written in the last eight weeks before
mastering. The four files older than June 2005 are the ones section
[08](08-cross-title.md) is about.

And the volumes froze in an order that reads like a schedule:

| Volume | Newest member |
|---|---|
| `TO7BGM` | 2005-10-21 11:22:56 |
| `TO7MOV` | 2005-10-24 10:47:28 |
| `TO7EV` | 2005-11-10 13:57:37 |
| `TO7SE` | 2005-11-11 21:01:22 |
| `TO7NPC` | 2005-11-18 14:38:40 |
| `TO7BTL` | 2005-11-24 18:09:22 |
| `TO7FIELD` | 2005-11-24 18:17:52 |
| `TO7MAP` | 2005-11-24 18:18:00 |
| `TO7ROOT` | 2005-11-25 22:37:58 |

Music and video first, by a month; then voice and effects; then models; then the
three geometry volumes within nine minutes of each other on the last working
day; then the root, whose newest member is the executable itself, at 22:37 on
mastering day. Five of the nine volumes' newest members are their `VSSVER.SCC`
([09](09-leftovers.md)).

The 17 `AFS` archives carry their own per-member date fields too, and unlike
Legendia's **they are filled**: `CHT.AFS`'s members run from 2005-10-06 16:10:20
onward, `BTL.AFS`'s from 2005-09-07 19:02:00. So this disc has a second, finer
chronology inside the first.

---

## `FPS3` and `FPS2`

The studio's own archive header, in two revisions, 1,087 of them at the top
level of the volumes and many more nested. Not `FPS4` — the whole-image sweep
returns two four-byte `FPS4` hits against an expected noise rate of about one,
and neither is a header.

```
FPS3                                 FPS2
+0x00  "FPS3"                        +0x00  "FPS2"
+0x04  u32  slot count               +0x04  u32  slot count
+0x08  u32  table offset (0x1C)      +0x08  u32  zero
+0x0C  u32  first data offset        +0x0C  u32  zero
+0x1C  table                         +0x40  table
slot: u32 offset, u32 size, char[4]  slot: char[4], u32 offset, u32 size
```

The two revisions differ in exactly two things: where the table starts, and the
order of the fields inside a slot. `FPS3` puts the extension last, `FPS2` puts
it first.

Both allow empty slots and they mark them differently — `FPS3` writes
`0xFFFFFFFF` as the offset, `FPS2` leaves the tail of its table filled with
`0xFE` — and **the count field cannot be trusted in `FPS2`**: every `FPS2` on
this disc declares 67 slots and none has more than seven real ones, so a reader
that believes the count walks straight off the end of the table and into the
payload. The bound to use is the first data offset. `tools/fps.py` does that and
says so in its own docstring.

Slots repeat. An `FPS3` frequently lists the same `(offset, size)` twice under
the same extension, so a slot count is not a payload count; `codec_census.py`
deduplicates before descending.

The extensions inside are the studio's: `rpx`, `anm`, `cb7`, `sb7`, `bin`,
`F_fl`, `skit`.

---

## Members with no header at all

Twenty-seven of the largest members on the disc have no container header,
because they are not containers. They are **flat runs of nine-byte codec
blocks**, each starting on a 2,048-byte boundary so the loader can seek to one
without reading the ones in front of it:

```
F0.PKF     37,951,488 bytes     292 blocks, covering 100.00% of the file
F3.PKF     29,687,808 bytes   4,634 blocks
BTL_ENM.BIN 77,283,328 bytes     316 blocks
```

This matters more than it looks. A census that stops at the member level sees
`F0.PKF` as *one* block — its first nine bytes are a perfectly valid header —
decodes 163,176 bytes out of 37,951,488, gets a length match, and reports
success.
**46,345 of this disc's 47,513 blocks are inside such a run**, which is 97.5% of
them and 545 MB of packed data. The run walker accepts a run only if the walk
reaches the end of the member, which is what stops an ordinary file whose first
byte happens to be 1 or 3 from being mistaken for one.

---

## The `AFS` archives

Seventeen, 1,101,207,552 bytes, all audio. Plain CRI `AFS`: magic, count,
`(offset, size)` extent table, then a 48-byte-per-member directory with names,
a six-field date and a size.

Two habits worth recording:

* **Every archive opens with a dummy.** Member 0 is `dmy.adx` or `dummy.adx` in
  all seventeen, and its declared size in the directory equals the archive's
  member count.
* **Five of the seventeen are empty.** `ETC.AFS`, `SCE_08.AFS`, `SCE_09.AFS`,
  `SCE_11.AFS` and `SCE_12.AFS` are 12,288 bytes each and hold only the dummy.
  `SCE_01` through `SCE_12` is a twelve-slot scenario index with four slots
  never filled.

---

## What is not here

Searched for explicitly across the whole 4,357,816,320-byte image and
**not found**: `THEIRSCE` (*Rebirth*'s scenario chunk), `FILE.FPB`
(*Destiny 2*'s container), `VAGp`, `KORG`, `TLPS` and `TLPK` (*Legendia*'s
wrappers), `SourceSafe` as text, and `.pdb`. `MSCF` returns ten hits and
`SCPK` two, both inside compressed and video payload at the rate a four-byte
pattern occurs by chance in 4 GB; `CPS ` and `CPS\0` return seven between them
and every one was located and read, and not one is a sixteen-byte header.
[09](09-leftovers.md) has the full sweep with every line accounted for.
