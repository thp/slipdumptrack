# SlipSpeed track tester 2020-04-17 <m@thp.io>
# .. in good old OpenGL 1, celebrating the fixed function pipeline!
# (req: Pillow, ImageMagick, PyGame, PyOpenGL)
# Buy the game or get the shareware here: https://voxel.itch.io/slipspeed/

import glob, os, random, math, time, pygame, PIL.Image

from sliptiles import *
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

WAYPOINT_DEBUG = False

scr = pygame.display.set_mode((w, h), DOUBLEBUF | OPENGL)

def find_tile_ctrl(d, tile):
    for y in range(sz):
        for x in range(sz):
            if d[y*sz + x + sz*sz*2] == tile:
                return (x, y)

def blitquad(x, y, ch, rotation_deg=0, scale=1.):
    x0 = x * ts - ts * (scale - 1) / 2
    x1 = x0 + ts * scale
    y0 = y * ts - ts * (scale - 1) / 2
    y1 = y0 + ts * scale

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
fn = random.choice(glob.glob('SLIP*/ASSETS/TRACKS/*/*/TRACK.DAT'))

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

KEYMAP = {
    'left':       [K_LEFT,  K_a, K_j, K_f],
    'right':      [K_RIGHT, K_d, K_l, K_h],
    'accelerate': [K_UP,    K_w, K_i, K_t],
    'reverse':    [K_DOWN,  K_s, K_k, K_g],
}

class Player(object):
    def __init__(self, idx):
        self.idx = idx
        self.reset()
        self.gotcash = 0
        self.points = 0

    def reset(self):
        # Find first tile in the third layer (ships + waypoints)
        px, py = find_tile_ctrl(d, FIRST_SHIP_TILE+self.idx)
        self.ppos = Vector2((px, py)) * ts
        self.rotation = 0
        self.speed = 0
        self.ship_height = 2
        self.ship_dheight = 0
        self.lap = 0
        self.next_waypoint = 0
        self.steer = 0
        self.accelerate = False
        self.reverse = False
        self.celebrating = False
        self.alive = True

    def stop_moving(self):
        self.accelerate = False
        self.reverse = False
        self.speed = 0
        self.steer = 0

    def start_celebrating(self):
        self.celebrating = True
        self.points += 1
        self.stop_moving()

    def kill_off(self):
        self.alive = False
        self.stop_moving()

    def __repr__(self):
        return f'<Player {self.idx} @ ({self.ppos.x}, {self.ppos.y}) alive={self.alive}>'

    def handle(self, evt):
        if evt.type == KEYDOWN:
            if evt.key == KEYMAP['left'][self.idx]:
                self.steer = -3
            elif evt.key == KEYMAP['right'][self.idx]:
                self.steer = +3
            elif evt.key == KEYMAP['accelerate'][self.idx]:
                self.accelerate = True
            elif evt.key == KEYMAP['reverse'][self.idx]:
                self.reverse = True
        elif evt.type == KEYUP:
            if evt.key == KEYMAP['left'][self.idx] or evt.key == KEYMAP['right'][self.idx]:
                self.steer = 0
            elif evt.key == KEYMAP['accelerate'][self.idx]:
                self.accelerate = False
            elif evt.key == KEYMAP['reverse'][self.idx]:
                self.reverse = False

    def get_waypoint_distances(self):
        return [(math.sqrt((self.ppos.x-x*16)**2+(self.ppos.y-y*16)**2), i, x, y)
                for i, (x, y) in enumerate(waypoints)]

    def get_distance_to_next(self):
        waypoint_distances = self.get_waypoint_distances()
        return next(dist for (dist, i, x, y) in waypoint_distances if i == self.next_waypoint)


PLAYERS = 2

players = [Player(i) for i in range(PLAYERS)]

waypoints = [find_tile_ctrl(d, FIRST_WAYPOINT_TILE+i) for i in range(8)]

zoomin = 2
MAXSPEED = 6

def collides_with(ppos, x, y):
    return math.sqrt((x-ppos.x)**2 + (y-ppos.y)**2) < ts

camx = 0
camy = 0

celebration_started = None

while True:
    while True:
        evt = pygame.event.poll()
        if evt.type == NOEVENT:
            break

        if evt.type == KEYDOWN:
            if evt.key in (K_ESCAPE, K_q):
                raise SystemExit(1)

        if not any(player.celebrating for player in players):
            for player in players:
                if player.alive:
                    player.handle(evt)

    glClear(GL_COLOR_BUFFER_BIT)

    alive_players = [player for player in players if player.alive]

    # Check winning condition (one screenful distance)
    max_x_distance = w/zoomin
    max_y_distance = h/zoomin
    min_players_x = min(player.ppos.x for player in alive_players)
    max_players_x = max(player.ppos.x for player in alive_players)
    min_players_y = min(player.ppos.y for player in alive_players)
    max_players_y = max(player.ppos.y for player in alive_players)
    if max_players_x - min_players_x > max_x_distance or max_players_y - min_players_y > max_y_distance:
        ranked_alive_players = sorted(alive_players, key=lambda player: (player.lap, player.next_waypoint, -player.get_distance_to_next()))
        print('killing off:', ranked_alive_players[0])
        ranked_alive_players[0].kill_off()

    alive_players = [player for player in players if player.alive]

    if len(alive_players) == 1 and PLAYERS != 1 and celebration_started is None:
        alive_players[0].start_celebrating()
        celebration_started = time.time()

    if celebration_started is not None:
        if time.time() - celebration_started > 5:
            celebration_started = None
            for player in players:
                player.reset()

    xo = int((min_players_x + max_players_x) / 2 + ts/2 - w/2/zoomin)
    yo = int((min_players_y + max_players_y) / 2 + ts/2 - h/2/zoomin)

    alpha = 0.8

    camx = camx * alpha + xo * (1 - alpha)
    camy = camy * alpha + yo * (1 - alpha)

    glLoadIdentity()
    glOrtho(int(camx), int(camx+w/zoomin), int(camy+h/zoomin), int(camy), 0, 1)

    # Draw background below
    glCallList(bglist)

    # Player<->Player Collision
    for idx, player_a in enumerate(alive_players):
        for player_b in alive_players[idx+1:]:
            if collides_with(player_a.ppos, player_b.ppos.x, player_b.ppos.y):
                move = Vector2(player_b.ppos.x-player_a.ppos.x, player_b.ppos.y-player_a.ppos.y)
                player_a.ppos -= move / 2
                player_b.ppos += move / 2
                # TODO: Move relative to direction/speed and collision position
                player_a.speed *= -0.5
                player_b.speed *= -0.5

    # Draw cash + cash collision
    glBegin(GL_QUADS)
    glColor4f(1., 1., 1., 1.)
    for x, y, ch in list(cashes):
        for player in players:
            if collides_with(player.ppos, x*ts, y*ts):
                player.gotcash += 1
                cashes.remove((x, y, ch))
                break
        blitquad(x, y, FIRST_CASH_TILE + int(time.time()*8) % (LAST_CASH_TILE - FIRST_CASH_TILE + 1))

    # render player ship (with shadow)
    for player in players:
        if not player.celebrating:
            glColor4f(1., 1., 1., 1. / (1 + player.ship_height/4))
            blitquad(int(player.ppos.x)/ts, int(player.ppos.y)/ts, FIRST_SHIP_SHADOW_TILE+player.idx, player.rotation, 1. + (player.ship_height-2) / 32)
            glColor4f(1., 1., 1., 1.)
            blitquad(int(player.ppos.x-player.ship_height/2)/ts, int(player.ppos.y-player.ship_height/2)/ts, FIRST_SHIP_TILE+player.idx, player.rotation)
    glEnd()

    for player in players:
        waypoint_distances = player.get_waypoint_distances()

        current_waypoint = (player.next_waypoint + len(waypoints) - 1) % len(waypoints)
        previous_waypoint = (player.next_waypoint + len(waypoints) - 2) % len(waypoints)
        #print(f'curr: {current_waypoint}, next: {player.next_waypoint}')

        for pos, (distance, i, x, y) in enumerate(sorted(waypoint_distances)):
            glColor4f(1., 1., 1., 1.)
            glBegin(GL_QUADS)
            blitquad(x, y, FIRST_WAYPOINT_TILE+i)
            glEnd()

            glDisable(GL_TEXTURE_2D)
            glBegin(GL_LINES)
            if pos == 0:
                if player.next_waypoint == i:
                    player.next_waypoint += 1
                    print(f'next waypoint reached {player.next_waypoint}')

                    if player.next_waypoint == len(waypoints):
                        print('next lap')
                        player.next_waypoint = 0
                        player.lap += 1
                elif previous_waypoint == i:
                    ...
                    #player.next_waypoint = current_waypoint
                    #if player.next_waypoint == len(waypoints)-1:
                    #    print('prev lap')
                    #    player.lap -= 1
                    #print(f'back to current waypoint {player.next_waypoint}')

            if player.next_waypoint == i:
                glColor4f(0., 1., 0., 1. if WAYPOINT_DEBUG else 0)
            elif current_waypoint == i:
                glColor4f(1., 0., 0., 1. if WAYPOINT_DEBUG else 0)
            elif previous_waypoint == i:
                glColor4f(1., 1., 0., 1. if WAYPOINT_DEBUG else 0)
            else:
                glColor4f(0., 0., 0., 0.)

            glVertex2f(x*16+8, y*16+8)
            glVertex2f(player.ppos.x+8, player.ppos.y+8)
            glEnd()
            glEnable(GL_TEXTURE_2D)

        # Wall hit checks
        hit = False
        for x, y in walls:
            if collides_with(player.ppos, x*ts, y*ts):
                player.ppos -= Vector2(x*ts-player.ppos.x, y*ts-player.ppos.y)
                player.speed *= -0.5
                hit = True

        if player.celebrating:
            player.rotation += 4

        # Steering
        player.rotation += player.steer

        # Move if not wall hit
        if not hit:
            player.ppos += Vector2((0, -1)).rotate(player.rotation) * player.speed

        # Accelerate/reverse/decelerate
        if player.accelerate:
            player.speed = min(MAXSPEED, player.speed + .2)
        elif player.reverse:
            player.speed = max(-MAXSPEED, player.speed - .2)
        else:
            player.speed *= 0.9

        # Height
        player.ship_dheight -= 1
        player.ship_height += player.ship_dheight
        if player.ship_height <= 2:
            if abs(player.ship_dheight) > 2:
                player.ship_dheight *= -0.8
            else:
                if player.celebrating:
                    player.ship_dheight = 10
                else:
                    player.ship_dheight = 0
            player.ship_height = 2

    # Draw foreground on top
    glCallList(fglist)

    # render celebrating players on top of foreground
    glBegin(GL_QUADS)
    glColor4f(1., 1., 1., 1.)
    for player in players:
        if player.celebrating:
            glColor4f(1., 1., 1., 1. / (1 + player.ship_height/4))
            blitquad(int(player.ppos.x)/ts, int(player.ppos.y)/ts, FIRST_SHIP_SHADOW_TILE+player.idx, player.rotation, 1. + (player.ship_height-2) / 32)
            glColor4f(1., 1., 1., 1.)
            blitquad(int(player.ppos.x-player.ship_height/2)/ts, int(player.ppos.y-player.ship_height/2)/ts, FIRST_SHIP_TILE+player.idx, player.rotation)
    glEnd()

    # update screen
    pygame.display.set_caption(f'{fn} - cash: {players[0].gotcash} - lap: {players[0].lap}')
    pygame.display.flip()
