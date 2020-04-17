# SlipSpeed track dumper 2020-04-16 <m@thp.io> (req: Pillow, ImageMagick)
# Buy the game or get the shareware here: https://voxel.itch.io/slipspeed/

import glob, os, subprocess, PIL.Image

from sliptiles import CLASSIFICATION

ts = 16
sz = 128

def classify_tile(fn, x, y, idx):
    for name, first, last in CLASSIFICATION:
        if idx >= first and idx <= last:
            return name
    raise ValueError(f'tile {idx} at ({x}, {y}) in {fn}')


for fn in glob.glob('ASSETS/TRACKS/*/*/TRACK.DAT'):
    d = open(fn, 'rb').read()

    img = PIL.Image.open(fn.replace('TRACK.DAT', 'TILES.PNG'))

    tiles = [img.crop((x*ts, y*ts, (x+1)*ts, (y+1)*ts))
             for y in range(16) for x in range(16)]

    anim = []
    for i in range(4):
        dst = PIL.Image.new('P', (sz*ts, sz*ts))
        dst.putpalette(img.getpalette())

        for y in range(sz):
            for x in range(sz):
                if i == 3:
                    # "difference" map between non-wall background and foreground
                    ch = d[y*sz + x + sz*sz*0]
                    ch_fg = d[y*sz + x + sz*sz*1]
                    if classify_tile(fn, x, y, ch) != 'wall':
                        ch = 0  # Can race on this
                        if ch_fg != 0xFF:
                            ch = 6  # Hidden track part
                    else:
                        ch = 1  # Wall -- cannot race on this
                else:
                    ch = d[y*sz + x + sz*sz*i]
                if i == 0 or ch != 0xFF:
                    dst.paste(tiles[ch], (ts*x, ts*y))

        outname = f'dump-{fn.replace("/", "-").lower()}-{i}.gif'
        dst.save(outname, transparency=0)
        anim.append(outname)

    subprocess.check_call(['convert', '-delay', '100', '-loop', '0'] +
                          anim + [anim[0].replace('-0.gif', '-anim.gif')])
