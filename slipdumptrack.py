# SlipSpeed track dumper 2020-04-16 <m@thp.io> (req: Pillow, ImageMagick)
# Buy the game or get the shareware here: https://voxel.itch.io/slipspeed/

import glob, os, subprocess, PIL.Image

ts = 16
sz = 128

for fn in glob.glob('ASSETS/TRACKS/*/*/TRACK.DAT'):
    d = open(fn, 'rb').read()

    img = PIL.Image.open(fn.replace('TRACK.DAT', 'TILES.PNG'))

    tiles = [img.crop((x*ts, y*ts, (x+1)*ts, (y+1)*ts))
             for y in range(16) for x in range(16)]

    anim = []
    for i in range(3):
        dst = PIL.Image.new('P', (sz*ts, sz*ts))
        dst.putpalette(img.getpalette())

        for y in range(sz):
            for x in range(sz):
                ch = d[y*sz + x + sz*sz*i]
                if i == 0 or ch != 0xFF:
                    dst.paste(tiles[ch], (ts*x, ts*y))

        outname = f'dump-{fn.replace("/", "-").lower()}-{i}.gif'
        dst.save(outname, transparency=0)
        anim.append(outname)

    subprocess.check_call(['convert', '-delay', '100', '-loop', '0'] +
                          anim + [anim[0].replace('-0.gif', '-anim.gif')])
