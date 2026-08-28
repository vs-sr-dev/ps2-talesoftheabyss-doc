# 06 — Decoder lineage

Reproduce with:

```
python tools/prefix_scan.py SLPS_255.86 0x00122230 872 SLPS_254.00 SLPS_255.33 \
       SLPS_254.50 SLPS_251.72 VENUS.ELF SLPS_030.50 SLPS_011.00
python tools/prefix_scan.py SLPS_255.86 0x0028FF18 872 <the same targets>
python tools/decoder_lineage.py SLPS_255.86 0x00122248 SLPS_254.00 0x00242C80 200
python tools/decoder_lineage.py SLPS_255.86 0x00122150 SLPS_254.00 0x00242B70 44
```

Output: [`reports/decoder-prefix.txt`](../reports/decoder-prefix.txt).

---

## The question this disc was opened to answer

*Tales of Legendia*, four months earlier, produced the corpus's most awkward
result. It had the format complete and the source not at all: 872 bytes of its
decoder scored **21** bytes against *Symphonia*'s PlayStation 2 port and **20**
against *Rebirth*'s, while an executable containing no decoder at all — the
corpus's `VENUS.ELF` control — scored **20**. And 2,420 contiguous bytes of C
runtime were identical between the same pair of files. So the codec had crossed
into that build as a specification and not as a file.

That left a question with three possible answers, all of them strong, and the
honest thing was not to pick one in advance:

* Abyss shares bytes with *Symphonia* or *Rebirth* → **the line of code is
  alive, and Legendia was the deviation.**
* Abyss shares with nobody → **every title has its own copy, and propagation is
  always by specification.**
* Abyss shares with *Legendia* → the least expected, and the most informative.

**It is the first.** And the second half of the answer — which of *Symphonia*'s
two unrelated decoders it descends from — is sharper than the first half.

---

## The measurement

872 bytes of Abyss's method-3 decoder, from `0x00122230`, searched at any
alignment through whole executables without telling the tool where to look.
The needle length is Legendia's, so the two results sit on the same scale.

| Abyss's **decoder** against | CPU | Longest identical run |
|---|---|---:|
| ***Symphonia*, PlayStation 2, 2004** | R5900 | **69 bytes** |
| *Legendia*, PlayStation 2, 2005 | R5900 | 18 bytes |
| *Rebirth*, PlayStation 2, 2004 | R5900 | 14 bytes |
| *Destiny 2*, PlayStation 2, 2002 | R5900 | 12 bytes |
| ***Venus & Braves*, 2003 — the negative control** | **R5900** | **14 bytes** |
| *Eternia*, PlayStation, 2000 | R3000A | 11 bytes |
| *Destiny*, PlayStation, 1997 | R3000A | 10 bytes |

The `VENUS.ELF` row is what makes the rest readable and it costs one extra
argument. It is 933,840 instruction words with no `4078` immediate anywhere, no
zero loop, no ×8 pattern fill — **no decoder at all** — and it scores 14. So 14
is the floor, 18 for Legendia is the floor, and **69 is five times the floor**.

Widening the needle to the whole 1,896-byte codec region does not move the
number: 69 against *Symphonia*, and the run sits at needle+248 either way. 69
bytes is what there is.

## The control that makes it a measurement

A byte result is worth much more if you can show byte equality was available.
872 bytes of Abyss's **own C runtime** — the Emotion Engine SDK's quadword
`memcpy` at `0x0028FF18`, which is the routine this build's own stored path
calls — same length, same tool, same targets:

| Abyss's **C runtime** against | Longest identical run |
|---|---:|
| *Symphonia*, PlayStation 2, 2004 | **632 bytes** |
| *Legendia*, PlayStation 2, 2005 | **632 bytes** |
| *Venus & Braves*, 2003 | 436 bytes |
| *Destiny 2*, PlayStation 2, 2002 | 164 bytes |
| *Rebirth*, PlayStation 2, 2004 | 136 bytes |
| *Eternia*, PlayStation, 2000 | 11 bytes |
| *Destiny*, PlayStation, 1997 | 11 bytes |

Widening the needle to 2 KB and 8 KB returns 632 every time: the run is the
whole `memcpy` object and it stops where the next object begins.

So the two-line summary is:

> Abyss and *Legendia* share **632 bytes** of C runtime and **18 bytes** of
> decoder. Abyss and *Symphonia* share **632 bytes** of C runtime and **69
> bytes** of decoder.

Same toolchain — all three executables were built by the same compiler, and this
one stamps it: `SLPS_255.86` carries a `.comment` reading `MW MIPS C Compiler
(2.4.1.01)`, exactly as `SLPS_254.00` and `SLPS_255.33` do. Byte equality was
equally available against both. Only one of them gave it.

---

## Which of *Symphonia*'s two decoders

*Tales of Symphonia*'s PlayStation 2 port carries the codec **four times**, in
two unrelated pairs, and the fact that they are unrelated is already in the
corpus: `gc-talesofsymphonia-doc` reports 2 identical words out of 276 between
them.

| Symphonia's copy | Dictionary clear | Length | Abyss's 872-byte needle scores |
|---|---|---:|---:|
| `0x001C93D0` + `0x001C9820` | quadword `bzero`, **4080** | 1,104 + 768 | **4 bytes** |
| `0x00242C5C` + `0x0024324C` | inline byte loop ×8, **4078/4079** | 1,520 + 1,176 | **69 bytes** |

The 4080 pair is the one the corpus made its 2004 headline out of — "somebody
edited the decoder's source for this CPU". Abyss has nothing to do with it: one
identical word in two hundred, a four-byte run, which is noise.

Abyss descends from **the other one** — the copy in that same executable that
was *not* edited, that still clears the ring with the 1997 inline loop, still
writes the synthetic preload, and still dispatches on the nine-byte header's
method byte.

Aligned on the dictionary-clear loop (`0x00122248` against `0x00242C80`), over
200 words:

```
identical words         31 (15.5%)
longest identical run   17 words / 68 bytes
same opcode            113 (56.5%)
```

and the divergence, where it starts, is register allocation and nothing else:

```
Abyss   0x00122288  sb    zero, 0(v1)      Symphonia  0x00242CC0  sb    zero, 0(v1)
Abyss   0x0012228C  daddu t7, zero, zero   Symphonia  0x00242CC4  daddu t4, zero, zero
```

`t7` against `t4`, and the 69-byte run ends on the first byte of that word
because both encode `daddu rX, zero, zero` and both begin `2d`.

For scale, the corpus's own reference points on this measure:

| Pair | Identical words | Longest run |
|---|---:|---:|
| *Destiny* 1997 ↔ *Eternia* 2000 — the same object | 69 / 140 | **212 bytes** |
| ***Abyss* 2005 ↔ *Symphonia* 2004, second pair** | **31 / 200** | **68 bytes** |
| *Destiny 2* 2002 ↔ *Symphonia* 2004, first pair | 1 / 180 | 6 bytes |
| *Legendia* 2005 ↔ *Symphonia* 2004 | — | 21 bytes |

Abyss sits between "the same compiled object" and "nothing at all", which is
where a **recompile of the same source** sits.

## And the dispatcher says it twice

The 176-byte routine that reads the nine-byte header is the same routine in both
builds, and it is worth putting side by side because almost every word in it is
address-dependent — `jal` targets and branch offsets cannot match — and it still
scores 10 identical words in 44:

```
Abyss  0x00122150  addiu sp, sp, -4144    Symphonia  0x00242B70  addiu sp, sp, -4144
       0x00122154  addiu v0, zero, 3                 0x00242B74  addiu v0, zero, 2
       0x00122158  sd    ra, 0(sp)                   0x00242B78  sd    ra, 0(sp)
       0x0012215C  lbu   t1, 2(a1)                   0x00242B7C  lbu   t0, 2(a1)
       0x00122160  lbu   a3, 3(a1)                   0x00242B80  lbu   a3, 3(a1)
       0x00122164  lbu   a2, 4(a1)                   0x00242B84  lbu   a2, 4(a1)
       0x00122168  lbu   t0, 1(a1)                   0x00242B88  lbu   t1, 1(a1)
       0x0012216C  lbu   v1, 0(a1)                   0x00242B8C  lbu   v1, 0(a1)
       0x00122170  sll   t1, t1, 8                   0x00242B90  sll   t0, t0, 8
       0x00122174  sll   a3, a3, 16                  0x00242B94  sll   a3, a3, 16
       0x00122178  sll   a2, a2, 24                  0x00242B98  sll   a2, a2, 24
```

The same 4,144-byte stack frame, the same five `lbu`s in nearly the same order,
the ring placed at `sp + 16` in both. Two differences of substance:

* **Symphonia's dispatcher has a case for method 2** and Abyss's does not.
  Symphonia tests 2, 3, 1, 0 and routes 2 to the same target as the fallthrough;
  Abyss tests 3, 1, 0 and falls through to `addiu v0, zero, -1`. Method 2 has
  never appeared in any block on any disc in this corpus.
* **Symphonia inlines the stored copy** as a byte loop; Abyss calls the SDK's
  quadword `memcpy` at `0x0028FF18`. Both advance the source past `+9` first, so
  both are the fixed version of the 1997 defect described in section 5 of the
  specification.

---

## What this changes

The corpus's boundary statement after *Legendia* was that the codebase
propagated the codec **as knowledge rather than as a file** — because the one
build that plainly inherited had inherited no code. That statement was built on
a single observation and it now has to be narrowed rather than repeated.

Abyss inherited code. Fifteen months and one *Legendia* later, the routine is
still being recompiled from a source file that *Symphonia*'s port also compiled,
and it is being recompiled from the **unedited** copy in that file rather than
from the 4080 variant that the 2004 build made its own.

So the picture at the end of ten builds is not one line, and not one copy per
title either. It is:

* a **1997 source** that reaches 2005 intact, via *Symphonia*'s second pair and
  then Abyss — inline clear, synthetic preload, nine-byte header, methods 0/1/3;
* at least **three edits of it** that went nowhere: *Symphonia*'s own 4080
  quadword `bzero` (2004), *Rebirth*'s 4079 library `memset` (2004), and
  *Legendia*'s resumable state machine with the `CPS` envelope (2005);
* and a **format** that all of them agree on to the bit.

*Legendia* is not the rule. It is one of at least three forks that did not
propagate, and it is the only one of the three that was written from a
description rather than from the file. What the corpus can now say is that the
codebase carried **both** — a source file that kept being compiled, and a
specification that could be re-implemented when somebody did not have it.

## What this does not settle

Which of these two things Abyss's team thought they were doing. The
measurements say the source file was on hand and was compiled; they say nothing
about whether that was a decision or an inheritance nobody reviewed. And they
say nothing about *Legendia*'s authors' access — a team can have a file and not
use it. See [99](99-open-questions.md).
