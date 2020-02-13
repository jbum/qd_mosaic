# Photo Mosaic library -- Jim Bumgardner
# based on the Perl scripts I wrote for the book Flickr Hacks
#

from PIL import Image, ImageDraw
import re, json, copy
from math import sqrt
from operator import itemgetter
import datetime as dt
from mosaic_constants import json_path, render_path

class Mosaick:
    def __init__(self, params):
        # set params with reasonable defaults...
        self.json_path = json_path
        self.render_path = render_path
        self.max_images = params.get('max_images', 800)
        self.imageset   = params.get('imageset', [])
        self.reso       = params.get('reso', 0)
        self.resoX      = params.get('resoX', 7)
        self.resoY      = params.get('resoY', 7)
        self.cellsize   = params.get('cellsize', 20)
        self.noborders  = params.get('noborders', False)
        self.verbose    = params.get('verbose', False)
        self.grabThumbs = params.get('grabThumbs', False)
        self.doflops    = params.get('doflops', False)
        self.load       = params.get('load', False)
        self.rootname   = params.get('rootname', 'mosaic')
        self.dupesOK    = params.get('dupesOK', False)
        self.cspace     = params.get('cspace', False)  # color space (in bits per component, 0 = normalized)
        self.hmode      = params.get('hmode', False)  # heatmap mode, with overlapping tiles - unported from perl
        self.hlimit     = params.get('hlimit', 0) # heatmap image limit 0 = unlimited
        self.hbase      = params.get('hbase', '')
        self.mixin      = params.get('mixin', 0)
        self.cmode      = params.get('cmode', 'Darken')  # also 'Blend'
        self.anno       = params.get('anno', False)
        self.grayscale  = params.get('grayscale', False)
        self.minDupeDist = params.get('minDupeDist', 8)
        self.tileblur   = params.get('tileblur', 0.4)
        self.tilefilter = params.get('tilefilter', 'Sinc')  # currently unused
        self.targetblur = params.get('targetblur', 0.4)
        self.dupeList   = params.get('dupeList', {})
        self.hasForces  = params.get('hasForces', False)
        self.targetfilter = params.get('targetfilter', 'Sinc') # currently unused
        self.basepic    = params.get('basepic', '')
        self.usevars    = params.get('usevars', True)
        self.accurate   = params.get('accurate', False)
        self.draft      = params.get('draft', False)
        self.filename   = params.get('filename', '')
        self.quality    = params.get('quality', 90)
        self.strip      = params.get('strip', False)
        self.png        = params.get('png', False)
        self.tint       = params.get('tint', False)

        self.filter     = Image.ANTIALIAS  # NEAREST, BICUBIC, BILINEAR, ANTIALIAS is best for color averaging

        # computed
        print("Quality = %d" % (self.quality))
        print("Mixin = %d" % (self.mixin))

        if self.hmode and self.cspace == 0:
            self.cspace = 8
        if self.resoX == 0 and self.reso > 0:
            self.resoX = reso
        if self.resoY == 0:
            self.resoY = self.resoX
        self.reso2 = self.resoX * self.resoY
        self.tileAspectRatio = self.resoX / float(self.resoY)
        self.minDupeDist2 = self.minDupeDist ** 2
        print("Min Dupe Dist ^2 = %d" % (self.minDupeDist2))


        self.basename = self.basepic
        if self.hmode and self.hbase == '':
            self.hbase = self.basepic

        self.basename = re.sub(r"^.*\/", '', self.basename)
        self.basename = re.sub(r"\.(jpg|png|gif)", '', self.basename)

        self.sortedcells = []
        self.finalimages = []
        self.images = []

        print("Done Mosaic Init")

    def setupCells(self):
        cells = []
        aart = 'BEEEEEEEEEMWWQQQQQQQQQQQNHHHHH@@@@@KKKRRRAA#dddgg88bbbbXXpppPFFFDSSww4444%k9966m222xx$ZhhLLLf&&&V3s55555555ooTuuzvvJJJJJJJJJnclIrrrttjjjjjjj[]]??>><1}}}}}}}}{{{{{="""i/\\\\\\\\\\++++*;;||||!!!!^^^^^^^^^^^^^^^^:::,,,,,,\'\'~~~~~-----____________.......`````````````';
        srcimg = Image.open(self.basepic)
        w, h = srcimg.size
        aspect = h/float(w)
        self.targetAspectRatio = aspect
        hcells = sqrt(self.max_images / aspect)
        vcells = (hcells * aspect) * self.tileAspectRatio
        self.hcells = int(hcells + 0.5)
        self.vcells = int(vcells + 0.5)
        if (self.hcells * self.vcells > self.max_images):
          self.hcells = int(hcells)
          self.vcells = int(vcells)
        if self.resoX*self.hcells > w:
          self.resoX = int(w / self.hcells)
          if self.resoX < 1:
            self.resoX = 1 
          self.resoY = int(self.resoX / self.tileAspectRatio)
          self.reso2 = self.resoX * self.resoY
          print("Forcing Reso to %d x %d due to lack of resolution in target image" % (self.resoX, self.resoY))
        elif self.resoY * self.vcells > h:
          self.resoY = int(h / self.vcells)
          if self.resoY < 1:
              self.resoY = 1
          self.resoX = int(self.resoY * self.tileAspectRatio)
          self.reso2 = self.resoX * self.resoY
          print("Forcing Reso to %d x %d due to lack of resolution in target image" % (self.resoX, self.resoY))
        if self.verbose:
            print("Original Image Width %d x %d" % (w,h))
            print("Allocating Cell Data %dx%d x %dx%d (AR=%.2f)" % (self.hcells, self.vcells, self.resoX, self.resoY, self.tileAspectRatio))

        # this makes baseimg, and baseimg2 clones of srcimg, but converted specifically to RGB space
        # baseimg = Image.open(self.basepic)
        baseimg = srcimg.convert("RGB")

        baseimg2 = srcimg.convert("RGB")

        baseimg = baseimg.resize((self.hcells, self.vcells), self.filter)
        baseimg2 = baseimg2.resize((self.hcells*self.resoX, self.vcells*self.resoY), self.filter)
        bpixels = baseimg.getdata()

        w2,h2 = baseimg2.size

        if not self.hmode:
          # normal mode
          print("Walking Pixels")
          i = 0
          for y in range(self.vcells):
            outputStr = '' # '\033[7m'
            for x in range(self.hcells):
              rgb = bpixels[i]
              # rgb = baseimg.get_pixels(x,y,1,1)[0]
              l = getHaeberliLuminance(rgb)
              hsv = RGBtoHSV(rgb)
              
              vc = [0,90,37,97,97][int(l*4)]

              chrpos = int(l*255)
              chr = aart[chrpos:chrpos+1]
              # outputStr += chr + chr
              outputStr += "\033[%dm%s%s" % (vc,chr,chr)
              # puts "rgb = #{rgb[0]},#{rgb[1]},#{rgb.blue} max=#{Magick::QuantumRange} sat=#{hsv[1]} "
              x0 = x * self.resoX
              y0 = y * self.resoY
              # pull the appropriate rectangle - note we could also do this using getdata if we crop it out
              croptile = baseimg2.crop((x0,y0,x0+self.resoX,y0+self.resoY))
              pix = list(croptile.getdata())

              # !! convert to cspace...
              # !! lab color conversion...

              # precompute flopped pixels...
              fpix = list(croptile.transpose(Image.FLIP_LEFT_RIGHT).getdata())

              cell = { 'i':i, 'x':x, 'y':y, 'l':l, 's':hsv[1], 'pix':pix, 'fpix':fpix, 'avg':rgb }

              cells.append(cell)
              i += 1
            outputStr += "\033[0m"
            print(outputStr)

        else:
          # hmode - overlapping cells - experimental
          i = 0
          for y in range(self.vcells*self.resoY-self.resoY):
            outputStr = ''
            for x in range(self.hcells*self.resoX-self.resoX):
              # note: this is not the correct average rgb for the cell
              # but I don't think we're using luminance for hmode...
              rgb = baseimg.getpixel((int(x/self.resoX),int(y/self.resoY)))
              l = getHaeberliLuminance(rgb)
              if x % self.resoX == 0 and y % self.resoY == 0:
                chrpos = int(l*255)
                chr = aart[chrpos:chrpos+1]
                outputStr += chr + chr

              pix = list(baseimg2.crop((x,y,x+self.resoX,y+self.resoY)).getdata())
              # !! convert to color space
              # !! lab color conversion...
              # !! tinting
              cell = { 'i':i, 'x':x, 'y':y, 'l':l, 'var':0, 'pix':pix, 'avg':rgb }
              cells.append(cell)
              i += 1

            if outputStr != '':
              print(outputStr)

        self.cells = cells

        if not self.hmode:
          # sort cells by constrast of interior pixels - high contrast cells (such as eyes) will be processed first
          for cell in cells:
            cell['e'] = self.getEdginess(cell)
          # sort cells here
          self.sortedcells = sorted(cells, key=itemgetter('e'), reverse=True)

        print("Done setup cells")

    def getEdginess(self,cell):
        pix = cell['pix']
        cumdiff = 0
        resoX = self.resoX

        for i in range(self.reso2):
          x = i % self.resoX
          y = int(i / self.resoX)

          if y > 0:
            j = i - self.resoX
            cumdiff += ((pix[j][0] - pix[i][0]) ** 2 + (pix[j][1] - pix[i][1]) ** 2 + (pix[j][2] - pix[i][2]) ** 2) / 255.0

          if y < self.resoY-1:
            j = i + self.resoX
            cumdiff += ((pix[j][0] - pix[i][0]) ** 2 + (pix[j][1] - pix[i][1]) ** 2 + (pix[j][2] - pix[i][2]) ** 2) / 255.0

          if x > 0:
            j = i - 1
            cumdiff += ((pix[j][0] - pix[i][0]) ** 2 + (pix[j][1] - pix[i][1]) ** 2 + (pix[j][2] - pix[i][2]) ** 2) / 255.0

          if x < self.resoX-1:
            j = i + 1
            cumdiff += ((pix[j][0] - pix[i][0]) ** 2 + (pix[j][1] - pix[i][1]) ** 2 + (pix[j][2] - pix[i][2]) ** 2) / 255.0

        return cumdiff


    def makeHeatmap(self, filename):
        print("Making heatmap")
        if not self.sortedcells:
            self.setupCells()
            if not self.sortedcells:
                print("Problem setting up cells for heatmap")
                return

        width = self.resoX * self.hcells
        height = self.resoY * self.vcells
        heatmap = Image.new("RGB", (width, height), "black")
        hpixels = heatmap.load() # create the pixel map

        for n,cell in enumerate(self.sortedcells):
          alpha = float(n)/(len(self.sortedcells) - 1) if len(self.sortedcells) > 1 else 1
          pix = cell['pix']
          pi = 0
          for py in range(self.resoY):
            for px in range(self.resoX):
              r = int(alpha*pix[pi][0] + 255*(1-alpha))
              g = int(alpha*pix[pi][1] + 255*(1-alpha))
              b = int(alpha*pix[pi][2] + 255*(1-alpha))
              hpixels[int(cell['x'] * self.resoX + px), int(cell['y'] * self.resoY + py)] = (r,g,b)
              pi += 1

        heatmap.save(filename)

    def samplePhotos(self):
        startTime = dt.datetime.now()

        images = []
        maxImages = self.imageset.getMaxImages()
        if self.verbose:
          print("Sampling %d source images..." % (maxImages))
        maxReso = max(self.resoX,self.resoY)
        for idx in range(maxImages):
            image = self.imageset.getRGBImage(idx, maxReso)
            if image == None:
                print("Bad Image!!")
            w,h = image.size
            badImage = False
            if self.noborders:

              rgb1 = image.getpixel((w/2,0))     # top center
              rgb2 = image.getpixel((w/2,h-1))   # bot center
              rgb3 = image.getpixel((0, h/2))    # left center
              rgb4 = image.getpixel((w-1, h/2))  # right center

              d1 = (rgb2[0] - rgb1[0])**2 + (rgb2[1] - rgb1[1])**2 + (rgb2[2] - rgb1[2])**2
              d1 = d1 / 255.0
              d2 = (rgb4[0] - rgb3[0])**2 + (rgb4[1] - rgb3[1])**2 + (rgb4[2] - rgb3[2])**2
              d2 = d1 / 255.0
              if d1 <= 0.007 or d2 <= 0.007 or float(w)/h >= 2 or float(h)/w >= 2:
                badImage = True
                if self.verbose:
                  print('.')

            if not badImage:
              i2 = image.resize((1,1), self.filter)
              # FIX THIS
              rgb = list(image.getdata())[0]
              # print("RGB",rgb,image.size,self.imageset.makeFilePath(idx,''))
              l = getHaeberliLuminance(rgb)
              photo = {'idx':idx, 'l':l}
              if self.hasForces:
                  photo['force'] = self.imageset.getImageForce(idx)
              images.append(photo)

            if self.verbose and (idx+1) % 500 == 0:
              print("%d..." % (idx+1))
        print("Got %d images, %.2f secs to sample" % (len(images), floatseconds(dt.datetime.now() - startTime)))

        self.images = images

    def subsamplePhoto(self,photo):
        if not('pix' in photo) or len(photo['pix']) == 0:
          photo['pix'] = []
          key = self.imageset.getImageDupeID(photo['idx'])
          if key not in self.dupeList:
            self.dupeList[ key ] = []
          for v in range(3):
            if v > 0 and not self.usevars:
                continue
            image = self.getCroppedPhoto(photo['idx'], self.resoX, v)
            # print("Resizing image to ",self.resoX,self.resoY)
            image = image.resize((self.resoX, self.resoY), self.filter)
            # !! convert to grayscale if necessary...
            if self.grayscale:
              image = image.convert('L').convert('RGB')
            pix = list(image.getdata())
            photo['pix'].append(pix)

    def getCroppedPhoto(self, idx, resoX, var):
        image = self.imageset.getRGBImage(idx,resoX)
        if not image:
          print("Problem getting image %d" % (idx))
          return None

        # crop to square
        w,h = image.size
        imgAspectRatio = float(w)/h
        if var == 0:
          if imgAspectRatio < self.tileAspectRatio:
            nh = int(w / self.tileAspectRatio)
            image = image.crop((0,(h-nh)/2,w,nh+(h-nh)/2))
          elif imgAspectRatio > self.tileAspectRatio:
            nw = int(h * self.tileAspectRatio)
            image = image.crop(((w-nw)/2,0,nw+(w-nw)/2,h))
 
        elif var == 1: # left/top
          if imgAspectRatio < self.tileAspectRatio:
            nh = int(w / self.tileAspectRatio)
            image = image.crop((0,0,w,nh))
          elif imgAspectRatio > self.tileAspectRatio:
            nw = int(h * self.tileAspectRatio)
            image = image.crop((0,0,nw,h))
 
        else: # var == 2 # right/bot
          if imgAspectRatio < self.tileAspectRatio:
            nh = int(w / self.tileAspectRatio)
            image = image.crop((0,(h-nh),w,nh+(h-nh)))
          elif imgAspectRatio > self.tileAspectRatio:
            nw = int(h * self.tileAspectRatio)
            image = image.crop(((w-nw),0,nw+(w-nw),h))

        return image
 
    def buildLumIndex(self):
        self.images = sorted(self.images, key=itemgetter('l'))
        iIndex = []
        lIdx = -1
        n = 0
        if self.verbose:
            print("Sorting %d images for luminance" % (len(self.images)))
        for j,img in enumerate(self.images):
          if int(img['l']*255) != lIdx:
            lIdx = int(img['l']*255)
            while n <= lIdx:
              iIndex.append(j)
              n += 1
        while n <= 255:
          iIndex.append(j)
          n += 1
        if self.verbose:
            print("Lumindex has %d entries" % (n))
        self.iIndex = iIndex

    def getMinDupeDist2(self, img, x, y):
        mind = 100000000
        key = self.imageset.getImageDupeID(img['idx'])
        if not (key in self.dupeList):
          return mind
        dupeCoords = self.dupeList[key]
        for dd in dupeCoords:
          dx = (dd['x'] - x) ** 2
          dy = (dd['y'] - y) ** 2
          if dx == 0:
            mind = dx
          if dy == 0:
            mind = dy
          if dx+dy < mind:
            mind = dx+dy

        return mind

    # this is where the CPU is grinding - should be optimized for speed
    def cumDiff(self, pix1, pix2, upperBound):
        # elegant but slow
        # esum = sum([(p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2 for p1,p2 in zip(pix1,pix2)])

        esum = 0
        for i in range(self.reso2):   # note using zip here is slightly slower
            esum += (pix1[i][0] - pix2[i][0]) ** 2 + (pix1[i][1] - pix2[i][1]) ** 2 + (pix1[i][2] - pix2[i][2]) ** 2
            if upperBound > 0 and esum > upperBound:
                break

        return esum

    def selectTiles(self):
        if not self.images:
            self.samplePhotos()
            if not self.images:
                return
        if not self.sortedcells:
            self.setupCells() 
            if not self.sortedcells:
                return

        numImages = len(self.images)
        lastImageIdx = numImages-1
        if self.verbose:
            print("Selecting from %d images... %d cells" % (numImages, len(self.sortedcells)) )

        self.buildLumIndex()

        i = 0
        lErr = 0
        fimages = []

        startTime = dt.datetime.now()

        maxLumErr = 0
        maxDiff = 0

        for cell in self.sortedcells:
          # puts "tile #{i} cell #{cell['x']} x #{cell['y']} " if self.verbose
          cIdx = 0
          minDiff = -1
          flop = False
          var = 0
          gotOne = False

          # this computes a number of slots based on a desired number of images which ranges from 300 to 100
          # using extra candidates for images which are earlier in the array (and edgier)

          lErr = 20 # worked this out experimentally - normal mode
          if self.draft:
              lErr = 5      # worked out experimentally
          if self.accurate:
              lErr = 40

          # add bonus here based on edginess...
          # lErr += 20 + cell['e'].to_f/self.reso2
          while not gotOne:
            ii = int(cell['l'] * 255)
            mini = self.iIndex[max(0,ii-lErr)]
            maxi = self.iIndex[min(255,ii + lErr)]
            # puts "  ii = #{ii} lErr = #{lErr} fmin-max = #{mini}-#{maxi}" if self.verbose
            if maxi - mini < 256:
              mini -= 128
              maxi += 128
            mini = max(0,mini)
            if maxi > lastImageIdx or ii+lErr >= 255:
                maxi = lastImageIdx
            # puts "  min-max = #{mini}-#{maxi}" if self.verbose

            # tried various tricks here to reorder candidates to get more bounds clipping.  didn't shorten execution time
            # see ruby...
            cands = list(range(mini,maxi+1))

            for j in cands:

              image = self.images[j]

              # also tried optimization here to no avail...
              # lumDiff = ((image['l']*255).to_i-ii).abs
              # minPossibleDiff = lumDiff == 0? 0 : (self.resoX*self.resoY*3*(lumDiff-1))+1
              # next if minDiff > 0 && minPossibleDiff > minDiff
              if 'xx' in image and image['xx']:
                continue

              if self.getMinDupeDist2(image, cell['x'], cell['y']) < self.minDupeDist2:
                continue

              # pp image
              self.subsamplePhoto(image) # subsample photo if we haven't yet

              for v in range(3 if self.usevars else 1):
                diff = self.cumDiff(image['pix'][v],cell['pix'],minDiff)

                if diff < minDiff or minDiff == -1:
                  minDiff = diff
                  cIdx = j
                  flop = False
                  var = v
                  gotOne = True

                if self.doflops:
                  diff = self.cumDiff(image['pix'][v],cell['fpix'],minDiff)
                  if diff < minDiff or minDiff == -1:
                    minDiff = diff
                    cIdx = j
                    flop = True
                    var = v
                    gotOne = True


            # if no match found, widen range
            lErr += 5


          cPhoto = self.images[cIdx]

          lumErr = abs(cPhoto['l'] - cell['l'])
          maxLumErr = max(lumErr,maxLumErr)
          maxDiff = max(minDiff,maxDiff)

          cPhoto['i'] = cell['i']
          cell['iIdx'] = len(fimages)
          cell['img'] = cPhoto
          cell['flop'] = flop
          cell['var'] = var
          cell['diff'] = minDiff
          fimages.append(cPhoto)

          # handle dupes
          cPhoto['xx'] = not self.dupesOK
          cPhoto['placed'] = True

          dupeCoords = self.dupeList[ self.imageset.getImageDupeID(cPhoto['idx']) ]
          drec = { 'x': cell['x'], 'y': cell['y'] }
          dupeCoords.append(drec)

          i += 1

          if i % 100 == 0 and self.verbose:
            print("%d..." % (i))

        # end
        print("Done selection pass, elapsed: %.2f seconds" % (floatseconds(dt.datetime.now() - startTime)))
        print("Max Lum Err: %.1f   Max Diff: %d" % (maxLumErr * 256, maxDiff))

        if self.hasForces:
          iq = [p for p in self.images if 'placed' not in p and p['force'] and 'pix' in p ]
          print("Adding %d forces" % (len(iq)))

          while len(iq) > 0:
            image = iq.pop(0)

            minDiff = -1
            cIdx = -1
        
            nbrPlacedForces = 0
            #
            for cell in self.sortedcells:
              diff = self.cumDiff(image['pix'][0],cell['pix'], minDiff)
              if ((diff < minDiff or minDiff == -1) and ((not cell['img']['force']) or diff < cell['diff'])):
                minDiff = diff
                cIdx = cell['i']
              if cell['img']['force']:
                nbrPlacedForces += 1
            
            if (cIdx == -1):
              print("No Cell match!  minDiff = %d" % (minDiff))
            else:
              cell = self.cells[cIdx] # $self->{cells}->[$cIdx];
              #       if a force photo is already there, push it to end of queue
              if cell['img']['force']:
                iq.append(cell['img'])
                print("Repush")
              #  place new photo there
              cell['img'] = image;
              cell['flop'] = False
              image['i'] = cell['i']
              cell['diff'] = minDiff

        # renumber final images here
        fimages = []
        for cell in self.cells:
          cell['iIdx'] = len(fimages)
          fimages.append(cell['img'])

        self.finalimages = fimages
        self.images = []
        self.iIndex = []
        self.sortedcells = []

    def selectTilesHMode(self):
      if not self.images:
        self.samplePhotos()
        if not self.images:
          return

      self.setupCells()
      if not self.cells:
        return

      numImages = len(self.images)
      maxImages = min(len(self.images), self.hlimit)
      nbrImagesMatched = 0

      lastImageIdx = numImages-1
      # self.buildLumIndexHMode2()  # !!! MAKE LUM INDEX FOR CELLS...

      unplacedImages = copy.copy(self.images)  # may have to use deepcopy...
      nbrPlaced = 0
      hPass = 0
      fimages = []

      while len(unplacedImages) > 0 and nbrImagesMatched < maxImages:
        hPass += 1
        print("Pass " + hPass)
        nbrUnplaced = 0
        for i in range(min(self.hlimit,len(unplacedImages))):
          print(" placing image %d" % (i))
          image = unplacedImages[i]
          if 'placed' in image:
            continue
          self.subsamplePhoto(image)
          if 'cellIdx' in image:
            cell1 = self.cells[image['cellIdx']]
            overlaps = False
            for j in range(i):
              image2 = unplacedImages[j]
              if not 'cellIdx' in image2:
                continue
              # 10% overlap check
              cell2 = self.cells[image2['cellIdx']]
              if self.cellsOverlap(cell1,cell2):
                overlaps = True
                break

            if not overlaps:
              fimages.append(image)
              image['placed'] = True
              print("Placed an image")
              nbrImagesMatched += 1
              if nbrImagesMatched >= maxImages:
                break
              cell1 = self.cells[image['cellIdx']]
              for cell2 in self.cells:
                if self.cellsOverlap(cell1,cell2):
                  cell2['used'] = True

              continue
            else:
              print("Image %d overlaps, replacing" % (i))

          nbrUnplaced += 1
          minDiff = -1
          gotOne = False
          for ucrec in self.cells:
            diff = self.cumDiff(image['pix'][0],ucrec['pix'],minDiff)
            if diff < minDiff:
              minDiff = diff
              cIdx = ucrec['i']
              flop = False
              var = 0
              gotOne = True

          if gotOne:
            image['cellIdx'] = cIdx
            image['cDist'] = minDiff

        # sort images so that better matches are first
        unplacedImages = sorted( unplacedImages, key=itemgetter('cDist'))

      # sort images so that better matches render last
      fimages =  sorted(fimages, key=itemgetter('cDist'), reverse=True)
      self.finalimages = fimages
      self.images = []
      self.iIndex = []

    def cellsOverlap(self, cell1,cell2):
      x1 = cell1['x']
      y1 = cell1['y']
      x2 = cell2['x']
      y2 = cell2['y']
      w = self.resoX
      h = self.resoY
      return not(x1 >= x2 + self.resoX or x1 + self.resoX <= x2 or y1 >= y2 + self.resoY or y1 + self.resoY <= y2)


    def loadData(self):
        loadfilename = "%s/%s_%s_mosaick.json" % (self.json_path,self.rootname, self.basename)

        sdata = json.loads(open(loadfilename).read())

        self.basepic = sdata['basepic']

        self.hcells = sdata['hcells']
        self.vcells = sdata['vcells']
        self.tileAspectRatio = sdata['tileAspectRatio']
        self.targetAspectRatio = sdata['targetAspectRatio']
        self.cells = sdata['cells']

        # for cell in sdata['cells']:
        #     self.cells.append( {'x': cell['x'],
        #                         'y': cell['y'],
        #                         'iIdx': cell['iIdx'],
        #                         'var': cell['var'],
        #                         'avg':     cell['avg'],
        #                         'flop': cell['flop'] })
        self.finalimages = []
        for img in sdata['finalimages']:
            self.finalimages.append({ 'idx': img['idx'], 'desc': img['desc'] })

    def saveData(self):
        sdata = { 'basepic': self.basepic,
                  'hcells': self.hcells,
                  'vcells': self.vcells,
                  'tileAspectRatio': self.tileAspectRatio,
                  'targetAspectRatio': self.targetAspectRatio,
                  'cells': [],
                  'finalimages': [] }

        sdata['cells'] = [{'x': cell['x'],
                           'y':     cell['y'],
                           'iIdx':  cell['iIdx'],
                           'var':   cell['var'],
                           'avg':     cell['avg'],
                           'flop':  cell['flop']} for cell in self.cells]

        for img in self.finalimages:
          sdata['finalimages'].append({'idx':img['idx'],'desc':self.imageset.getImageDesc(img['idx']) })

        savefilename = "%s/%s_%s_mosaick.json" % (self.json_path, self.rootname, self.basename)
        open(savefilename, "w").write(json.dumps(sdata, indent=4))

    def makeMosaic(self):
        print("Making mosaic")
        if not self.finalimages:
          if self.load:
            self.loadData()
          elif self.hmode:
            self.selectTilesHMode()
          else:
            self.selectTiles()
          if len(self.finalimages) == 0:
              return
          if not self.hmode:
            self.saveData()

        if not self.cellsize:
          if not self.minWidth or not self.minHeight:
            print("No output dimension defined")
            return
          print("No explicit cellsize defined")
          outputAspectRatio = self.minWidth / float(self.minHeight)
          if self.targetAspectRatio < outputAspectRatio:
            self.cellsize = int(self.minHeight / self.vcells / self.tileAspectRatio)
          else:
            self.cellsize = int(self.minWidth / self.hcells)
          if self.hcells * self.cellsize < self.minWidth:
            self.cellsize += 1 
          if self.vcells * int(self.cellsize * self.tileAspectRatio+0.5) < self.minWidth:
            self.cellsize += 1 

        if self.filename == '':
            self.filename = "%s/%s_%s_%d_x_%d_c%d%s.jpg" % (self.render_path, self.rootname, self.basename, self.hcells, self.vcells, self.cellsize,"_gray" if self.grayscale else "")
        self.pngname = re.sub(r'\.\w+$', '.png', self.filename)
        self.width = self.cellsize * self.hcells
        self.height = (self.cellsize / self.tileAspectRatio) * self.vcells
        cellsizeX = int(self.width / self.hcells + 0.5)
        cellsizeY = int(self.height / self.vcells + 0.5)
        width = cellsizeX * self.hcells
        height = cellsizeY * self.vcells
        if self.verbose:
            print("Image Dimensions will be %d x %d (tiles = %dx%d pixels)" % (width, height, cellsizeX, cellsizeY))
        maxCellsize = max(cellsizeX,cellsizeY)
        # htmlName = re.sub(r'\.jpg', '.html', self.filename)

        mosaic = Image.new("RGB", (width, height), "black")
        draw = ImageDraw.Draw(mosaic)

        # markup = ''
        # markup += "<img src=\"%s\" usemap=\"#mozmap\" border=0>\n" % (self.filename)
        # markup +="<map name=\"mozmap\">\n";

        if not self.hmode:
          for cell in self.cells:
            imgdat = self.finalimages[cell['iIdx']]
            x = cell['x']
            y = cell['y']
            img = self.getCroppedPhoto(imgdat['idx'], maxCellsize, cell['var'])
            img = img.resize((cellsizeX, cellsizeY), self.filter)

            if cell['flop'] and self.doflops:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)

            if self.mixin > 0 and self.tint:  # !! this causes the paste to break
              mask = Image.new("L",(cellsizeX,cellsizeY),int(self.mixin*255/100))
              tint = Image.new("RGB", (cellsizeX, cellsizeY), tuple(cell['avg']))
              img.paste(tint,(0,0),mask)

            mosaic.paste(img, (x*cellsizeX,y*cellsizeY))

            # markup += "<AREA SHAPE=rect COORDS=\"%d,%d,%d,%d\" href=\"%s\" TITLE=\"%s\">\n" % (
            #            x*cellsizeX,y*cellsizeY,(x+1)*cellsizeX,(y+1)*cellsizeY,
            #            self.imageset.getImageWebpage(imgdat['idx']),
            #            self.imageset.getImageDesc(imgdat['idx']) )

            # perform annotations
            if self.anno:
              # text = Magick::Draw.new
              pointsize = int(cellsizeX * 0.33)
              pointsize = max(9,pointsize)
              label = '%c%d' % (65+x,y+1)
              draw.text((x*cellsizeX+1,y*cellsizeY+1),label,(255,255,255))
        else:
          # !! HMODE IN DEVELOPMENT - images are allowed to overlap
          if self.hbase != '':
            mosaic = Image.load(self.hbase).resize((width, height))
            draw = ImageDraw.Draw(mosaic)
          for i,imgdat in enumerate(self.finalimages):
            cell = self.cells[imgdat['cellIdx']]
            x = cell['x']
            y = cell['y']
            # markup += "<AREA SHAPE=rect COORDS=\"%d,%d,%d,%d\" href=\"%s\" TITLE=\"%s\">\n" % (
            #            x*cellsizeX,y*cellsizeY,(x+1)*cellsizeX,(y+1)*cellsizeY,
            #            self.imageset.getImageWebpage(imgdat['idx']),
            #            self.imageset.getImageDesc(imgdat['idx']) )

            img = self.getCroppedPhoto(imgdat['idx'], maxCellsize, cell['var'])
            img = img.resize((cellsizeX,cellsizeY))
            if cell['flop'] and self.doflops:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            mosaic.paste(img, (x*cellsizeX/self.resoX,y*cellsizeY/self.resoY, x*cellsizeX/self.resoX+cellsizeX, y*cellsizeY/self.resoY+cellsizeY))
            # mosaic.composite!(img,x*cellsizeX/self.resoX,y*cellsizeY/self.resoY,Magick::OverCompositeOp)

        # markup += '</map>'

        # output markup to file here...
        # open(htmlName, "w").write(markup)

        if self.mixin > 0 and not self.tint:
          print("Mixing in %d%%..." % (self.mixin))
          bgpic = Image.open(self.basepic).resize((width, height), self.filter)
          mask = Image.new("L",(width,height),int(self.mixin*255/100))
          mosaic.paste(bgpic,(0,0),mask)

        if self.grayscale:
          mosaic = mosaic.convert("L")

        if self.png:
            mosaic.save(self.pngname)
          
        if self.verbose:
            print("Saving JPEG %s" % (self.filename))
        mosaic.save(self.filename, quality=self.quality)

def floatseconds(dt):
    return (dt.seconds*1000000 + dt.microseconds)/1000000.0

# Utilities
def getHaeberliLuminance(rgb):
    return (0.3086*rgb[0]+ 0.6094*rgb[1] + 0.0820*rgb[2])/255.0 # Haeberli luminance calc

def RGBtoHSV(rgb):
    r = rgb[0] / 255.0
    g = rgb[1] / 255.0
    b = rgb[2] / 255.0
    mx = max(r,g,b)
    mn = min(r,g,b)
    v = mx
    s = (mx-mn)/mx if (mx != 0) else 0
    h = 0
    if s != 0:
      d = mx - mn
      if r == mx:
        h = (g - b)/d
      elif g == mx:
        h = 2 + (b-r)/d
      elif b == mx:
        h = 4 + (r-g)/d
      h *= 60
      if (h < 0):
        h += 360
    return (h/360,s,v)

