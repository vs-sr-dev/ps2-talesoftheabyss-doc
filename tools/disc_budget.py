"""How the 4,357,816,320 bytes were spent, by content rather than by file.

A file listing says `TO7EV.CVM` is 1.07 GB.  That is not the same question as
"how much of this disc is voice", because the volume mixes seventeen `AFS`
archives of speech with compressed field data and a scene index.  So this walks
every member of every volume, opens the `AFS` and `FPS3`/`FPS2` archives inside
them, classifies each leaf by its own first bytes, and adds up bytes per class.

Members are counted at their *stored* size, because that is what they cost the
disc.  A compressed member costs what it occupies, not what it expands to; the
unpacked total belongs to the codec census, not to the budget.

Two lines are judgement calls and are kept separate rather than folded in.
Container overhead -- the `CVM` headers, the ISO 9660 directories, the `AFS`
extent tables and the gaps between sector-aligned members -- is reported as
`container/slack` rather than charged to whatever it sits next to.  And the six
files outside the volumes (the executable, the four I/O processor images and
`SYSTEM.CNF`) get their own line.

    python tools/disc_budget.py IMAGE.iso FILEDIR
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fps
import iso9660
from codec_census import afs_members, leaves as codec_leaves
from cvm import CVM
from cvm_census import sniff

VOLUMES = ['TO7ROOT', 'TO7FIELD', 'TO7MAP', 'TO7BTL', 'TO7NPC',
           'TO7EV', 'TO7MOV', 'TO7BGM', 'TO7SE']

# Which class each magic belongs to, for the five-line summary the sibling
# pipelines report.  Anything not named here is `other data`.
GROUP = {
    'MPEG-PS (Sofdec)': 'video',
    'AHX': 'voice',
    'ADX': 'audio (ADX)',
    'codec block': 'compressed game data',
    'CPS': 'compressed game data',
    'TIM2': 'texture',
}


# The leaf walker is codec_census's, so the two reports cannot disagree about
# what a member is.  It opens AFS and FPS3/FPS2 archives and it splits a member
# that is a flat run of sector-aligned blocks into its blocks, which is what
# moves 545 MB of field data out of `other game data` and into `compressed`.
def leaves(d, path, depth=0):
    for p, buf in codec_leaves(d, path, depth):
        yield (p, sniff(buf[:32], len(buf)), len(buf))


def main(argv):
    if len(argv) < 3:
        raise SystemExit(__doc__)
    image, d = argv[1], argv[2]
    total = os.path.getsize(image)
    img = iso9660.Image(image)
    files = [(e.path, e.size) for e in img.walk() if not e.is_dir]
    named = sum(s for _, s in files)

    kinds, groups = {}, {}
    accounted = 0
    for v in VOLUMES:
        p = os.path.join(d, v + '.CVM')
        c = CVM(p)
        for e in c.walk():
            if e.is_dir:
                continue
            c.f.seek(c.base + e.lba * 2048)
            buf = c.f.read(e.size)
            for path, kind, n in leaves(buf, '%s:/%s' % (v, e.path)):
                kinds[kind] = kinds.get(kind, 0) + n
                g = GROUP.get(kind, 'other game data')
                groups[g] = groups.get(g, 0) + n
                accounted += n

    outside = sum(s for n, s in files if not n.endswith('.CVM'))
    volumes = sum(s for n, s in files if n.endswith('.CVM'))
    slack = total - outside - volumes
    inner_slack = volumes - accounted

    print('IMAGE                    %14d bytes' % total)
    print('  named files            %14d   %.2f%%' % (named, 100 * named / total))
    print('  outside the volumes    %14d   %.2f%%'
          % (outside, 100 * outside / total))
    print('  the nine CVM volumes   %14d   %.2f%%'
          % (volumes, 100 * volumes / total))
    print('  image slack            %14d   %.4f%%'
          % (slack, 100 * slack / total))
    print()
    print('INSIDE THE VOLUMES')
    print('  payload accounted for  %14d   %.2f%% of the image'
          % (accounted, 100 * accounted / total))
    print('  container/slack        %14d   %.2f%%'
          % (inner_slack, 100 * inner_slack / total))
    print()
    print('%-24s %14s %8s' % ('BY CLASS', 'BYTES', 'OF IMAGE'))
    for k in sorted(kinds, key=lambda x: -kinds[x]):
        print('  %-22s %14d %7.2f%%' % (k, kinds[k], 100 * kinds[k] / total))
    print()
    print('%-24s %14s %8s' % ('GROUPED', 'BYTES', 'OF IMAGE'))
    for g in sorted(groups, key=lambda x: -groups[x]):
        print('  %-22s %14d %7.2f%%' % (g, groups[g], 100 * groups[g] / total))
    media = sum(groups.get(x, 0) for x in ('video', 'voice', 'audio (ADX)'))
    print()
    print('  video + voice          %14d %7.2f%%'
          % (groups.get('video', 0) + groups.get('voice', 0),
             100 * (groups.get('video', 0) + groups.get('voice', 0)) / total))
    print('  all media              %14d %7.2f%%' % (media, 100 * media / total))


if __name__ == '__main__':
    main(sys.argv)
