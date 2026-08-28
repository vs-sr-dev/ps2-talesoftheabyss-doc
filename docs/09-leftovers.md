# 09 — Leftovers

Reproduce with:

```
python tools/leftovers.py SLPS_255.86
python tools/leftovers.py IMAGE.iso --sweep
python tools/locate.py IMAGE.iso <offsets>
```

Output: [`reports/leftovers.txt`](../reports/leftovers.txt),
[`reports/magic-sweep.txt`](../reports/magic-sweep.txt).

Everything here is in the shipped retail build.

---

## Twenty-five absolute source paths

Three of the five I/O processor images — `CEI.IRX`, `PFM.IRX`, `SDM.IRX` — were
compiled with Metrowerks and none of them merged its `.comment` sections. They
carry **113, 85 and 74** copies of `MW MIPS C Compiler (2.4.1.01)`, one per
object file, and with them the objects' paths on the machine that built them:

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

*Legendia*'s equivalent was one path, `host0:C:\tox\fieldwork\dev\field\`. This
is the whole sound subsystem's directory tree, with the split between the shared
`CEI` transport layer and the `snd` driver visible in the layout, and `ik_vol.c`
linked into both modules.

`C:\TO7\prog\` is the project root. `TO7` is the tag everything else uses: the
nine volumes, the executable's own volume list (`to7ROOT.cvm`, `to7BTL.cvm`, …),
the C++ class names `CTO7SystemSaveData` and `CTO7GameSaveDataObj`, and one
asset called `TO7PUBLIC.TXD`.

The Emotion Engine side kept two devkit paths of its own, the fallbacks the
loader uses when the disc is not a disc:

```
host0:ioprp300.img
host0:irxarc.bin
```

---

## A sound test, and the whole soundtrack listed in English

A Japan-only release whose executable carries the class family
`CSoundModeControlPanel`, `CSoundModeBgmSelect`, `CSoundModeVoiceSelect`,
`CSoundModeVoiceList`, `CSoundModeProgramList`, `CSoundModePlaySound` — and
next to them, the complete BGM list, **in English**:

```
abyss                        The Royal City of Light
New world                    The Grocer's Village
Qliphoth                     The Fortified City
Guilt, duty and ...          The Frontier Fortress
The last chapter             Desert Oasis
Wedge                        The Mining Town
Wing of hope                 The City of Guardians
The place of relaxation      Port town
...
Flow when being dammed up    Never surrender
Sign of the quiet dark       Fang which wants blood
Relic of wandering frenzy    Awkward justice
The arrow was shot           At the time of farewell
The edge of a decision       meaning of birth
```

Around ninety entries, mixing place names, arrangement titles and lines that
read as translations made for the composer's own reference rather than for a
player (`Flow when being dammed up`, `time to raise the cross`, `a place in the
sun`). The single occurrence of the string `abyss` anywhere in 4.36 GB is the
first track in this list.

This is a data point on the team rather than on the game. *Tales of Rebirth*
romanised its entire cast into English; *Tales of Legendia* had **no English
name table at all**; this disc has a full English track list and no romanised
cast table — its debug strings name characters in capitals (`LUKE`, `ASCH`) but
there is no roster.

---

## Debug strings for things the disc does not do

At `0x0047DD80` in the executable, in Shift-JIS:

```
デバッグ用？ comp_dict_XXX は動作しません
   "debug-only? comp_dict_XXX does not work"

人物名鑑チェック：：TOAはできないようです
   "character-encyclopedia check:: TOA seems unable to"

モンスター図鑑は未実装です
   "the monster encyclopedia is not implemented"

LUKEのパラメータをASCHに引き継ぎました
ASCHのパラメータをLUKEに引き継ぎました
   "LUKE's parameters were carried over to ASCH", and back

ERROR:SYSTEM_GET_ENCOUNT_COUNT に MYSELF は指定できません
ERROR : SET_SYSTEM_user_party_top で不正な引数が指定されました
set_EXPRESSION : %s がありません
enemy_encount : enemy[%d] が存在しません
remove_class : 称号0番は指定できません
```

`comp_dict` is the only name this disc has for a compression dictionary, and it
appears once, in a message saying the debug version of it does not work.

The scripting layer names itself here too: `SYSTEM_GET_ENCOUNT_COUNT`,
`SYSTEM_SET_USER_PARTY_TOP`, `set_EXPRESSION`, `enemy_encount`, `remove_class`,
and the expression set `EYE_DEFAULT00`, `EYE_DEFAULT00_MOVE`, `MOUTH_DEFAULT00`,
`MOUTH_DEFAULT00_TALK`.

---

## Nine Visual SourceSafe status files

`VSSVER.SCC`, binary, magic `34 12 01 00`, one in each of the nine volumes:

| Volume | Bytes | Written |
|---|---:|---|
| `TO7NPC` | 16,880 | 2005-11-18 14:38:40 |
| `TO7MAP` | 10,992 | 2005-11-24 18:18:00 |
| `TO7SE` | 8,656 | 2005-11-09 23:45:02 |
| `TO7ROOT` | 2,912 | 2005-11-25 16:52:46 |
| `TO7BGM` | 2,400 | 2005-10-21 11:22:56 |
| `TO7EV` | 2,320 | 2005-11-10 13:57:37 |
| `TO7FIELD` | 1,216 | 2005-11-24 18:17:52 |
| `TO7BTL` | 736 | 2005-11-24 18:09:22 |
| `TO7MOV` | 400 | 2005-10-24 10:47:28 |

These are the working-copy state files Visual SourceSafe writes into a checked-out
directory. Nine asset directories were checked out of source control and mastered
onto the disc with the checkout marker still in them, and in **five of the nine**
the marker is the newest member in its volume — so in those five it is the last
thing that touched the directory before it was mastered. `TO7ROOT`'s is dated
16:52 on mastering day, six hours before the executable was linked.

No sibling disc in this corpus carries one.

---

## Thirty-six overlays in nine configurations

Metrowerks `MWo3` overlays, four roles × nine prefixes, **all thirty-six
distinct** by content and mostly by size. Each carries its own build name in its
header — `ov_D_btl.ovl`, `ov_P_S_DVD_field.ovl` — matching the file name on disc.

| | `BTL` | `FIELD` | `SFD` | `SKIT` |
|---|---:|---:|---:|---:|
| `D` | 740,352 | 738,944 | **32,512** | 244,480 |
| `MD` | 747,264 | 772,992 | 268,800 | 247,552 |
| `DVD` | 571,904 | 665,984 | 268,800 | 215,936 |
| `FR` | 571,904 | 665,984 | 268,800 | 215,936 |
| `F_DVD` | 560,768 | 637,312 | 268,800 | 215,552 |
| `PDVD` | 520,704 | 492,416 | 268,800 | 206,976 |
| `PFR` | 520,704 | 492,416 | 268,800 | 206,976 |
| `P_S_DVD` | 520,704 | 492,416 | 268,800 | 206,976 |
| `R` | **429,312** | **331,904** | **32,512** | **355,200** |

`D` and `R` are the two that break the pattern: both have a 32 KB `SFD` overlay
where the other seven have 268 KB, and `R` is the smallest in three roles and the
largest in the fourth. What the nine prefixes mean is not stated anywhere on the
disc. See [99](99-open-questions.md).

---

## Placeholders, at scale

**611 copies of one file.** `TO7EV.CVM:/SE.AFS` has 1,025 slots and 405 distinct
payloads. 611 of the slots are named `dummy.adx` and all 611 hold the identical
13,810-byte stream, at 611 separate offsets — **8,437,910 bytes** of one
placeholder, 0.19% of the disc. Across all seventeen archives, 15,689 members
hold 14,944 distinct payloads and the repeats cost 10,199,882 bytes.

**Every archive opens with a dummy.** Member 0 of all seventeen is `dmy.adx` or
`dummy.adx`, and the size the directory declares for it equals the archive's own
member count.

**Five archives hold nothing else.** `ETC.AFS`, `SCE_08.AFS`, `SCE_09.AFS`,
`SCE_11.AFS` and `SCE_12.AFS` are 12,288 bytes each. `SCE_01` … `SCE_12` is a
twelve-slot scenario index with four slots never filled.

**Two test assets in the index.** The battle overlays list 619 distinct `.slz`
names and two of them are `_btm_test00.slz` and `_btm_test01.slz`.

**A gap in the music numbering.** `TOA_SFXBGM_MD00` through `MD06` exist as MIDI
sequences; `MD04` does not.

---

## A Sony SDK module five years older than the disc

```
/MEM2MB.IRX   1,425 bytes   2000-04-25 16:15:40 +9
```

Every other file in the file system is 2005. This one predates the disc by five
years and seven months, and it is the oldest timestamp on it by four years and
nine months — the second-oldest is `BTL_NANARI.SLZ`, 2005-02-03. It is Sony's
module for restricting the console to 2 MB of I/O processor RAM, shipped
unchanged.

---

## The end roll shipped as plain text

`TO7ROOT.CVM:/TOAEND_JP.TXT`, 12,397 bytes, 1,274 CRLF lines of which 732 are
non-blank, Shift-JIS, with `@`-prefixed layout codes (`@s4`, `@o0`, `@h`, `@\6`)
interleaved with the credit lines. It is the staff roll, uncompiled and
uncompressed, sitting beside the game's data where any text editor could open it —
the only human-readable document on the disc.

268 of its non-blank lines are pure ASCII; the rest are Japanese.

---

## Middleware that named itself, twice

**RenderWare.** Three paths out of the SDK's own daily build tree —
`c:/daily/rwsdk/plugin/pds/sky2/G3_2DStroke/G3_2DStroke_Node.c` and two
siblings — with `Core built at Jul 16 2004 17:14:46`, the diagnostics
`PS2 material pipes` / `PS2 sector pipes` / `PS2 atomic pipes` /
`Only rendering sub system`, and twenty-seven `PS2*.csl` pipeline node names.
The word "RenderWare" is nowhere in the binary; `rwsdk` and `pds` are its own
directory names. **No other disc in this corpus uses it.**

**CRI, built to the second.** Twenty-four components stamped inside a
twenty-nine-second window:

```
PL2ENC     Ver.1.01  Build:Feb 28 2005 19:25:06
SJ/PS2EE   Ver.6.31  Build:Feb 28 2005 19:25:09
...
G/PS2EE    Ver.1.002 Build:Feb 28 2005 19:25:35
ROFS       Ver.1.77  Build:Mar  2 2005 11:30:59
ROCI       Ver.1.15  Build:Mar  2 2005 11:31:01
RSU        Ver.1.10  Build:Mar  2 2005 11:31:01
```

*Legendia* carried the same habit — nine components in twenty-six seconds on
12 April 2004 — so two discs now show a single library build each, frozen at the
second it finished.

And the nine `CVM` volumes were built by `ROFSBLD Ver.1.52 2003-06-09`, which is
the same builder to the day that produced *Tales of Symphonia*'s nine volumes
eighteen months earlier, still shipping CRI's unfilled `SAMPLE_GAME_TITLE` and
`PUBLISHER_NAME`.

---

## Build stamps inside the assets

The `SB7` map payloads open with their producing tool's `__DATE__` and
`__TIME__`, so the map data dates itself independently of the file system:

```
x2   SB7 Dec 17 2004 10:28:51      <- the oldest tool build on the disc
x1   SB7 Jan  4 2005 15:05:26
x11  SB7 Feb 25 2005 17:15:53      <- the most used
x4   SB7 Mar  9 2005 15:20:35
x1   SB7 Apr  1 2005 11:42:09
x3   SB7 Apr 21 2005 17:13:51
x4   SB7 May 23 2005 15:14:32
x4   SB7 May 24 2005 17:13:58
x4   SB7 Oct  9 2005 15:56:47
```

`Dec 17 2004` is one month after *Tales of Rebirth*'s disc was stamped and one
day after *Tales of Tactics* was built.

---

## Save data with the real product code

```
BISLPS-25586TOASB
BISLPS-25586_TOASYS
/BISLPS-25586_TOA
icon.sys   toa_sys.ico   toa_game.ico   _mcico.slz
```

*Rebirth* shipped `BISLPS-00000ToRsv%02d` with the code left as zeroes;
*Legendia* shipped `BISLPS-25533TOL-S` with the real one. So does this — three
times, in three different string formats.
