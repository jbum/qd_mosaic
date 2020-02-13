# render mosaic in svg form using vector data
# 

'''
'''

import argparse, json, os, re, sys
import svgwrite
import struct
from struct import unpack
from mosaic_constants import bdata_path, json_path

parser = argparse.ArgumentParser(description='Render SVG Mosaic')
parser.add_argument('-pts','--pts_per_tile',type=int,default=96/4,help="Help units per tile, defaults to 24 (1/4 inch)")
# parser.add_argument('bin_file', help='Image set file')
parser.add_argument('json_file', help='Json file - produced by build_mosaic')
parser.add_argument('svg_file', help='SVG file to output')

args = parser.parse_args()

if not os.path.exists(args.json_file):
    print("%s not found" % (args.json_file))

sdata = json.loads(open(args.json_file).read())

basepic = sdata['basepic']
hcells = sdata['hcells']
vcells = sdata['vcells']
tileAspectRatio = sdata['tileAspectRatio']
targetAspectRatio = sdata['targetAspectRatio']
cells = sdata['cells']
finalimages = sdata['finalimages']
is_inverted = False

# 'desc':'i-stitches/stitches_358.png'
# compile list of bin files employed and which images are used
bset_dict = {}
pat = re.compile(r'^(.*)/(\w+)_(\d+).png')
for fimg in finalimages:
    m = pat.match(fimg['desc'])
    if m:
        (bdir,bnom,bnum) = (m.group(1),m.group(2), int(m.group(3))-1)
        if 'i-' in bdir:
            is_inverted = True
        if bnom not in bset_dict:
            bset_dict[bnom] = []
        bset_dict[bnom].append(bnum)

# !! initialize SVG HERE
margin = args.pts_per_tile
pw, ph = (hcells*args.pts_per_tile+margin*2, vcells*args.pts_per_tile+margin*2)
svg_document = svgwrite.Drawing(filename = args.svg_file,
                                size = ("%dpx" % (pw), "%dpx" % (ph)),
                                debug = False)  # debug = false makes it MUCH faster
svg_drawing = svg_document.g(stroke='black',fill='none')

def render_drawing_cell(cell, drec):
    global svg_document

    (tx, ty, do_flop) = (cell['x'], cell['y'], cell['flop'])
    (px, py) = (margin+tx*args.pts_per_tile, margin+ty*args.pts_per_tile)
    minx = min([min([x for x in xvecs]) for xvecs, yvecs in drec['image']])
    maxx = max([max([x for x in xvecs]) for xvecs, yvecs in drec['image']])
    miny = min([min([y for y in yvecs]) for xvecs, yvecs in drec['image']])
    maxy = max([max([y for y in yvecs]) for xvecs, yvecs in drec['image']])
    w, h = (1+maxx-minx, 1+maxy-miny)
    ox = (256 - w)/2.0
    oy = (256 - h)/2.0
    sc = args.pts_per_tile / 256.0

    # g = svg_document.g(transform="translate(%.1f %1.f)" % (px, py))
    # precompute translate followed by scale
    sx,sy = (sc,sc)
    # g = svg_document.g(transform="matrix(%.2f 0 0 %.2f %.2f %.2f)" % (sx,sy,px,py))
    g = svg_document.g()
    for xvecs,yvecs in drec['image']:
        # centered, flopped and scaled coords
        tuples = [(px+(ox+(x if not do_flop else maxx-x))*sc,py+(oy+yvecs[i])*sc) for i, x in enumerate(xvecs)]
        dpath = ''
        for i,(x,y) in enumerate(tuples):
            if i == 0:
                dpath = "M%.1f,%.1f" % (x,y)
            elif i == 1:
                dpath += " L%.1f,%.1f" % (x,y)
            else:
                dpath += ", %.1f,%.1f" % (x,y)
        # print dpath
        g.add(svg_document.path(d=dpath))
        # draw.line(tuples, fill='black', width=pen_width)
    return g

def unpack_drawing(file_handle):
    key_id, = unpack('Q', file_handle.read(8))
    countrycode, = unpack('2s', file_handle.read(2))
    recognized, = unpack('b', file_handle.read(1))
    timestamp, = unpack('I', file_handle.read(4))
    n_strokes, = unpack('H', file_handle.read(2))
    image = []
    for i in range(n_strokes):
        n_points, = unpack('H', file_handle.read(2))
        fmt = str(n_points) + 'B'
        x = unpack(fmt, file_handle.read(n_points))
        y = unpack(fmt, file_handle.read(n_points))
        image.append((x, y))

    return {
        'key_id': key_id,
        'countrycode': countrycode,
        'recognized': recognized,
        'timestamp': timestamp,
        'image': image
    }

def unpack_drawings(filename):
    with open(filename, 'rb') as f:
        while True:
            try:
                yield unpack_drawing(f)
            except struct.error:
                break

for key,known_ids in bset_dict.items():
    print("reading " + key)
    bin_file = "%s/%s.bin" % (bdata_path,key)
    if not os.path.exists(bin_file):
        print("%s not found" % (bin_file))
        sys.exit()

    max_id = max(known_ids)

    # walk through the binary file until we've rendered our data...
    for i,drawing in enumerate(unpack_drawings(bin_file)):
        if i not in known_ids:
            continue
        thumb_nom = "%s/%s_%d.png" % (key, key, i+1)
        got_it = False
        for cell in cells:
            if thumb_nom in finalimages[cell['iIdx']]['desc']:
                g = render_drawing_cell(cell, drawing)
                cell['gpath'] = g
                got_it = True
        if not got_it:
            print("Could not find %s for %s %d" % (thumb_nom,key,i))
        if i >= max_id:
            break
print("adding drawing")

# do 4 corner cells first, to insure paper isn't skewed too bad
preview_cells = (0,hcells-1,(vcells-1)*hcells,(vcells-1)*hcells+hcells-1)
for paddr in preview_cells:
    cell = cells[paddr]
    svg_drawing.add(cell['gpath'])

# do remaining cells in an optimal order
for y in range(vcells):
    is_rev = (y % 2) != 0
    for x in range(hcells):
        addr = y*hcells + ((hcells-(x+1)) if is_rev else x)
        if addr in preview_cells:
            continue
        cell = cells[addr]
        svg_drawing.add(cell['gpath'])
svg_document.add(svg_drawing)
print("saving svg")
svg_document.save()


