# get_desired_bins

import os, subprocess, argparse
from mosaic_constants import bdata_path

parser = argparse.ArgumentParser(description='Fetch bin files from quickdraw repository')
parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Verbose')
parser.add_argument('-vv', '--vverbose', default=False, action='store_true', help='Very Verbose')
parser.add_argument('-t', '--test', default=False, action='store_true', help='Test - no actual commands are run')
parser.add_argument('-b', '--bin', help="Extra bin to grab")
args = parser.parse_args()


# browse available bins
# https://console.cloud.google.com/storage/browser/quickdraw_dataset/full/binary

desired_bins = ['flower','skull','hurricane','flying saucer','zigzag','bird','cat','dog',
	            'paper clip','sheep','star','wheel','animal migration','ocean']
if args.bin:
	desired_bins.append(args.bin)

def do_command(cmd):
	print cmd
	if not args.test:
		subprocess.check_call(cmd, shell=True)


for dbin in desired_bins:
	ifilename = dbin.replace(' ','\\ ') + ".bin"
	ofilename = bdata_path + '/' + dbin.replace(' ','_') + '.bin'
	if os.path.exists(ofilename):
		continue
	cmd = 'gsutil -m cp gs://quickdraw_dataset/full/binary/%s %s' % (ifilename, ofilename)
	do_command(cmd)
