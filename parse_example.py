# Copyright 2017 Google Inc.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# https://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import struct, argparse, os
from struct import unpack

parser = argparse.ArgumentParser(description='Read bin file')
parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Verbose')
parser.add_argument('-vv', '--vverbose', default=False, action='store_true', help='Very Verbose')
parser.add_argument('-t', '--test', default=False, action='store_true', help='Test - no actual commands are run')
parser.add_argument('-n', '--nbr', type=int, default=10, help='Test - no actual commands are run')
parser.add_argument('-dt', '--draw_thumbs', default=False, action='store_true', help='Draw Thumbs to thumbs/ directory')
parser.add_argument('-d', '--dump_full', default=False, action='store_true', help='Dump info')
parser.add_argument('infile',help='File to read')
args = parser.parse_args()


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

def draw_thumb(drec, fname):
    if os.path.exists(fname):
        return
    (pw, ph) = (256, 256)
    img = Image.new("RGB", (pw,ph), 'white')
    draw = ImageDraw.Draw(img)

    for xvecs,yvecs in drec['image']:
        tuples = [(x,yvecs[i]) for i, x in enumerate(xvecs)]
        draw.line(tuples, fill='black', width=1)
    img.save(fname)
    print "Saved %s" % (fname)

root_nom = args.infile.replace(".bin","")

for i,drawing in enumerate(unpack_drawings(args.infile)):
    # do something with the drawing
    if args.dump_full:
        print(drawing)
    else:
        print "#%d %s" % (i+1,drawing['key_id'])
    # print(drawing['countrycode'])
    if args.draw_thumbs:
        draw_thumb(drawing,"thumbs/%s_%d.png" % (root_nom, i+1))
    if i+1 == args.nbr:
        break
