#
#

from imageset import FlickrSet, ListSet
from mosaick import Mosaick
import json
import argparse
import sys, os, re
from mosaic_constants import set_path

'''
TODO: 
Sample images in Grayscale space to save memory/time.


tests:
pypy build_mosaic.py hurricane_set.txt targets/grace_2.png -noflops -novars -cacheroot thumbs/

# pypy build_mosaic.py hurricane_set.txt targets/grace_2.png -noflops -novars -cacheroot hurricane/ -max 1000 -v
# pypy build_mosaic.py hurricane_set.txt targets/grace_2.png -noflops -novars -cacheroot hurricane/ -v
# pypy build_mosaic.py skull_set.txt targets/grace_2.png -noflops -novars -cacheroot skull/ -v


# pypy build_mosaic.py sets/skull_set.txt targets/grace_2.png -novars -cacheroot thumbs/ -v



'''


parser = argparse.ArgumentParser(description='Build Photomosaics using Flickr sets or photo lists')
# integer options
parser.add_argument('-rx', '--resox', type=int, default=7, help='Sub-tile X-resolution')
parser.add_argument('-ry', '--resoy', type=int, default=7, help='Sub-tile Y-resolution')
parser.add_argument('-max', '--maxtiles', type=int, default=800, help='maximum tiles (default=800)')
parser.add_argument('-min', '--mindupedistance', type=int, default=8, help='min dupe distance (default=8)')
parser.add_argument('-mixin', '--mixin', type=int, default=0, help='render option: mix in color amount (0-100) (default=0)')
parser.add_argument('-cellsize', '--cellsize', type=int, default=20, help='render option: cell size (default=20)')
parser.add_argument('-hlimit', '--hlimit', type=int, default=0, help='hmode limit - number of images to map, default=unlimited')
parser.add_argument('-q', '--quality', type=int, default=90, help='render option: jpeg quality')

# string options
parser.add_argument('-o', '--ofile', default='', help='output file (default is auto generated)')
parser.add_argument('-hbase', '--hbase', default='', help='hmode base image')
parser.add_argument('-cacheroot', '--cacheroot', default='thumbs/', help='image list cache root')

# boolean options
parser.add_argument('-png', default=False, action='store_true', help='render option: produce image in png format')
parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Verbose messages')
parser.add_argument('-big', '--big', default=False, action='store_true', help='render option: same as cellsize=100')
parser.add_argument('-load', '--load', default=False, action='store_true', help='Load tile choices from previous run (change render options only)')
parser.add_argument('-hm', '--heatmap', default=False, action='store_true', help='Produce heatmap of high-constrast cells')
parser.add_argument('-noborders', '--noborders', default=False, action='store_true', help='Reject images with solid-color borders or over 2:1 aspect ratio')
parser.add_argument('-noflops', '--noflops', default=False, action='store_true', help='Images may not be flopped horizontally')
parser.add_argument('-nodupes', '--nodupes', default=False, action='store_true', help='No duplicate images (even when spread apart)')
parser.add_argument('-noownerdupes', '--noownerdupes', default=False, action='store_true', help='Images from the same owner are treated as dupes')
parser.add_argument('-novars', '--novariations', default=False, action='store_true', help='Don\'t use cropping variations (1/3 faster, slightly worse matching, keeps crops centered)')
parser.add_argument('-accurate', '--accurate', default=False, action='store_true', help='2x slower than normal, slightly better results')
parser.add_argument('-draft', '--draft', default=False, action='store_true', help='4x faster than normal, slightly worse results')
parser.add_argument('-quick', '--quick', default=False, action='store_true', help='Only use 100 source images - for testing')
parser.add_argument('-anno', '--anno', default=False, action='store_true', help='render option: annotate cells with labels')
parser.add_argument('-hmode', '--hmode', default=False, action='store_true', help='hmode (overlapping mosaic - not yet working)')
parser.add_argument('-grayscale', '--grayscale', default=False, action='store_true', help='Convert image to grayscale')
parser.add_argument('-tint', '--tint', default=False, action='store_true', help='Use average color for mixin tinting')

# arguments
parser.add_argument('pfile',  help='photo list file')
parser.add_argument('basepic',  help='target image')

args = parser.parse_args()

imageSet = None

if '.json' in args.pfile:
  imageSet = FlickrSet( {'filename': args.pfile,
                         'downloadsOK': True,
                         'verbose': True, # args.verbose
                         'dupeOwnersOK': not args.noownerdupes,
                         'cacheRoot': args.cacheroot,
                        } )
else:
  imageSet = ListSet( {'filename': args.pfile, 
                       'downloadsOK': False,
                       'verbose': True, # args.verbose
                       'cacheRoot': args.cacheroot,
                      } )

print("Images: %d"  % (imageSet.getMaxImages()))

rootname = re.sub(r'\.\w+$', '', args.pfile).replace(set_path+'/','')
print("rootname =" + rootname)

moz = Mosaick({'resoX': args.resox,
              'resoY': args.resoy,
              'max_images': args.maxtiles,
              'imageset': imageSet,
              'basepic': args.basepic,
              'noborders': args.noborders,
              'doflops': not args.noflops,
              'rootname': rootname,
              'cellsize': 100 if args.big else args.cellsize,
              'dupesOK': not args.nodupes,
              # 'lab': $lab,
              'mixin': args.mixin,
              'tint': args.tint,
              # 'speckle': $speckle,
              'accurate': args.accurate,
              'draft': args.draft,
              'usevars': not args.novariations and not args.draft,
              'load': args.load,
              # 'cspace': $cspace,
              'hmode': args.hmode,
              'hlimit': args.hlimit,
              'hbase': args.hbase,
              # 'strip': $strip,  # unimplemented - use this for large images if we can't allocate the full-sized mosaic
              'minDupeDist': args.mindupedistance,
              'verbose': args.verbose,
              'png': args.png,
              'filename': args.ofile,
              'quality': args.quality,
              'anno': args.anno,
              'grayscale': args.grayscale,
              'hasForces':True, # treat it as true all the time - use individual records to control it
              })


if (args.heatmap):
  moz.makeHeatmap("heatmap.png")
  print("Done making heatmap") # !! include timing info
  sys.exit()

moz.makeMosaic()
print("Done making mosaic") # !! include timing info

