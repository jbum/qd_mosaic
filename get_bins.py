# get_desired_bins

import os, subprocess, argparse
from mosaic_constants import bdata_path

parser = argparse.ArgumentParser(description='Fetch bin files from quickdraw repository')
parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Verbose')
parser.add_argument('-vv', '--vverbose', default=False, action='store_true', help='Very Verbose')
parser.add_argument('-t', '--test', default=False, action='store_true', help='Test - no actual commands are run')
parser.add_argument('bins', nargs='+', help="Bin(s) to grab, example: bird")
args = parser.parse_args()

# browse available bins
# https://console.cloud.google.com/storage/browser/quickdraw_dataset/full/binary

def do_command(cmd):
	print cmd
	if not args.test:
		subprocess.check_call(cmd, shell=True)


for dbin in args.bins:
	print "Getting",dbin
	ifilename = dbin.replace(' ','\\ ') + ".bin"
	ofilename = bdata_path + '/' + dbin.replace(' ','_') + '.bin'
	if os.path.exists(ofilename):
		continue
	cmd = 'gsutil -m cp gs://quickdraw_dataset/full/binary/%s %s' % (ifilename, ofilename)
	do_command(cmd)
