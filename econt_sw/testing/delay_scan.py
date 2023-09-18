import time
import argparse
import csv

#import logging
#logging.basicConfig()
#logger = logging.getLogger("delayScan")
#logger.setLevel('INFO')
    
from utils.io import IOBlock

"""
Delay scan on IO blocks.

Usage:
   python testing/delay_scan.py --io from
"""

def delay_scan(odir,ioType='from',tag=''):
    io = IOBlock(ioType,'IO')
    io.configure_IO(invert=True)
    bitcounts,errorcounts = io.delay_scan(verbose=False)
    
    if not odir is None:
        import os
        os.system(f'mkdir -p {odir}')
        with open(f'{odir}/{ioType}_io_delayscan_errorcounts{tag}.csv','w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow([f'CH_{ch}' for ch in errorcounts.keys()])
            for j in range(len(errorcounts[0])):
                writer.writerow([errorcounts[key][j] for key in errorcounts.keys()])
        with open(f'{odir}/{ioType}_io_delayscan_bitcounts{tag}.csv','w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow([f'CH_{ch}' for ch in bitcounts.keys()])
            for j in range(len(bitcounts[0])):
                writer.writerow([bitcounts[key][j] for key in bitcounts.keys()])
    return bitcounts, errorcounts

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--io', type=str, default='from', help='IO block name')
    parser.add_argument('--odir', type=str, default='./', help='output dir') 
    args = parser.parse_args()

    x=delay_scan(args.odir,args.io)
    print(x)
