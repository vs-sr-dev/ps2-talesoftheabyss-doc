"""What the audio and video on this disc actually are, read from the streams.

Three CRI formats ship here, and the disc is the first in this corpus to use
all three in bulk:

  Sofdec  an MPEG-2 program stream with CRI's multiplex, named `.SFD`
  ADX     CRI's ADPCM -- music, ambience, sound effects and battle voice
  AHX     CRI's MPEG-2 layer II voice codec, named `.ahx`, one per line

Classification is by magic and every number is arithmetic on a header rather
than an estimate.  ADX and AHX both begin `80 00` followed by a big-endian
offset to the data and a codec byte at +4, so the two are told apart by that
byte and not by the file name -- which matters, because the `AFS` directories
here name a voice line `SCE_001_001_A.ahx` and a music cue `TOA_SFXBGM_D002.ADX`
and both would answer to a name-based census, while a third of the `.adx` in
`SE.AFS` are neither music nor voice.

Playing time comes from the ADX header's own total-sample count divided by its
own sample rate.  For AHX the sample count field is zero -- CRI leaves it so on
that codec -- so AHX duration is derived from the MPEG frame count instead, and
is reported separately rather than added to the ADX total, because the two are
measured different ways.

Video figures come from the MPEG sequence header: width and height are its
twelve-bit fields, the frame rate its four-bit code, the bit rate its
eighteen-bit field times 400.

    python tools/media_census.py FILEDIR
    python tools/media_census.py FILEDIR --voice     # the cast table
"""

import collections
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from codec_census import afs_members
from cvm import CVM

SECTOR = 2048
VOLUMES = ['TO7ROOT', 'TO7FIELD', 'TO7MAP', 'TO7BTL', 'TO7NPC',
           'TO7EV', 'TO7MOV', 'TO7BGM', 'TO7SE']
SEQ = b'\x00\x00\x01\xb3'
RATE = {1: '23.976', 2: '24', 3: '25', 4: '29.97', 5: '30',
        6: '50', 7: '59.94', 8: '60'}
ASPECT = {1: 'square', 2: '4:3', 3: '16:9', 4: '2.21:1'}


def cri_header(h):
    """(kind, channels, rate, samples, dataoff) for an ADX or AHX header."""
    if len(h) < 20 or h[:2] != b'\x80\x00':
        return None
    dataoff = struct.unpack_from('>H', h, 2)[0]
    codec = h[4]
    chans = h[7]
    srate = struct.unpack_from('>I', h, 8)[0]
    samples = struct.unpack_from('>I', h, 12)[0]
    if codec in (2, 3):
        if not (1 <= chans <= 8) or not (4000 <= srate <= 96000):
            return None
        return ('ADX', chans, srate, samples, dataoff)
    if codec in (0x10, 0x11):
        return ('AHX', chans or 1, srate, samples, dataoff)
    return None


# MPEG-2 LSF layer II, the only frame header any AHX on this disc carries.
BR_LSF = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]
SR_LSF = [22050, 24000, 16000]


def mpeg_frame(f):
    """(bitrate, sample rate, samples per frame, frame bytes) or None."""
    if len(f) < 4 or f[0] != 0xFF or (f[1] & 0xE0) != 0xE0:
        return None
    ver = (f[1] >> 3) & 3          # 2 = MPEG-2 LSF, 3 = MPEG-1
    layer = (f[1] >> 1) & 3        # 2 = layer II
    if ver != 2 or layer != 2:
        return None
    br = BR_LSF[(f[2] >> 4) & 0xF] * 1000
    sr = SR_LSF[(f[2] >> 2) & 3]
    pad = (f[2] >> 1) & 1
    if not br:
        return None
    return br, sr, 1152, 144 * br // sr + pad


def sequence(buf):
    """(w, h, aspect, frame rate, bit rate) from the first sequence header."""
    j = buf.find(SEQ)
    if j < 0 or j + 12 > len(buf):
        return None
    b = buf[j + 4:j + 12]
    w = (b[0] << 4) | (b[1] >> 4)
    h = ((b[1] & 0x0F) << 8) | b[2]
    aspect = b[3] >> 4
    rate = b[3] & 0x0F
    bitrate = ((b[4] << 10) | (b[5] << 2) | (b[6] >> 6)) * 400
    return w, h, ASPECT.get(aspect, str(aspect)), RATE.get(rate, str(rate)), bitrate


def streams(d):
    """(volume, path, kind, size, info) for every audio/video stream."""
    for v in VOLUMES:
        c = CVM(os.path.join(d, v + '.CVM'))
        for e in c.walk():
            if e.is_dir:
                continue
            c.f.seek(c.base + e.lba * SECTOR)
            head = c.f.read(4096)
            if head[:4] == b'AFS\x00':
                c.f.seek(c.base + e.lba * SECTOR)
                blob = c.f.read(e.size)
                for i, name, o, s in afs_members(blob):
                    hh = cri_header(blob[o:o + 20])
                    if hh:
                        f0 = blob[o + hh[4] + 4:o + hh[4] + 8]
                        yield (v, '%s/%s' % (e.path, name), hh[0], s, hh, f0)
                continue
            if head[:4] == b'\x00\x00\x01\xba':
                c.f.seek(c.base + e.lba * SECTOR)
                yield (v, e.path, 'SFD', e.size,
                       sequence(c.f.read(1 << 20)), b'')
                continue
            hh = cri_header(head[:20])
            if hh:
                yield (v, e.path, hh[0], e.size, hh,
                       head[hh[4] + 4:hh[4] + 8])


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    d = argv[1]
    rows = list(streams(d))

    sfd = [r for r in rows if r[2] == 'SFD']
    adx = [r for r in rows if r[2] == 'ADX']
    ahx = [r for r in rows if r[2] == 'AHX']

    if '--voice' in argv:
        agg = collections.Counter()
        byt = collections.Counter()
        for v, p, k, s, i, _f in rows:
            base = os.path.basename(p).split('.')[0]
            pre = base.split('_')[0]
            agg[pre] += 1
            byt[pre] += s
        print('%-14s %8s %14s' % ('PREFIX', 'STREAMS', 'BYTES'))
        for pre in sorted(agg, key=lambda x: -byt[x])[:40]:
            print('%-14s %8d %14d' % (pre, agg[pre], byt[pre]))
        return

    print('SOFDEC VIDEO -- %d streams, %d bytes' % (len(sfd), sum(r[3] for r in sfd)))
    shapes = collections.Counter(r[4] for r in sfd if r[4])
    for sh, n in shapes.most_common():
        print('  %d x  %dx%d  %s  %s fps  %d bit/s' % (n, sh[0], sh[1], sh[2], sh[3], sh[4]))
    for v, p, k, s, i, _f in sorted(sfd, key=lambda r: -r[3])[:8]:
        print('  %-9s %-18s %12d  %.1f s at declared rate'
              % (v, p, s, s * 8 / i[4] if i and i[4] else 0))
    print()

    print('ADX -- %d streams, %d bytes' % (len(adx), sum(r[3] for r in adx)))
    secs = sum(r[4][3] / r[4][2] for r in adx if r[4][2])
    ch = collections.Counter(r[4][1] for r in adx)
    sr = collections.Counter(r[4][2] for r in adx)
    print('  channels %s' % dict(ch))
    print('  rates    %s' % dict(sr))
    print('  total playing time %.2f hours (from the headers\' sample counts)'
          % (secs / 3600))
    print()

    print('AHX -- %d streams, %d bytes' % (len(ahx), sum(r[3] for r in ahx)))
    frames = collections.Counter(r[5] for r in ahx)
    print('  distinct first-frame headers %s'
          % {k.hex(' '): v for k, v in frames.most_common(4)})
    secs = 0.0
    for r in ahx:
        fr = mpeg_frame(r[5])
        if fr:
            br, sr2, spf, fb = fr
            secs += ((r[3] - r[4][4] - 4) // fb) * spf / sr2
    print('  MPEG-2 LSF layer II, %d bit/s, %d Hz, mono'
          % (mpeg_frame(list(frames)[0])[0], mpeg_frame(list(frames)[0])[1])
          if frames else '')
    print('  total playing time %.2f hours (from the frame count)' % (secs / 3600))
    print()

    print('%-10s %8s %8s %8s %16s' % ('VOLUME', 'SFD', 'ADX', 'AHX', 'BYTES'))
    for v in VOLUMES:
        sub = [r for r in rows if r[0] == v]
        if not sub:
            continue
        print('%-10s %8d %8d %8d %16d'
              % (v, sum(1 for r in sub if r[2] == 'SFD'),
                 sum(1 for r in sub if r[2] == 'ADX'),
                 sum(1 for r in sub if r[2] == 'AHX'),
                 sum(r[3] for r in sub)))


if __name__ == '__main__':
    main(sys.argv)
