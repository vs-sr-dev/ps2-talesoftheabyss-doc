# 08 — What this disc carries from other *Tales* titles

Reproduce with:

```
python tools/leftovers.py IMAGE.iso --sweep
python tools/locate.py IMAGE.iso <every non-zero offset>
python tools/cvm_census.py FILEDIR --csv
```

Output: [`reports/magic-sweep.txt`](../reports/magic-sweep.txt),
[`reports/cross-title.txt`](../reports/cross-title.txt).

---

*Tales of Rebirth* (2004) was the first disc in this corpus with nothing from
another title on it. *Tales of Legendia* (2005) was the second. **This one is
not the third**, and what it carries is specific, dated, and traceable to the
disc it came from.

---

## 109 sound effects from *Tales of Rebirth*

`TO7EV.CVM:/SE.AFS` holds 1,025 members. Their names are prefixed by title:

| Prefix | Members | Bytes | Written |
|---|---:|---:|---|
| `dummy.adx` | 611 | 8,437,910 | 2005-08-26 11:12:04 |
| `toa_` | 211 | — | 2005-08-26 11:12:00 – 11:12:58 |
| **`tor_`** | **109** | **9,573,862** | **2005-08-26 11:12:04 – 11:14:14** |
| `sfxse_` | 94 | — | 2005-08-26 11:12:12 – 11:12:20 |

`toa` is this game's own tag — it is what the memory-card strings, the icons and
the end-roll text file use. `tor` is *Tales of Rebirth*'s; the corpus records
that disc shipping `BISLPS-00000ToRsv%02d` in its save-data strings.

The 109 are footsteps, doors, magic and impacts:

```
tor_no_se_mp_steps04.adx        tor_no_se_mp_door_open00.adx
tor_no_se_mp_steps05.adx        tor_no_se_mp_door_close00.adx
...            through 12       tor_no_se_mp_dan_etto_burst00.adx
tor_no_se_bt_mag_rise1.adx      tor_no_se_mp_mg3_grass_break.adx
```

Strip the `tor_` and the remainder is a name in *Rebirth*'s own scheme —
`no_se_mp_`, `no_se_bt_`, `no_se_ev_`. So the test is direct: take the 105
distinct names, strip the prefix, and search *Tales of Rebirth*'s 4,508,516,352-byte
disc image for each.

**All 105 are there.** Not 104, not 103. *Rebirth*'s own effect table sits at
offset `0x685328F2` of that image and reads:

```
no_se_mp_steps00   no_se_mp_steps00_b   no_se_mp_steps01   no_se_mp_steps01_b
no_se_mp_steps02   no_se_mp_steps02_b   ...   no_se_mp_steps12
```

which is the same series, with `_b` variants this disc did not take.

**The audio itself was re-encoded, not copied.** A 64-byte needle from the
middle of six of the `tor_` streams appears nowhere in *Rebirth*'s image, and
neither does an ADX header from any of them. So this is a sound library being
re-imported and re-compressed, keeping the source title's names and marking
them with the source title's tag — which is what a shared internal effects
library looks like from the outside, and not what copying files off a master
looks like.

All of `SE.AFS` was packed in one run on **2005-08-26 between 11:12:00 and
11:14:14**, so the `tor_` effects went in at the same moment as the game's own.

Nothing else on the disc carries a foreign prefix. Across **18,736 member names**
— 3,047 from the nine volumes and 15,689 from the seventeen `AFS` archives —
the prefixes `tos`, `tod`, `toe`, `top` and `to8` return **zero**.

---

## Three battle models named for three earlier games' characters

`TO7BTL.CVM` holds 32 compressed battle models. Twenty-nine of them are named
for this game's cast — `BTL_LUK*`, `BTL_TEA*`, `BTL_JAD*`, `BTL_ANS*`,
`BTL_GUY*`, `BTL_NAT*`, `BTL_ASH*`. Three are not:

| File | Bytes | Written | Decodes to |
|---|---:|---|---|
| `BTL_NANARI.SLZ` | 150,762 | **2005-02-03 10:02:04** | 223,456 |
| `BTL_RID.SLZ` | 259,117 | **2005-03-10 16:46:14** | 396,928 |
| `BTL_FIRIA.SLZ` | 147,390 | **2005-03-22 12:41:34** | 264,224 |

Those three names are not in this game's cast. They are the romanisations of one
lead character from each of the three earlier PlayStation-family titles in this
corpus:

| Name on this disc | Character | Title | Year |
|---|---|---|---|
| `FIRIA` | Philia Felice | *Tales of Destiny* | 1997 |
| `RID` | Reid Hershel | *Tales of Eternia* | 2000 |
| `NANARI` | Nanaly Fletch | *Tales of Destiny 2* | 2002 |

**This is marked *Consistent*, not Verified.** The names match and the pattern —
one per earlier title, in release order — is not what coincidence produces, but
the disc nowhere states what they are. See [99](99-open-questions.md).

Two things about them are Verified, and both are measurements.

**They are the three oldest game assets on the disc.** Every other file in the
file system is newer, including the protagonist's: `BTL_LUK02.SLZ` is dated
2005-06-14, more than four months after `BTL_NANARI.SLZ`. Excluding one Sony SDK
module from 2000, the disc's chronology opens with these three and nothing else.

```
2005-02-03  BTL_NANARI.SLZ
2005-03-10  BTL_RID.SLZ
2005-03-22  BTL_FIRIA.SLZ
2005-04-21  BTL_ASH01.SLZ      <- the first of this game's own
```

**Nothing on the disc names them.** The executable does not contain the strings
`NANARI`, `FIRIA` or `BTL_RID` anywhere across 5,086,288 bytes; nor does any of
the 36 overlays, which between them list 619 distinct `.slz` names including two
called `_btm_test00.slz` and `_btm_test01.slz`. The only place these three files
are named is the `ROFS` directory entry that stores them.

### They belong to a numbered series that the disc does keep using

Decoded, each of the three is an `FPS3` archive whose parts carry internal tags
in this disc's own convention — `C_b00`, `C_l00`, `C_m00`, `C_r00` followed by a
model code:

```
BTL_RID.SLZ      C_b00exc000  C_l00exc000  C_m00exc000
BTL_NANARI.SLZ   C_l00exc001  C_m00exc001  C_r00exc001
BTL_FIRIA.SLZ    C_b00exc002  C_l00exc002  C_m00exc002  C_r00exc002
```

`exc000`, `exc001`, `exc002` — an internally numbered series, and the series
continues in `TO7NPC.CVM` with models the battle volume has no counterpart for:

```
EXC003.NPC   262,084 bytes   2005-09-27   C_b00exc003 ...
EXC004.NPC    15,784 bytes   2005-10-05   C_k06exc006 ...
TOL00.NPC    134,412 bytes   2005-10-13   C_b00tol00 ...
```

`EXC004.NPC` is tagged `exc006`, so the series has gaps: 004 and 005 are not on
the disc. And `TOL00.NPC` is the **only one of the disc's 877 `.NPC` members**
whose three-letter prefix is neither a character abbreviation nor an object
family used elsewhere — `TOL` occurs exactly once, and `TOL` is *Tales of
Legendia*'s project tag, from a disc mastered four months and two days before
this one.

That last observation is thin on its own and is recorded as thin. `tol00` is a
five-character model code in a scheme that also contains `exc000` and `ash00`,
and nothing in the file, its neighbours or the executable says what it is. It
goes in [99](99-open-questions.md) with its measurement beside it and no
conclusion.

---

## And what is *not* here

The whole-image sweep looked for every marker the sibling pipelines have used
and every one of them came back at or below the noise rate for its length. In
4,357,816,320 bytes a four-byte pattern occurs about **1.01 times** by chance
and a three-byte pattern about **260**:

| Pattern | Hits | Reading |
|---|---:|---|
| `Symphonia`, `symphonia`, `destiny`, `DESTINY`, `eternia`, `phantasia`, `Venus`, `rebirth`, `REBIRTH`, `legendia`, `LEGENDIA`, `Legendia` | **0** | — |
| `THEIRSCE` (*Rebirth*, 2004) | **0** | — |
| `FILE.FPB` (*Destiny 2*, 2002) | **0** | — |
| `TLPS` (*Legendia*'s AHX wrapper) | **0** | — |
| `KORG` (*Legendia*'s sound house) | **0** | — |
| `VAGp` | **0** | — |
| `TLPK` (*Legendia*'s package tag) | 4 | 4-byte; all four inside compressed `.SKT` / `.PKB` payload |
| `CPS ` + `CPS\0` (*Legendia*'s envelope) | 7 | 4-byte; six in Sofdec/ADX payload, one in `CHT.AFS` |
| `SCPK` (*Destiny 2*'s bundle) | 2 | 4-byte; both inside `.PKB` payload |
| `MSCF` | 10 | 4-byte; all inside stream payload |
| `TOD2` / `tod2` | 1 / 1 | 4-byte, at rate |
| `ToR` | 174 | 3-byte, **below** 260 |
| `ToL` / `tox` | 178 / 151 | 3-byte, below 260 |
| `TOL` | 419 | 3-byte, 1.6× the rate — none is a tag |
| `TOP2` | **25** | 4-byte, 25× the rate — **and it is not a finding** |

The `TOP2` line is the one that had to be read rather than counted. Twenty-five
hits of *Symphonia*'s project tag looks like something. Every one of them is
inside a single file, `TO7MOV.CVM:/AS_009.SFD`, and the 48-byte window around
each is **byte-for-byte identical to the others**: one repeating pattern in one
214 MB video stream. `locate.py` printed all four sampled windows side by side
and they are the same forty-eight bytes.

Every non-zero line above was located and its neighbourhood read. None of them
is a header, a name or a tag.

---

## So

Three discs in a row from this studio were supposed to be a policy. They are
not. *Rebirth* and *Legendia* carried nothing from anywhere; this one carries a
sound library from *Rebirth* under *Rebirth*'s names, and three battle models
named for the leads of 1997, 2000 and 2002 that are the oldest assets it has.

The two carries are different in kind, and that is the interesting part. The
sound effects were **re-encoded from a shared library** and kept the source
title's naming so that anyone reading the archive can see where they came from.
The three models were **built for this project**, in this project's own model
scheme, numbered `exc000`–`exc002` in a series that runs to at least `exc006` —
and they were built *first*, before anything else in the game.
