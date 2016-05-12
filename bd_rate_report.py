#!/usr/bin/env python3

from numpy import *
from scipy import *
from scipy.interpolate import interp1d
from scipy.interpolate import pchip
import sys
import argparse
import json

parser = argparse.ArgumentParser(description='Produce bd-rate report')
parser.add_argument('run',nargs=2,help='Run folders to compare')
parser.add_argument('anchor',nargs=1,help='Folder to find anchor runs')
args = parser.parse_args()

met_name = ['PSNR', 'PSNRHVS', 'SSIM', 'FASTSSIM', 'CIEDE2000'];

def bdrate(file1, file2, anchorfile):
    anchor = flipud(loadtxt(anchorfile));
    a = flipud(loadtxt(file1));
    b = flipud(loadtxt(file2));
    rates = [0.06,0.2];
    ra = a[:,2]*8./a[:,1]
    rb = b[:,2]*8./b[:,1]
    interp_type = 'linear';    #only used for integration (pchip is used for metric interpolation)
    bdr = zeros((4,4))
    ret = {}
    for m in range(0,5):
        ya = a[:,3+m];
        yb = b[:,3+m];
        yr = anchor[:,3+m];
        try:
            #p0 = interp1d(ra, ya, interp_type)(rates[0]);
            #p1 = interp1d(ra, ya, interp_type)(rates[1]);
            p0 = yr[0];
            p1 = yr[1];
            log_ra_interp = arange(log(ra[0]),log(ra[-1]),0.001)
            ya_interp = pchip(log(ra), ya)(log_ra_interp)
            log_rb_interp = arange(log(rb[0]),log(rb[-1]),0.001)
            yb_interp = pchip(log(rb), yb)(log_rb_interp)
            a_rate = interp1d(ya_interp, log_ra_interp, interp_type)(arange(p0,p1,0.01));
            b_rate = interp1d(yb_interp, log_rb_interp, interp_type)(arange(p0,p1,0.01));
            if not len(a_rate) or not len(b_rate):
                bdr = NaN;
            else:
                bdr=100 * (exp(mean(b_rate-a_rate))-1);
        except ValueError:
            bdr = NaN;
        except linalg.linalg.LinAlgError:
            bdr = NaN;
        ret[m] = bdr
    return ret


info_data = {}
info_data[0] = json.load(open(args.run[0]+'/info.json'))
info_data[1] = json.load(open(args.run[1]+'/info.json'))

if info_data[0]['task'] != info_data[1]['task']:
    print("Runs do not match.")
    sys.exit(1)

task = info_data[0]['task']

sets = json.load(open("rd_tool/sets.json"))
videos = sets[task]["sources"]

info_data[2] = json.load(open(args.anchor[0]+'/'+sets[task]['anchor']+'/info.json'))

if info_data[2]['task'] != info_data[0]['task']:
    print("Mismatched anchor data!")
    sys.exit(1)

metric_data = {}
for video in videos:
    metric_data[video] = bdrate(args.run[0]+'/'+task+'/'+video+'-daala.out',args.run[1]+'/'+task+'/'+video+'-daala.out',args.anchor[0]+'/'+sets[task]['anchor']+'/'+task+'/'+video+'-daala.out')

print("AWCY Report v0.3")
print('Reference: ' + info_data[0]['run_id'])
print('Test Run: ' + info_data[1]['run_id'])
print('Range: Anchor ' + info_data[2]['run_id'] + ' q range 20-50')
avg = {}
for m in range(0,len(met_name)):
    avg[m] = mean([metric_data[x][m] for x in metric_data])
    print("%10s: %9.2f" % (met_name[m], avg[m]))
print()
print("%40s %9s %9s %9s %9s %9s" % ('file','PSNR','SSIM','PSNRHVS','FASTSSIM','CIEDE2000'))
print('------------------------------------------------------------------------------------------')
for video in sorted(metric_data):
    metric = metric_data[video]
    print("%40s %9.2f %9.2f %9.2f %9.2f %9.2f" % (video, metric[0], metric[1], metric[2], metric[3], metric[4]))
print('------------------------------------------------------------------------------------------')
print("%40s %9.2f %9.2f %9.2f %9.2f %9.2f" % ('Average', avg[0], avg[1], avg[2], avg[3], avg[4]))
