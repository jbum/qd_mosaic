# render doodles as little 100x100 raster thumbnails, for use with photomosaic software.
#
import struct, argparse, os, sys
from struct import unpack
from mosaic_constants import bdata_path, set_path, thumbs_path

parser = argparse.ArgumentParser(description='Read bin file')
parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Verbose')
parser.add_argument('-vv', '--vverbose', default=False, action='store_true', help='Very Verbose')
parser.add_argument('-t', '--test', default=False, action='store_true', help='Test - no actual commands are run')
parser.add_argument('-f', '--force', default=False, action='store_true', help='Force image override')
parser.add_argument('-n', '--nbr', type=int, default=20000, help='Test - no actual commands are run')
# parser.add_argument('-dt', '--draw_thumbs', default=False, action='store_true', help='Draw Thumbs to thumbs/ directory')
parser.add_argument('-d', '--dump_full', default=False, action='store_true', help='Dump info')
parser.add_argument('-td', '--thumbs_dir', help='Thumbs dir (default uses name derived from file)')
parser.add_argument('-i', '-inv', '--invert', default=False, action='store_true', help='Invert (for white ink on black)')
parser.add_argument('-o', '--ofile', help="Output txt file override")
parser.add_argument('infile',help='File to read')
args = parser.parse_args()

if args.thumbs_dir == None:
    td = args.infile.replace(".bin","").(bdata_path+'/', thumbs_path+'/')
else:
    td = args.thumbs_dir
if td[-1] == '/':
    td = td[0:-1]
if not os.path.isdir(td):
    if os.path.exists(td):
        print td + " is a file (not a directory)"
        sys.exit()
    else:
        print "Making directory ",td
        os.mkdir(td)
args.thumbs_dir = td


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

'''

'image': [(
             (107, 132, 137, 160, 178, 182, 182, 187, 235, 254, 253, 242, 197, 213, 241, 236, 195, 176, 152, 135, 129, 121, 87, 82, 74, 73, 79, 88, 105, 30, 9, 0, 8, 68, 100, 108), 
             (79, 6, 0, 36, 58, 67, 75, 77, 58, 45, 56, 79, 137, 157, 212, 212, 194, 181, 158, 132, 154, 170, 217, 221, 221, 195, 161, 143, 120, 114, 110, 104, 99, 88, 79, 73))],

'image': [((91, 47, 42, 91, 126, 148), 
           (115, 204, 221, 199, 174, 154)), 
          ((137, 177, 189, 199, 197), 
           (156, 201, 220, 230, 125)), 
          ((194, 254), (122, 116)), 
          ((252, 217, 167), (113, 90, 74)), ((77, 61, 0), (112, 113, 100)), ((6, 82), (99, 56)), ((78, 95, 109, 144, 170), (63, 14, 0, 28, 71))]
'''

from PIL import Image, ImageDraw, ImageFont
from PIL import ImageFilter
pen_width = 15 # this is intended to simulate a medium pen stroke, if the 256x256 drawing occupies about 1/4 inch sq.

def draw_thumb(drec, fname):
    if os.path.exists(fname) and not args.force:
        # print "got it",fname
        return
    (pw, ph) = (262, 262)
    img = Image.new("RGB", (pw,ph), 'white' if not args.invert else 'black')

    # get width/height of image
    minx = min([min([x for x in xvecs]) for xvecs, yvecs in drec['image']])
    maxx = max([max([x for x in xvecs]) for xvecs, yvecs in drec['image']])
    miny = min([min([y for y in yvecs]) for xvecs, yvecs in drec['image']])
    maxy = max([max([y for y in yvecs]) for xvecs, yvecs in drec['image']])
    w, h = (1+maxx-minx, 1+maxy-miny)

    draw = ImageDraw.Draw(img)
    ox = (pw - w)/2
    oy = (ph - h)/2

    ink_color = 'black' if not args.invert else 'white'

    for xvecs,yvecs in drec['image']:
        tuples = [(ox+x,oy+yvecs[i]) for i, x in enumerate(xvecs)]
        draw.line(tuples, fill=ink_color, width=pen_width)
        # draw joints and end-caps
        for x,y in tuples:
            draw.ellipse([x-pen_width*0.5,y-pen_width*0.5,x+pen_width*0.5,y+pen_width*0.5], outline=None, fill=ink_color)
    # draw end-caps
    img = img.filter(ImageFilter.BLUR).filter(ImageFilter.BLUR).resize((102,102),Image.LANCZOS).crop((1,1,101,101))
    img.save(fname)
    # print "Saved %s %d %d" % (fname, w, h)


root_nom = args.infile.replace(".bin", "")

if args.ofile:
    setfile = args.ofile
else:
    setfile = args.infile.replace(".bin",".txt").(bdata_path+'/',set_path+'/')


with open(setfile,"w") as ofile:
    # ofile.write("CACHEROOT:%s/\n" % (args.thumbs_dir))
    for i,drawing in enumerate(unpack_drawings(args.infile)):
        # do something with the drawing
        if args.dump_full:
            print(drawing)
        # print(drawing['countrycode'])
        out_fname = "%s_%d.png" % (root_nom, i+1)
        draw_thumb(drawing,"%s/%s" % (args.thumbs_dir,out_fname)) # this will skip output if file exists
        ofile.write("%s%s/%s\n" % (('i' if args.invert else ''),root_nom,out_fname))
        if i % 1000 == 0:
            print i
        if i+1 == args.nbr:
            break
