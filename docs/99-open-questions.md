# 99 — Open questions

Everything here has a measurement beside it. Where the disc cannot settle
something, it is left unsettled rather than softened.

---

### 1. Why does this build compile the *unedited* copy of the 2004 source?

**Measured.** Abyss's decoder shares **69 bytes** and 17 identical instruction
words with the pair at `0x00242C5C` / `0x0024324C` in `SLPS_254.00`, and **4
bytes** and one word with the pair at `0x001C93D0` / `0x001C9820` in the same
file. `SLPS_254.00` carries both, and they share 2 identical words in 276 with
each other. So *Symphonia*'s PlayStation 2 port had two unrelated
implementations of this codec linked into one executable, and this disc
descends from the one that was **not** edited for the Emotion Engine.

**Open.** Whether that is a choice or an accident. Three readings fit the bytes
equally: the 4080 quadword variant was a local optimisation nobody propagated;
the two copies came from different libraries and Abyss's team pulled the older
one without knowing the other existed; or the older one was simply what was in
whatever archive the project started from. Nothing on either disc distinguishes
them. [06](06-decoder-lineage.md)

### 2. Why does *Symphonia*'s dispatcher have a case for method 2 and this one not?

**Measured.** Symphonia's classic dispatcher at `0x00242B70` tests `2`, then
`3`, then `1`, then `0`, and routes `2` to the same target as the fallthrough.
Abyss's at `0x00122150` tests `3`, then `1`, then `0`, and falls through to
`addiu v0, zero, -1`. Method 2 has never appeared in a block on any disc in
this corpus.

**Open.** Whether Abyss deleted a dead case or Symphonia added one. The corpus
records that *Destiny 2*'s I/O processor copy dispatched on internal kinds
**2 and 4**, and that both of *Rebirth*'s copies did; a `2` in the on-disc
dispatcher is at least adjacent to that renumbering, but adjacency is not
evidence. [05](05-block-codec.md), [06](06-decoder-lineage.md)

### 3. Did *Legendia*'s team have this source file?

**Not answerable from these discs, and worth stating because the temptation is
strong.** Abyss demonstrates the source was on hand somewhere in the studio in
2005. *Legendia*, four months earlier, reproduced the format exactly without
using it. That is compatible with the file being unavailable to that team, and
equally compatible with it being available and not used. A disc records what
was compiled, not what was on the network drive. [06](06-decoder-lineage.md)

### 4. What do the nine overlay prefixes mean?

**Measured.** 36 `MWo3` overlays, four roles (`BTL`, `FIELD`, `SFD`, `SKIT`) ×
nine prefixes (`D`, `DVD`, `F_DVD`, `FR`, `MD`, `PDVD`, `PFR`, `P_S_DVD`, `R`),
all 36 distinct by content. `D` and `R` both carry a 32,512-byte `SFD` overlay
where the other seven carry 268,800; `R` is the smallest in three roles and the
largest in the fourth.

**Open.** Nothing on the disc says what the prefixes select. `DVD` appearing in
five of the nine and `P` in three suggests a media or hardware axis crossed
with something else, and the sizes are consistent with that, but a plausible
expansion of nine two-to-seven-character tokens is not a finding.
[09](09-leftovers.md)

### 5. What is `TOL00.NPC`?

**Measured.** One member of `TO7NPC.CVM`, 134,412 bytes, an `FPS3` archive
dated 2005-10-13, whose parts are tagged `C_b00tol00`, `C_l00tol00`,
`C_m00tol00`, `C_r00tol00` in this disc's own model-naming convention. `TOL` is
the three-letter prefix of exactly **one** of the disc's 877 `.NPC` members, and
it is the only such prefix that is neither a character abbreviation nor an
object family used elsewhere. `TOL` is also *Tales of Legendia*'s project tag,
from a disc mastered four months and two days earlier.

**Open, and thin.** `tol00` is a five-character model code in the same scheme
that contains `exc000` and `ash00`; nothing in the file, its neighbours or the
executable says what it depicts. It is recorded because it is the only name of
its kind on the disc, not because the reading is supported. [08](08-cross-title.md)

### 6. Are `RID`, `FIRIA` and `NANARI` the characters they look like?

**Measured, and this half is Verified.** Three compressed battle models in
`TO7BTL.CVM` carry names that are in no part of this game's cast, they are the
**three oldest game assets on the disc** (2005-02-03, 2005-03-10, 2005-03-22,
against 2005-04-21 for the first of the game's own), **nothing on the disc names
them** — zero occurrences of `NANARI`, `FIRIA` or `BTL_RID` across the 5 MB
executable and all 36 overlays — and internally they are `exc000`, `exc001` and
`exc002`, a numbered series that continues to at least `exc006` in the NPC
volume.

**Consistent, not Verified.** That `FIRIA` is Philia Felice (*Tales of Destiny*,
1997), `RID` is Reid Hershel (*Tales of Eternia*, 2000) and `NANARI` is Nanaly
Fletch (*Tales of Destiny 2*, 2002). One lead per earlier PlayStation-family
title in the corpus, in release order, is not what coincidence produces — but
the disc states none of it, and the identification comes from outside the bytes.
[08](08-cross-title.md)

### 7. Why does the sound-effect archive store one placeholder 611 times?

**Measured.** `SE.AFS` has 1,025 extent slots and 405 distinct payloads. 611
slots are named `dummy.adx`, all 611 hold the identical 13,810-byte stream, and
all 611 have their own offset — 8,437,910 bytes.

**Open.** A fixed-size index whose unused slots were filled by the packing tool
rather than left as zero-length extents is the obvious reading, and the tool
would have had to be told to do that. Whether the 1,025 is a hard limit, a
round number, or the size of an earlier effect list is not on the disc.
[07](07-media-and-budget.md), [09](09-leftovers.md)

### 8. Why is `VER = 1.05`?

**Measured.** `SYSTEM.CNF` reads `VER = 1.05`. *Legendia* read `1.01`,
*Rebirth* `1.00`.

**Open.** `VER` is a string in a text file that the boot loader does not
compare against anything. It may count revisions, or builds, or nothing. No
second image of this title was examined, so this pipeline has no evidence about
revisions of it and makes no claim. [02](02-disc-and-volume.md)

### 9. Nine of the twenty-seven video streams declare a reserved aspect code

**Measured.** Nine `.SFD` sequence headers set the bit-rate field to all ones
(the MPEG convention for variable) and the aspect-ratio code to **12**, which is
reserved in MPEG-2. All three 640×480 streams are among them, including
`OP.SFD`.

**Open.** Whether CRI's encoder writes 12 deliberately, whether the decoder
ignores it, or whether this is one setting used on nine files. Reported as
measured rather than repaired. [07](07-media-and-budget.md)

### 10. What are the twenty-seven header-less block runs indexed by?

**Measured.** Twenty-seven members — the `.PKF` field packs and four `.BIN`
battle files — are flat sequences of sector-aligned nine-byte blocks with no
directory of their own. `F3.PKF` holds 4,634 of them, `F0.PKF` 292. A walk from
the first block reaches the end of the member exactly in all twenty-seven.

**Open.** What tells the game which block is which. The block boundaries are
recoverable by walking, but a game does not walk 4,634 blocks to reach one; the
index must be somewhere, and it was not located. The likeliest place is one of
the battle or field overlays. [03](03-containers.md), [05](05-block-codec.md)

### 11. ~~Why did the ring-clear loop get unrolled?~~ *Answered: the compiler did it.*

**Measured.** Four PlayStation 2 builds clear the ring inline, and they split
cleanly by compiler stamp rather than by source:

| Build | `.comment` | Clear loop | Bound |
|---|---|---|---|
| *Destiny 2*, 2002 | **none** | one `sb` per iteration | **4078** |
| *Symphonia* 2004, 2nd pair | `MW MIPS C Compiler (2.4.1.01)` | **eight `sb` per iteration** | 4071 / 4070 |
| *Legendia*, 2005 | `MW MIPS C Compiler (2.4.1.01)` | **eight `sb` per iteration** | 4070 |
| ***Abyss*, 2005** | `MW MIPS C Compiler (2.4.1.01)` | **eight `sb` per iteration** | 4071 / 4070 |

The decisive row is *Legendia*'s. Its decoder shares 18 bytes with this one and
21 with *Symphonia*'s — the corpus's own noise floor — so it is **not** the same
source, and it unrolls the same loop the same way anyway. Two unrelated sources
compiled by the same stamped compiler both produce an eight-way unroll of a
byte-clear loop; the one build with no compiler string does not.

**So 4070 and 4071 are compiler artefacts, not packer constants.** They are
still worth scanning for — they put the hit at the top of the routine instead of
135 words in — but they identify the *toolchain*, and 4078/4079 remain the only
constants that identify the format. The corpus's section 7 should say that.
[05](05-block-codec.md)

The narrower part is still open: the two 256-iteration **preload** loops are
unrolled by eight in every build back to 1997, including on PowerPC in 2003,
which the corpus attributes to the source. If the ring clear's unroll is the
compiler's and the preload's is the source's, then one file contains both kinds
of eight and only disassembly tells them apart.

### 12. Which team built this game

**Open, and outside what this method can support.** A disc records paths, tags,
compilers and middleware. `C:\TO7\prog\`, `MW MIPS C Compiler (2.4.1.01)`,
RenderWare, CRI and Visual SourceSafe are all on it. None of that names an
organisation, and the credit roll in `TOAEND_JP.TXT` names people rather than
the structure this pipeline is asking about. [04](04-executables.md)

---

## Things that were open and are now closed

* **~~Does the codec source line survive past 2004?~~** *Yes.* 69 bytes and 17
  identical words against *Symphonia*'s unedited pair, with a 632-byte C-runtime
  control between the same files and a 14-byte floor from an executable that
  contains no decoder. [06](06-decoder-lineage.md)
* **~~Did *Legendia*'s envelope get adopted?~~** *No.* `CPS ` and `CPS\0` return
  seven hits in 4.36 GB against a chance rate of about one each; every one was
  located and is inside stream payload. The nine-byte header with its method
  byte is back, complete, with methods 0/1/3 used directly. [05](05-block-codec.md)
* **~~Is there a third dialect?~~** *No.* 47,513 of 47,513 blocks decode under
  the unmodified reference decoder. [05](05-block-codec.md)
* **~~Is the disc clean of other titles?~~** *No.* 109 sound effects carry
  *Rebirth*'s prefix and all 105 of their distinct names are present on
  *Rebirth*'s own disc. [08](08-cross-title.md)
