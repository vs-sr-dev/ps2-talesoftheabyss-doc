# Tools

Python 3, standard library only, one file per job. None of them writes to the
image, and none needs an argument beyond a path and sometimes an address.

Where a tool came from another pipeline it is named here, because a negative
result is only worth quoting if the instrument is the one that succeeded
elsewhere.

## Copied without an edit

| | from | md5 |
|---|---|---|
| `tales_block.py` | [tales-blockcodec-doc](https://github.com/vs-sr-dev/tales-blockcodec-doc) | `e2dcd6b8dc717b84f67bf8a46568298c` |
| `iso9660.py`, `ps2elf.py`, `dismips.py`, `sector_map.py` | [ps2-talesofrebirth-doc](https://github.com/vs-sr-dev/ps2-talesofrebirth-doc) via [ps2-talesoflegendia-doc](https://github.com/vs-sr-dev/ps2-talesoflegendia-doc) | |
| `prefix_scan.py` | ps2-talesofrebirth-doc | |
| `decoder_lineage.py` | ps2-talesofrebirth-doc | |
| `ring_sites.py` | ps2-talesoflegendia-doc (its `--imm` flag is used here) | |
| `cvm.py` | [gc-talesofsymphonia-doc](https://github.com/vs-sr-dev/gc-talesofsymphonia-doc) | |

`tales_block.py`'s md5 is checked rather than asserted: it is identical to the
corpus copy, to *Tales of Rebirth*'s and to *Tales of Legendia*'s. It needed no
edit to read this disc, which is the result reported in
[docs/05](../docs/05-block-codec.md).

## Modified

**`leftovers.py`** — from ps2-talesoflegendia-doc, with its `SWEEP` list
rewritten for this disc: *Legendia*'s own markers (`TLPS`, `TLPK`, `CPS `,
`tox`, `ToL`) added as things to look **for**, this disc's own tags (`TO7`,
`TO8`, `FPS2/3/4`, `VSSVER`) added, and the counts printed for every pattern
including the zeroes.

## Written here

| | |
|---|---|
| `cvm_census.py` | every member of every `CVM`, classified from its own bytes, with its date |
| `fps.py` | the `FPS3` and `FPS2` archive headers, and why the `FPS2` count field cannot be trusted |
| `codec_census.py` | decode every block on the disc, opening `AFS`, `FPS3`/`FPS2` and header-less block runs |
| `preload_test.py` | decode a sample twice, with and without the synthetic dictionary |
| `disc_budget.py` | where 4,357,816,320 bytes went, by content rather than by file |
| `media_census.py` | ADX, AHX and Sofdec read from their own headers; AHX duration from the MPEG frame size |
| `locate.py` | turn a raw image offset into "which member, and what is around it" |

## Inherited but not used

`afs.py`, `afs_census.py`, `cps.py`, `binfs.py`, `scpk.py`, `mpeg.py`,
`region_profile.py` and `xarch.py` are **not** in this repository. `cps.py`
reads *Legendia*'s sixteen-byte envelope, which is not on this disc;
`binfs.py`, `scpk.py` and `afs_census.py` read containers this disc does not
use; `xarch.py` implements a cross-instruction-set similarity measure that the
corpus records as having no discriminating power, and this pipeline compares
R5900 with R5900 throughout, so byte equality was available and was used
instead.

## Running them

```
python tools/iso9660.py IMAGE.iso --pvd
python tools/iso9660.py IMAGE.iso --extract FILEDIR
python tools/sector_map.py IMAGE.iso

python tools/ring_sites.py FILEDIR/SLPS_255.86 --mips --imm 4078,4079,4080 \
       --base 0x00100000 --off 0x100 --size 0x4d9900
python tools/ring_sites.py FILEDIR/SLPS_255.86 --mips --imm 4070,4071 \
       --base 0x00100000 --off 0x100 --size 0x4d9900
python tools/dismips.py FILEDIR/SLPS_255.86 --va 0x00122150 44

python tools/prefix_scan.py A.elf 0x00122230 872 B.elf [C.elf ...]
python tools/decoder_lineage.py A.elf 0x00122248 B.elf 0x00242C80 200

python tools/cvm.py FILEDIR/TO7ROOT.CVM --header
python tools/cvm_census.py FILEDIR --kinds
python tools/codec_census.py FILEDIR
python tools/preload_test.py FILEDIR --n 40 --seed 7
python tools/disc_budget.py IMAGE.iso FILEDIR
python tools/media_census.py FILEDIR

python tools/leftovers.py FILEDIR/SLPS_255.86
python tools/leftovers.py IMAGE.iso --sweep
python tools/locate.py IMAGE.iso 0x12B20754
```

`codec_census.py` takes about twenty minutes on this disc; it decodes 1.07 GB of
packed data. The whole-image sweep takes about two and a half minutes.
