from PIL import Image
import sys, os, subprocess, json

# generic ImageSet class (consider using abc [abstract base class library] for this)
class ImageSet:
    # These need to be implemented by sub-classes   
    def makeFilePath(self, idx, minWidth):
        print("ABSTRACT makeFilePath")
        return ""

    def getImage(self, idx, minWidth):
        print("ABSTRACT getImage")

    def getRGBImage(self, idx, minWidth):
        img = self.getImage(idx, minWidth)
        return img.convert("RGB")

    def getImageWebpage(self, idx):
        print("ABSTRACT getImageWebpage")
        return ""

    def getImageDesc(self, idx):
        return "Image %d" % (idx)

    def getImageDupeID(self, idx):
        print("ABSTRACT getImageDupeID")
        return idx

    def getImageID(self, idx):
        print("ABSTRACT getImageID")
        return idx

    def getMaxImages(self):
        print("ABSTRACT getMaxImages")
        return 0

    def getImageForce(self, idx):
        return None

# photolist from file of pathnames
# optional CACHEROOT at top, and additional fields via tsv syntax - see disneyland.txt
# second field is URL, so we can support optional downloads

class ListSet(ImageSet):
    # These need to be implemented by sub-classes   
    def __init__(self, params):
        self.filename = params.get('filename', '')
        self.downloadsOK = params.get('downloadsOK', False)
        self.verbose = params.get('verbose', True)
        self.cacheRoot = params.get('cacheRoot', '')
        self.photopaths = []
        self.urls = []
        text = open(self.filename).read()
        for line in text.split("\n"):
          if line == '':
            continue
          if line[:10] == 'CACHEROOT:':
            self.cacheRoot = line[10:]
          else:
            tokens = line.split("\t")
            self.photopaths.append(tokens[0])
            if len(tokens) > 1:
                self.urls.append(tokens[1])
            else:
                self.urls.append('')

    def makeFilePath(self, idx, minWidth):
        return self.cacheRoot + self.photopaths[idx]

    def getImage(self, idx, minWidth):
        try:
          return Image.open(self.makeFilePath(idx, minWidth))
        except IOError:
          print("Image not found: %s" % (self.makeFilePath(idx, minWidth)))
          if (self.cacheRoot == ''):
            print(" (consider supplying -cacheroot)")
          sys.exit()

    def getImageDesc(self, idx):
        return self.photopaths[idx]

    def getImageWebpage(self, idx):
        return self.urls[idx]

    def getImageDupeID(self, idx):
        return idx

    def getImageID(self, idx):
        return idx

    def getMaxImages(self):
        return len(self.photopaths)

# FlickrSet class (subclass of ImageSet) for handling sets of Flickr images
class FlickrSet(ImageSet):
    def __init__(self, params):
        self.filename = params.get('filename', '')
        self.photos = json.loads(open(self.filename).read())
        self.downloadsOK = params.get('downloadsOK', False)
        self.verbose = params.get('verbose', True)
        self.dupeOwnersOK = params.get('dupeOwnersOK', False)
        self.cacheRoot = params.get('cacheRoot', '')
        if self.cacheRoot == '':
            self.cacheRoot = 'flickrcache/'

    def getMaxImages(self):
        return len(self.photos)

    def makeFilePath(self, idx, minWidth):
        suffix = '_t' if minWidth <= 50 else ''
        if idx >= len(self.photos):
            print("idx %d not in photos len=%d" % (idx,len(self.photos)))
            return ''
        return self.makeLocalPath(self.photos[idx], suffix)

    def getImage(self, idx, minWidth):
        fname = self.makeFilePath(idx, minWidth)
        # print("getImage: " + fname)
        if fname == '':
            return None
        if (not os.path.exists(fname) or os.path.getsize(fname) < 50) and self.downloadsOK:
          if os.path.exists(fname):
            print("Image %s seems small at %d bytes" % (fname, os.path.getsize(fname)))
          self.downloadImage(idx, minWidth)
        if not os.path.exists(fname):
            print("DID NOT DOWNLOAD, downloadsOK = " + self.downloadsOK)
            return None
        return Image.open(fname)

    def getImageWebpage(self, idx):
        photo = self.photos[idx]
        if 'path' in photo:
            return 'file:///Users/jbum/Development/jbum_projects/graphics/pymosaics/%s' % (photo['path']);
        elif 'owner' in photo:
            return 'http://www.flickr.com/photos/%s/%s/' % (photo['owner'], photo['id']);
        else:
            return ''

    def getImageDesc(self, idx):
        photo = self.photos[idx]
        return 'Photo %s -- click to view' % (photo['id'])

    def getImageDupeID(self, idx):
        photo = self.photos[idx]
        if self.dupeOwnersOK:
          return photo['id']
        else:
          return photo['owner']

    def getImageID(self, idx):
        photo = self.photos[idx]
        return photo['id']

    def getImageForce(self, idx):
        photo = self.photos[idx]
        if 'force' in photo:
            return photo['force']
        else:
            return False

    # LOCAL
    def makeLocalPath(self, photo, suffix):
        if 'path' in photo:
            return photo['path']
        else:
            return self.makeDirName(photo['id']) + photo['id'] + suffix + ".jpg"

    def makeFlickrPath(self, photo, suffix):
        return "http://farm%s.static.flickr.com/%s/%s_%s%s.jpg" % (
                photo['farm'],photo['server'],photo['id'],photo['secret'],suffix)

    def makeDirName(self, id):
        iid = int(id)
        return self.cacheRoot + '%03d/%03d/' % ( (iid/1000000)%1000, (iid/1000)%1000 )

    def makeURL(self, idx, minWidth):
        suffix = '_t' if minWidth <= 50 else ''
        if idx >= len(self.photos):
            return ''
        return self.makeFlickrPath(self.photos[idx], suffix)

    def buildDirs(self, lname):
      dirs = lname.split('/')
      dirs.pop()
      ldir = ''
      for d in dirs:
        if '.jpg' in d:
          break
        if ldir != '':
          ldir += '/'
        ldir += d
        if not os.path.exists(ldir):
          os.mkdir(ldir)

    def downloadImage(self, idx, minWidth):
        r_path = self.makeURL(idx, minWidth)
        l_path = self.makeFilePath(idx, minWidth)
        self.buildDirs(l_path)
        if self.verbose:
            print("Downloading %s --> %s" % (r_path, l_path))
        f = open(l_path,"wb")
        subprocess.call(['curl', '-s', r_path], stdout=f)
        f.close()