# 05 — The block codec on this disc

Reproduce with:

```
python tools/ring_sites.py SLPS_255.86 --mips --imm 4078,4079,4080 \
       --base 0x00100000 --off 0x100 --size 0x4d9900
python tools/ring_sites.py SLPS_255.86 --mips --imm 4070,4071 ...
python tools/dismips.py SLPS_255.86 --va 0x00122150 44
python tools/codec_census.py FILEDIR
python tools/preload_test.py FILEDIR
```

Output: [`reports/ring-sites.txt`](../reports/ring-sites.txt),
[`reports/decoder-listing.txt`](../reports/decoder-listing.txt),
[`reports/codec-census.txt`](../reports/codec-census.txt),
[`reports/preload-test.txt`](../reports/preload-test.txt).

---

## The shortcut, run first, as section 7 now says to

Section 7 of the specification was rewritten after *Legendia*, whose header scan
returned zero while the decoder sat in plain sight. The order it prescribes is:
scan the executable for `4078`, `4079` and `4080`; disassemble the hit before
sweeping any data; only then look for the envelope. That order was followed
here and it answered in about a minute.

Six sites in `SLPS_255.86`, across 1,271,360 instruction words:

```
0x0011B204   addiu  a0, sp, 4080     4080   a stack local, not a constant
0x00122458   addiu  v1, zero, 4079   4079   <-- the method-3 decoder
0x001227CC   addiu  v1, zero, 4078   4078   <-- the method-1 decoder
0x001B569C   andi   a0, a0, 0x0FF0   4080   a bit mask
0x001DA7E0   addiu  sp, sp, 4080     4080   a function epilogue
0x0028E448   daddiu s0, s0, 4079     4079   page rounding in an allocator
```

**All six were read, not four of them.** The last is the same idiom Legendia
carried at `0x00107B90` — `daddiu 4079`, `daddiu -1`, `slti 4096` — and it was
innocent there too. The three `4080` hits are an address, a mask and a stack
adjustment; none is the constant.

On the five I/O processor images the answer is a clean negative:
`IOPRP300.IMG`, `CEI.IRX`, `PFM.IRX` and `SDM.IRX` have **no 4078, 4079 or 4080
anywhere**, and `IRXARC.BIN` has two `4080`s, one written as a hardware register
value next to a `4092` and one in a buffer-size argument list. So **the codec
runs on the Emotion Engine only**, as it did on *Symphonia*'s PlayStation 2 port
and unlike *Destiny 2* (2002) and *Rebirth* (2004), which both put a copy on the
I/O processor.

### One thing the shortcut nearly missed, and what to do about it

Both hits are the **cursor**, at +139 and +135 words into their routines. The
dictionary *clear* on this disc is bounded by **4071** and **4070**, because it
is an inline byte loop unrolled by eight with a seven-byte tail — eight-at-a-time
up to 4,071 or 4,070, then seven singles, clearing 4,079 and 4,078 bytes.

The published shortcut still finds the routine, because the cursor is inside it.
But section 7 also says *"disassemble the hit"* and *"forty instructions is
enough to read off the ring base, the mask, the initial cursor and the token
shape"* — and forty instructions around `0x00122458` lands **past the whole
dictionary setup**, in the middle of the token loop. Adding `--imm 4070,4071` as
a second pass costs one command and puts the hit at +11 and +10 words, at the
top of the routine:

```
0x00122258   slti  v1, t1, 4071   0x0012222C (+11 words)
0x001225D8   slti  v1, t1, 4070   0x001225B0 (+10 words)
```

and the two immediates also say *which mechanism* directly, without counting
`sb`s: a build that clears the ring with a plain byte loop has 4078 as the loop
bound, a build that unrolls it by eight has 4071 or 4070. That distinction is
worth having, because it is the difference between *Destiny 2*'s copy and this
one. See [99](99-open-questions.md).

---

## The machine

1,896 contiguous bytes at `0x00122150`, in four pieces.

```
0x00122150 .. 0x001221FC   176 bytes   the dispatcher
0x00122200 .. 0x00122228    44 bytes   the unpacked-size getter
0x00122230 .. 0x001225AC   896 bytes   method 3: LZSS + run escape
0x001225B0 .. 0x001228B4   776 bytes   method 1: LZSS
```

### The nine-byte header is back

```
0x00122150  addiu sp, sp, -4144      ; 16 + a 4,096-byte ring + pad
0x00122154  addiu v0, zero, 3
0x0012215C  lbu   t1, 2(a1)          ; the packed size, one byte at a time
0x00122160  lbu   a3, 3(a1)
0x00122164  lbu   a2, 4(a1)
0x00122168  lbu   t0, 1(a1)
0x0012216C  lbu   v1, 0(a1)          ; the method byte
...
0x00122184  beq   v1, v0, ...        ; method 3
0x00122190  beq   v1, v0, ...        ; method 1
0x00122198  beq   v1, zero, ...      ; method 0, stored
0x001221A4  addiu v0, zero, -1       ; anything else: error
```

This is section 1 of the specification, unchanged and complete: `+0` method,
`+1` packed size assembled from four `lbu`s, `+5` unpacked size read by a
separate 44-byte getter that nothing on the compressed paths calls. Method bytes
**0, 1 and 3 used directly** — not the internal kinds 2 and 4 that *Destiny 2*'s
I/O processor copy and both of *Rebirth*'s copies dispatch on.

*Legendia*'s sixteen-byte `CPS` envelope, four months earlier, is not on this
disc anywhere. The reversion is total.

### The stored path is the fixed one

```
0x001221A8  jal   0x0028FF18         ; the SDK's quadword memcpy
0x001221AC  addiu a1, a1, 9          ; source = block + 9
```

Source past the header, count from `+1` (the packed size). That is the 2000 and
2002 behaviour, not the 1997 defect. Nothing on this disc exercises it —
**zero method-0 blocks in 47,513** — so the path is right and unused, exactly as
in 1997, for the opposite reason.

### The ring is rebuilt on the stack on every call

`addiu a3, sp, 16` in the dispatcher, and the decoders take it in `a3`. A
4,144-byte stack frame per call, of which 4,096 is the dictionary. This is what
the specification describes for every PlayStation-family build from 1997 to
2004 — and *not* what *Legendia* does, which keeps its state in five
`gp`-relative globals so the routine can be resumed.

### The dictionary is cleared inline, unrolled by eight

```
0x00122248  addu  t0, a3, t1
0x0012224C  sb    zero, 0(t0)
0x00122250  addiu t1, t1, 8
0x00122254  sb    zero, 1(t0)
0x00122258  slti  v1, t1, 4071
0x0012225C  sb    zero, 2(t0)
   ... 3..7 ...
0x00122270  bne   v1, zero, 0x00122248
0x00122274  sb    zero, 7(t0)
   then seven single stores for the tail
```

4,079 bytes for method 3, 4,078 for method 1 — `RING − 17` and `RING − 18`, the
two cursors. So the count is now five PlayStation 2 builds and five ways to
clear one array:

| Build | Year | Mechanism | Constant |
|---|---|---|---|
| *Destiny 2* | 2002 | inline byte loop | 4078 |
| *Symphonia* PS2, first pair | 2004 | bespoke quadword `bzero` | **4080** |
| *Rebirth* | 2004 | library `memset` from a factored `ring_init` | **4079** |
| *Legendia* | 2005 | inline byte loop, no preload | 4078 |
| ***Abyss*** | **2005** | **inline byte loop unrolled by eight** | **4078 / 4079** |

and Abyss's is the same mechanism as *Symphonia*'s **second** pair, which is
where section [06](06-decoder-lineage.md) starts.

### The synthetic preload is here, both halves

Immediately after the clear, two 256-iteration loops, both unrolled by eight:

```
0x001222D0  addu  v1, a3, t7        ; (i, 0x00) pairs, ring[0x0000..0x07FF]
0x001222D4  sb    t0, 0(v1)
0x001222D8  sb    zero, 1(v1)
   ... eight bytes per iteration, i incrementing to 256

0x0012230C  addu  t0, a3, t7        ; (i, 0xFF) pairs, ring[0x0800..0x0EFF]
0x00122314  sb    t6, 0(t0)         ; t5 = 255, held in a register
0x0012231C  sb    t5, 1(t0)
   ... seven bytes per i, eight values of i per iteration
```

2,048 + 1,792 = **3,840 bytes of synthetic dictionary**, exactly as section 4
describes. *Legendia*'s `ring_init` clears 4,078 bytes and returns; this one does
not.

### Everything else is unchanged

| Fingerprint | Here |
|---|---|
| ring size | 4,096, on the stack |
| mask | `andi v1, v1, 0x0FFF` |
| control refill | `lbu` then `ori t0, t0, 0xFF00` |
| control bits | LSB first, `1` = literal |
| reference | `b0 \| ((b1 & 0xF0) << 4)` — top nibble in the **high** nibble |
| length | `(b1 & 0x0F) + 3`, 3 to 18 |
| run escape (method 3) | `n + 3` for 4–18, `b0 + 19` for 19–274 |
| loop bound | the packed size, `sltu at, a1, a2` |

The `+19` is there, at `0x00122540`: `addiu t4, t4, 18` and a loop that runs
`t4 + 1` times. Section 3 of the specification calls that constant the single
strongest evidence that this is one format and not two convergent designs. It is
in a 2005 build, on a fifth machine generation, ten years after the Super
Famicom cartridge whose `MVN` instruction is the reason it is 19 and not 21.

---

## The census

`tales_block.py` is the corpus copy — md5 `e2dcd6b8dc717b84f67bf8a46568298c`,
byte-identical to `tales-blockcodec-doc`'s and to *Legendia*'s and *Rebirth*'s —
and it needed no edit in either direction.

```
blocks found                 47513
decode to their declared len 47513
do not                       0

method 0 (stored)            0
method 1 (LZSS)              46358
method 3 (LZSS + run escape) 1155

packed bytes                 1069278379
unpacked bytes               2643327828
ratio                        2.472x
smallest packed              173
largest packed               2307879
largest unpacked             5115328
blocks where packed >= unpacked  0
```

**47,513 of 47,513.** 1.07 GB in, 2.64 GB out, 24.5% of the disc.

Where they are:

| Volume | Blocks | Packed bytes |
|---|---:|---:|
| `TO7FIELD` | 46,348 | 488,008,888 |
| `TO7MAP` | 594 | 459,730,429 |
| `TO7SE` | 538 | 110,196,939 |
| `TO7BTL` | 32 | 11,317,586 |
| `TO7ROOT` | 1 | 24,537 |
| `TO7NPC`, `TO7EV`, `TO7MOV`, `TO7BGM` | **0** | 0 |

Four of the nine volumes contain no compressed block at all: the NPC model
archives, the voice, the video and the music are stored.

### What the packer did here

* **No stored blocks.** Zero method 0 in 47,513, as on *Rebirth* (zero in 2,851)
  and unlike 2000 (969) and *Legendia* (3,353 raw members).
* **Nothing expands.** Zero blocks with `packed ≥ unpacked`, which now holds on
  every disc examined.
* **The run escape is a per-container setting, and here it is almost total.**
  All 46,345 blocks inside a flat run are method 1, without exception. Of the
  1,168 standalone members, 1,155 are method 3 and 13 are method 1. So the
  escape is on for members and off for runs, and the thirteen exceptions are the
  only blocks on the disc that go the other way � the same shape as the 2000
  disc, where six blocks out of 14,200 in one archive disagreed with their
  neighbours.
* **The ceiling came down.** The largest block is 2,307,879 packed producing
  4,529,600 — against *Legendia*'s 3,864,151 producing 6,162,880 and the
  GameCube's 1,007,213. The smallest is **173 packed bytes**, smaller than
  *Rebirth*'s 59-byte floor is large, and it is method 1: the packer still
  declines to store.

### And the preload is used

The decoder writes 3,840 synthetic bytes; the question is whether the packer put
anything there to find. Decoding a random sample twice, once with the ring as
published and once cleared to zeros:

| Sample | Byte-identical | Different | Different **length** |
|---|---:|---:|---:|
| seed 7, 40 members | 6 | 34 | **0** |
| seed 11, 40 members | 5 | 35 | **0** |
| seed 23, 40 members | 4 | 36 | **0** |

105 of 120 members decode to different bytes without the synthetic dictionary,
and **not one decodes to a different length**. That is section 7's warning
demonstrated rather than quoted: a wrong ring sails through every length check
this pipeline could run, and 47,513 of 47,513 would still have said 47,513.
