# first 6 rows of tiles = track
FIRST_TRACK_TILE = 0
# next 4(?) rows = wall
FIRST_WALL_TILE = 6 * 16
# next 2(?) rows = decoration
FIRST_DECORATION_TILE = 10 * 16
# then the exhaust tiles
FIRST_EXHAUST_TILE = 12 * 16
# then "unused" (black) tiles that are still used by "2ATHENS"
# ASSETS/TRACKS/1EARTH/2ATHENS/TRACK.DAT x=4 y=75 tile=198
# ASSETS/TRACKS/1EARTH/2ATHENS/TRACK.DAT x=5 y=75 tile=199
FIRST_UNUSED_TILE = 12 * 16 + 4
# then the cash tiles
FIRST_CASH_TILE = 12 * 16 + 8
# then the ship tiles
FIRST_SHIP_TILE = 13 * 16
# then the floppy tiles
FIRST_FLOPPY_TILE = 13 * 16 + 8
# then the ship shadows
FIRST_SHIP_SHADOW_TILE = 14 * 16
# then the floppy shadows
FIRST_FLOPPY_SHADOW_TILE = 14 * 16 + 8
# then the waypoints(?)
FIRST_WAYPOINT_TILE = 15 * 16
# then there are some special values (visually "alternative waypoints")
FIRST_SPECIAL_TILE = 15 * 16 + 8

LAST_TRACK_TILE = FIRST_WALL_TILE - 1
LAST_WALL_TILE = FIRST_DECORATION_TILE - 1
LAST_DECORATION_TILE = FIRST_EXHAUST_TILE - 1
LAST_EXHAUST_TILE = FIRST_EXHAUST_TILE + 3
LAST_UNUSED_TILE = FIRST_UNUSED_TILE + 3
LAST_CASH_TILE = FIRST_CASH_TILE + 7
LAST_SHIP_TILE = FIRST_SHIP_TILE + 7
LAST_FLOPPY_TILE = FIRST_FLOPPY_TILE + 7
LAST_SHIP_SHADOW_TILE = FIRST_SHIP_TILE + 7
LAST_FLOPPY_SHADOW_TILE = FIRST_FLOPPY_SHADOW_TILE + 7
LAST_WAYPOINT_TILE = FIRST_WAYPOINT_TILE + 7
# Exclude 0xFF, although it is "special" it's used as "empty" marker
LAST_SPECIAL_TILE = FIRST_SPECIAL_TILE + 6

CLASSIFICATION = (
    ('trck', FIRST_TRACK_TILE,         LAST_TRACK_TILE),
    ('wall', FIRST_WALL_TILE,          LAST_WALL_TILE),
    ('deco', FIRST_DECORATION_TILE,    LAST_DECORATION_TILE),
    ('xhst', FIRST_EXHAUST_TILE,       LAST_EXHAUST_TILE),
    ('xxxx', FIRST_UNUSED_TILE,        LAST_UNUSED_TILE),
    ('cash', FIRST_CASH_TILE,          LAST_CASH_TILE),
    ('ship', FIRST_SHIP_TILE,          LAST_SHIP_TILE),
    ('35in', FIRST_FLOPPY_TILE,        LAST_FLOPPY_TILE),
    ('shdw', FIRST_SHIP_SHADOW_TILE,   LAST_SHIP_SHADOW_TILE),
    ('35sh', FIRST_FLOPPY_SHADOW_TILE, LAST_FLOPPY_SHADOW_TILE),
    ('wpnt', FIRST_WAYPOINT_TILE,      LAST_WAYPOINT_TILE),
    ('spec', FIRST_SPECIAL_TILE,  LAST_SPECIAL_TILE),
    ('none', 0xFF,                     0xFF),
)
