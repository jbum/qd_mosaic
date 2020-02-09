import json
import argparse
import sys, os, glob


parser = argparse.ArgumentParser(description='List pictures in a directory')
parser.add_argument('dir', help='Name of directory to scan')
parser.add_argument('-f', '--force', default=False, action='store_true', help='Set force flags to true')
parser.add_argument('-o', '--ofile', default='untitled.txt', help='output file (default=untitled.txt')
args = parser.parse_args()


photos = []
for f in os.listdir(args.dir):
    if f.endswith(".png") or f.endswith(".jpg"):
        print args.dir + f
        photos.append({"force":True if args.force or f[0] == 'F' else False,"id":args.dir+f,"path":args.dir + f})


       # "isfamily": "0", 
       #  "title": "Black And White", 
       #  "farm": "4", 
       #  "ispublic": "1", 
       #  "server": "3753", 
       #  "isfriend": "0", 
       #  "secret": "210deefa79", 
       #  "owner": "32289743@N03", 
       #  "id": "18899060156"


text_file = open(args.ofile, "w")
text_file.write(json.dumps(photos, indent=4))
text_file.close()

print "Wrote %d records to %s" % (len(photos), args.ofile)
