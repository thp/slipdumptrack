# SlipSpeed track tester 2020-04-17 <m@thp.io>
# .. in good old OpenGL 1, celebrating the fixed function pipeline!
# (req: Pillow, ImageMagick, PyGame, PyOpenGL)
# Buy the game or get the shareware here: https://voxel.itch.io/slipspeed/

import glob, os, random, math, time, pygame, PIL.Image

from sliptiles import CLASSIFICATION, FIRST_SHIP_TILE, FIRST_SHIP_SHADOW_TILE, FIRST_CASH_TILE, LAST_CASH_TILE
from pygame.math import Vector2

from pygame.locals import *
from OpenGL.GL import *

ts = 16
sz = 128

def classify_tile(idx):
    for name, first, last in CLASSIFICATION:
        if idx >= first and idx <= last:
            return name
    raise ValueError(idx)

pygame.display.init()

w = 640
h = 480

scr = pygame.display.set_mode((w, h), DOUBLEBUF | OPENGL)

def find_tile_ctrl(d, tile):
    for y in range(sz):
        for x in range(sz):
            if d[y*sz + x + sz*sz*2] == tile:
                return (x, y)

def blitquad(x, y, ch, rotation_deg=0):
    x0 = x * ts
    x1 = x0 + ts
    y0 = y * ts
    y1 = y0 + ts

    xo = (x0 + x1) / 2
    yo = (y0 + y1) / 2

    center = Vector2(xo, yo)
    p0 = Vector2(x0, y0)
    p1 = Vector2(x1, y0)
    p2 = Vector2(x1, y1)
    p3 = Vector2(x0, y1)
    p0 = ((p0 - center).rotate(rotation_deg)) + center
    p1 = ((p1 - center).rotate(rotation_deg)) + center
    p2 = ((p2 - center).rotate(rotation_deg)) + center
    p3 = ((p3 - center).rotate(rotation_deg)) + center

    s = int(ch % 16) * img.width / ts
    t = int(ch / 16) * img.height / ts

    fw = 1 / img.width
    fh = 1 / img.height

    s0 = s * fw
    s1 = (s+ts) * fw
    t0 = 1 - t * fw
    t1 = 1 - (t+ts) * fw

    glTexCoord2f(s0, t0)
    glVertex2f(p0.x, p0.y)

    glTexCoord2f(s1, t0)
    glVertex2f(p1.x, p1.y)

    glTexCoord2f(s1, t1)
    glVertex2f(p2.x, p2.y)

    glTexCoord2f(s0, t1)
    glVertex2f(p3.x, p3.y)

# TODO: Track chooser
fn = random.choice(glob.glob('SLIPSW/ASSETS/TRACKS/*/*/TRACK.DAT'))

d = open(fn, 'rb').read()

def pal0_to_rgba(img):
    newimg = img.convert('RGBA')
    pi = img.load()
    px = newimg.load()
    for y in range(newimg.height):
        for x in range(newimg.width):
            if pi[x, y] == 0:
                px[x, y] = (0, 0, 0, 0)
    del px
    return newimg

img = pal0_to_rgba(PIL.Image.open(fn.replace('TRACK.DAT', 'TILES.PNG')))
data = img.tobytes("raw", "RGBA", 0, -1)
tex = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, tex)
glBindTexture(GL_TEXTURE_2D, tex)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glClearColor(1., 0., 0., 1.)
glEnable(GL_TEXTURE_2D)

def capture_display_list(func):
    # Display lists! remember those?
    def wrapper():
        result = glGenLists(1)
        glNewList(result, GL_COMPILE)
        func()
        glEndList()
        return result
    return wrapper

walls = []

@capture_display_list
def make_bg_list():
    glBegin(GL_QUADS)
    glColor4f(1., 1., 1., 1)
    for y in range(sz):
        for x in range(sz):
            ch = d[y*sz + x]
            if classify_tile(ch) == 'wall':
                walls.append((x, y))
            if ch != 0xff:
                blitquad(x, y, ch)
    glEnd()

bglist = make_bg_list()

cashes = []

@capture_display_list
def make_fg_list():
    glBegin(GL_QUADS)
    glColor4f(1., 1., 1., 1.)
    for y in range(sz):
        for x in range(sz):
            ch = d[y*sz + x + sz*sz]
            if classify_tile(ch) == 'cash':
                cashes.append((x, y, ch))
            elif ch != 0xff:
                blitquad(x, y, ch)
    glEnd()

fglist = make_fg_list()

# Find first tile in the third layer (ships + waypoints)
px, py = find_tile_ctrl(d, FIRST_SHIP_TILE)

ppos = Vector2((px, py)) * ts
steer = 0
rotation = 0
zoomin = 2
speed = 0
maxspeed = 6
accelerate = False
reverse = False
gotcash = 0

def collides_with(ppos, x, y):
    return math.sqrt((x-ppos.x)**2 + (y-ppos.y)**2) < ts

while True:
    while True:
        evt = pygame.event.poll()
        if evt.type == NOEVENT:
            break
        elif evt.type == KEYDOWN:
            if evt.key == K_ESCAPE:
                raise SystemExit(1)
            if evt.key == K_LEFT:
                steer = -3
            elif evt.key == K_RIGHT:
                steer = +3
            elif evt.key == K_UP:
                accelerate = True
            elif evt.key == K_DOWN:
                reverse = True
        elif evt.type == KEYUP:
            if evt.key == K_LEFT or evt.key == K_RIGHT:
                steer = 0
            elif evt.key == K_UP:
                accelerate = False
            elif evt.key == K_DOWN:
                reverse = False

    glClear(GL_COLOR_BUFFER_BIT)

    xo = int(ppos.x + ts/2 - w/2/zoomin)
    yo = int(ppos.y + ts/2 - h/2/zoomin)
    glLoadIdentity()
    glOrtho(xo, xo+int(w/zoomin), yo+int(h/zoomin), yo, 0, 1)

    # Draw background below
    glCallList(bglist)

    # Draw cash + cash collision
    glBegin(GL_QUADS)
    glColor4f(1., 1., 1., 1.)
    for x, y, ch in list(cashes):
        if collides_with(ppos, x*ts, y*ts):
            gotcash += 1
            cashes.remove((x, y, ch))
        blitquad(x, y, FIRST_CASH_TILE + int(time.time()*8) % (LAST_CASH_TILE - FIRST_CASH_TILE + 1))

    # render player ship (with shadow)
    glColor4f(1., 1., 1., 0.5)
    blitquad(int(ppos.x+2)/ts, int(ppos.y+2)/ts, FIRST_SHIP_SHADOW_TILE, rotation)
    glColor4f(1., 1., 1., 1.)
    blitquad(int(ppos.x)/ts, int(ppos.y)/ts, FIRST_SHIP_TILE, rotation)
    glEnd()

    # Wall hit checks
    hit = False
    for x, y in walls:
        if collides_with(ppos, x*ts, y*ts):
            ppos -= Vector2(x*ts-ppos.x, y*ts-ppos.y)
            speed *= -0.5
            hit = True

    # Steering
    rotation += steer

    # Move if not wall hit
    if not hit:
        ppos += Vector2((0, -1)).rotate(rotation) * speed

    # Accelerate/reverse/decelerate
    if accelerate:
        speed = min(maxspeed, speed + .2)
    elif reverse:
        speed = max(-maxspeed, speed - .2)
    else:
        speed *= 0.9

    # Draw foreground on top
    glCallList(fglist)

    # update screen
    pygame.display.set_caption(f'{fn} - cash: {gotcash}')
    pygame.display.flip()