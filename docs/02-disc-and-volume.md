# 02 — The disc and the volume

Reproduce with:

```
python tools/iso9660.py IMAGE.iso --pvd
python tools/iso9660.py IMAGE.iso
python tools/iso9660.py IMAGE.iso --csv
python tools/sector_map.py IMAGE.iso
```

Output: [`reports/iso-volume.txt`](../reports/iso-volume.txt),
[`reports/sector-map.txt`](../reports/sector-map.txt).

---

## What this actually is

The image supplied was a 3,703,341,728-byte archive holding one file of
4,357,816,320 bytes. Neither number is evidence of anything; the volume
descriptor is.

```
LBA 16     type 1    primary
  system id      PLAYSTATION
  volume id      (blank)
  volume space   2127840 sectors (4357816320 bytes)
  block size     2048
  path table     10 bytes at LBA 257 (L) / 259 (M)
  publisher      NAMCO LTD.
  application    PLAYSTATION
  created        2005112523565200$
LBA 17     type 255  terminator
LBA 18-20  BEA01 / NSR02 / TEA01     UDF bridge
```

**`volume space` is 2,127,840 sectors.** A single-layer DVD holds 2,298,496
sectors of 2,048 bytes, so this is **single layer** with 170,656 sectors to
spare — and `2,127,840 × 2,048 = 4,357,816,320` to the byte, so the image is
exactly the volume the disc declares, with no tail and no truncation. There is
one disc; nothing on it refers to a second.

**The volume identifier is blank.** Thirty-two spaces, as on *Tales of Rebirth*
and *Tales of Legendia*. Three consecutive discs from this studio leave the
field empty while the CRI volumes inside this one ship CRI's untouched default
(section [03](03-containers.md)).

**The path table is ten bytes.** Ten bytes is one record and one record is the
root: **sixteen files, no directories**. *Legendia*'s was 58 bytes and four
subdirectories; this disc goes back to *Rebirth*'s flat root.

**The creation stamp carries a `$` offset byte**, decimal 36 — GMT plus
thirty-six quarter-hours, **UTC+9**, Japan. So `2005-11-25 23:56:52` is local
Tokyo time, and every file on the disc carries the same offset.

**There is a UDF bridge**, as on *Legendia* and unlike *Rebirth* and
*Destiny 2*.

---

## The product code, from the only thing entitled to say it

`SYSTEM.CNF` is 57 bytes:

```
BOOT2 = cdrom0:\SLPS_255.86;1
VER = 1.05
VMODE = NTSC
```

**`SLPS-25586`, `VER = 1.05`, NTSC.** The boot file named there is on the disc
and is the 5,086,288-byte Emotion Engine ELF. Nothing else on the image claims
a different code: the save-data strings compiled into that executable read
`BISLPS-25586TOASB`, `BISLPS-25586_TOASYS` and `/BISLPS-25586_TOA`, which is the
same code again, and the memory-card icons beside them are `toa_sys.ico` and
`toa_game.ico`.

`VER = 1.05` is the highest version field in this corpus — *Legendia* shipped
`1.01`, *Rebirth* `1.00` — but a `VER` field is a string in a configuration
file, not a revision counter that anything checks, so it is recorded and not
interpreted. See [99](99-open-questions.md).

This is the Japanese release. The North American release carries a different
code entirely and is not this disc; nothing here is evidence about it.

---

## Where this disc sits in time

| Build | Volume stamped | Distance from Abyss |
|---|---|---|
| *Tales of Symphonia*, PlayStation 2 | 2004-08-17 | 15 months, 8 days earlier |
| *Tales of Rebirth* | 2004-11-17 | **12 months, 8 days earlier** |
| *Tales of Tactics*, i-appli | 2004-12-16 | 11 months, 9 days earlier |
| *Tales of Legendia* | 2005-07-23 | **4 months, 2 days earlier** |
| ***Tales of the Abyss*** | **2005-11-25** | — |

Four months and two days after *Legendia*, and twelve months after *Rebirth*.
Both gaps matter and they point in opposite directions: section
[06](06-decoder-lineage.md) shows this build's decoder shares nothing with the
one four months before it and a great deal with the one fifteen months before
it.

---

## Sixteen files, no directories

```
LBA         SECTORS        BYTES  PATH
282             136       278305  IOPRP300.IMG
418              38        75808  CEI.IRX
456              36        71696  PFM.IRX
492              30        60992  SDM.IRX
522            2484      5086288  SLPS_255.86
3006            189       386048  IRXARC.BIN
3195              1           57  SYSTEM.CNF
3196         479207    981415936  TO7MOV.CVM
482403        69064    141443072  TO7SE.CVM
551467        19026     38965248  TO7ROOT.CVM
570493       522553   1070188544  TO7EV.CVM
1093046      234954    481185792  TO7MAP.CVM
1328000      132729    271828992  TO7BTL.CVM
1460729      304395    623400960  TO7BGM.CVM
1765124       75810    155258880  TO7NPC.CVM
1840934      276658    566595584  TO7FIELD.CVM
```

Sixteen files, 4,336,242,202 bytes. Six of them are the program — one Emotion
Engine executable, four I/O processor images and the configuration — and the
other nine hold the entire game, as CRI `ROFS` volumes.

### Per-file dates are real

Every directory record carries a stamp and they are not all the same:

```
IOPRP300.IMG   2005-10-05 12:02:07
IRXARC.BIN     2005-10-05 12:02:07
PFM.IRX        2005-11-04 14:35:57
CEI.IRX        2005-11-14 14:18:18
SDM.IRX        2005-11-14 14:18:18
SLPS_255.86    2005-11-25 22:37:58
SYSTEM.CNF     2005-11-25 23:45:21
TO7NPC.CVM     2005-11-25 23:44:33
...
TO7SE.CVM      2005-11-25 23:49:09
```

The executable was linked at 22:37 and the nine volumes were mastered between
23:44:33 and 23:49:09 — a five-minute run — and the volume descriptor was
written at 23:56:52, seven minutes after the last of them. The disc records its
own mastering session.

---

## The layout has no interior gap

`sector_map.py` accounts for every sector:

```
2117592   2127839   10248     all zero
image      2127840 sectors (4357816320 bytes)
slack      10510 sectors (0.4939% of the disc)
```

The sixteen files are laid out back to back from LBA 282 to LBA 2,117,591 with
no hole anywhere between them. All the slack is one 21 MB zero run after the
last volume, plus the 239 sectors of system area and directory that every disc
spends.

| Disc | Interior gap | Slack |
|---|---|---|
| *Symphonia*, PlayStation 2, 2004 | **686 MB** | — |
| *Rebirth*, 2004 | none | — |
| *Legendia*, 2005 | none | 0.529%, all at the end |
| ***Abyss*, 2005** | **none** | **0.4939%, all at the end** |

Three discs in a row with no interior gap. *Symphonia*'s remains the outlier.
