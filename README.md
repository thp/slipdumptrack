SlipSpeed Track Viewer
======================

This is a tool to dump the track layouts into image files for
an easy overview and finding shortcuts.

Getting The Game
----------------

Download the Shareware version or buy the full game here:
[SlipSpeed by voxel, tijn on itch.io](https://voxel.itch.io/slipspeed)

Dependencies
------------

 - [Pillow](https://pillow.readthedocs.io/en/stable/) -- `pip3 install Pillow`
 - [ImageMagick](https://imagemagick.org/) -- `apt install imagemagick`

How To Use
----------

Run the script in the game folder. It will output 4 GIFs per track, the
3 layers and an animated GIF that adds each layer on top of the other.

File Format
-----------

The `TRACK.DAT` file contains 3 layers of a 128x128 tile grid.
Each layer contains 1 byte per tile, indexing into TILES.PNG
(see below). Layer 1 is at offset 0, layer 2 at offset 16384
(128x128) and layer 3 at offset 32768 (2x128x128).

 - Layer 1: Background layer (probably also collision/border info?)
 - Layer 2: Foreground layer (players are rendered below it)
 - Layer 3: Player starting positions and (waypoints for AI?)

The `TILES.PNG` stores 256 16x16 tiles that are referenced by
the TRACK.DAT file. Tile 0 is at (0, 0), tile 1 is at (16, 0),
tile 2 at (32, 0), ..., tile 16 is at (0, 16), etc...
