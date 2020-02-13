# mix_thumbs.py
#
# catenate multiple thumbs into one set
#
import subprocess, argparse

from mosaic_constants import set_path

parser = argparse.ArgumentParser(description='Catenate sets')
parser.add_argument('-v', '--verbose', default=False, action='store_true', help='Verbose')
parser.add_argument('-vv', '--vverbose', default=False, action='store_true', help='Very Verbose')
parser.add_argument('-t', '--test', default=False, action='store_true', help='Test - no actual commands are run')
parser.add_argument('-n', '--nbr', type=int, help='Max to use of each set (default produces a set of roughly 20000)')
parser.add_argument('-o', '--opath', help='output path')
parser.add_argument('sets', nargs='+', help='Sets to use (e.g. zizzag line etc)')
args = parser.parse_args()

if args.nbr == None:
	args.nbr = 1 + 20000 // len(args.sets)

def do_command(cmd):
	print(cmd)
	if not args.test:
		subprocess.check_call(cmd, shell=True)

newsetnom = '_'.join([nom.replace(set_path + '/','').replace('.txt','') for nom in args.sets])
if args.opath == None:
	args.opath = set_path + '/' + newsetnom + '.txt'
print(">> " + args.opath)

for i,nom in enumerate(args.sets):
	nom.replace(set_path + '/','').replace('.txt','')
	ipath = set_path + '/' + nom + '.txt'
	if args.nbr:
		cmdprefix = "head -%d" % (args.nbr)
	else:
		cmdprefix = "cat"
	cmd = "%s %s >%s%s" % (cmdprefix, ipath, '>' if i > 0 else '', args.opath)
	do_command(cmd)
