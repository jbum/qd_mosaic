Mosaic builder for building photomosaic-style mosaics intended for use with pen plotters.

![Karloff](samples/stitchesi_karloff3_25_x_38_c20.jpg)
![Grace](samples/zigzag_grace_2_33_x_29_c20.jpg)

Currently works with images from the Quick Draw dataset at https://quickdraw.withgoogle.com/data

Scripts
```
make_sample.sh       # make a sample mosaic from scratch
get_desired_bins.py  # download a collection of bin files from quickdraw
dump_qds.py          # produce raster thumbnail images for an image set and a photoset file.
build_mosaic.py      # photomosaic builder - ported from code from my book Flickr Hacks



imageset.py          # code used by build_mosaic
mosaick.py           # code used by build_mosaic
mosaic_constants.py  # code used by build_mosaic (produces a preview and a json file)
render_mosaic_svg.py # render mosaic data from a json file to an SVG

```

Directories
```
thumbs\               # thumbnails are stored here - new sub-directories made by dump_qds
bdata\                # binary files are placed here by get_desired_bins.py
jdata\                # json tile layouts are placed here by build_mosaic
renders\              # preview images are placed here by build_mosaic
samples\              # some sample output
sets\                 # photolists used by build_mosaic and output by dump_qds
targets\              # target photos

```