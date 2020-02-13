# render doodles as little 100x100 raster thumbnails, for use with photomosaic software.
#
import struct, argparse, os, sys
from struct import unpack
from mosaic_constants import bdata_path, set_path, thumbs_path, thumb_pen_width

from PIL import Image, ImageDraw, ImageFont
from PIL import ImageFilter

pen_width = thumb_pen_width 

parser = argparse.ArgumentParser(description='Make thumbnails from a binfile')
parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Verbose')
parser.add_argument('-vv', '--vverbose', default=False, action='store_true', help='Very Verbose')
parser.add_argument('-t', '--test', default=False, action='store_true', help='Test - no actual commands are run')
parser.add_argument('-f', '--force', default=False, action='store_true', help='Force image override')
parser.add_argument('-n', '--nbr', type=int, default=20000, help='Test - no actual commands are run')
parser.add_argument('-d', '--dump_full', default=False, action='store_true', help='Dump info')
parser.add_argument('-td', '--thumbs_dir', help='Thumbs dir (default uses name derived from file)')
parser.add_argument('-i', '-inv', '--invert', default=False, action='store_true', help='Invert (for white ink on black)')
parser.add_argument('-o', '--ofile', help="Output txt file override")
parser.add_argument('infile',help='Bin file to read doodles from')
args = parser.parse_args()

if args.thumbs_dir == None:
    td = args.infile.replace(".bin","").replace(bdata_path+'/', thumbs_path+'/'+('i-' if args.invert else ''))
else:
    td = args.thumbs_dir

if td[-1] == '/':
    td = td[0:-1]

if not os.path.isdir(td):
    if os.path.exists(td):
        print td + " is a file (not a directory)"
        sys.exit()
    else:
        print("Making directory " + td)
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


root_nom = args.infile.replace(".bin", "").replace(bdata_path+'/','')

if args.ofile:
    setfile = args.ofile
else:
    setfile = args.infile.replace(".bin",".txt").replace(bdata_path+'/',set_path+'/'+('i-' if args.invert else ''))


with open(setfile,"w") as ofile:
    # ofile.write("CACHEROOT:%s/\n" % (args.thumbs_dir))
    for i,drawing in enumerate(unpack_drawings(args.infile)):
        # do something with the drawing
        if args.dump_full:
            print(drawing)
        # print(drawing['countrycode'])
        out_fname = "%s_%d.png" % (root_nom, i+1)
        draw_thumb(drawing,"%s/%s" % (args.thumbs_dir,out_fname)) # this will skip output if file exists
        ofile.write("%s%s/%s\n" % (('i-' if args.invert else ''),root_nom,out_fname))
        if i % 1000 == 0:
            print i
        if i+1 == args.nbr:
            break
