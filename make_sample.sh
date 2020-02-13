# make_sample
#
# these first steps only need to be done once, once the thumbnails are produced you can
# repeat steps 3 and 4 with different target pictures and settings.

# step 1 - get desired binfiles (about 20 megs each)
#
python get_bins.py shorts

# 
# step 2 - convert these into thumbnails  (use -inv if you are planning on using light ink on dark paper)
#  (use pypy or something faster if you can)
# this is a faster example, but use 20000+ images if you want a better looking result
python make_thumbs.py -n 2000 bdata/shorts.bin
# python make_thumbs.py -inv -n 2000 bdata/shorts.bin  # inverted

# step 3. build the mosaic (use pypy or something faster if you can)
python build_mosaic.py thumbs/shorts.txt targets/grace_2.png -novars -max 800 -v

# step 4. build the svg
python render_mosaic_svg.py jdata/shorts_grace_2_mosaick.json renders/test.svg
#

# example of mosaic using multiple symbols
# ..use steps 1 and 2 to download individual sets you want.
# ...then extract some of each into a single file (called multi3.txt in this example)
# python mix_thumbs.py line circle zigzag stitches hurricane -o thumbs/abstract.txt
# python build_mosaic.py thumbs/abstract.txt targets/grace_2.png -novars -max 800 -v
# python render_mosaic_svg.py jdata/abstract_grace_2_mosaick.json renders/test.svg
