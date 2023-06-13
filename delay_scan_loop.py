import time
import argparse
import csv
from utils.io import IOBlock
import numpy as np
from set_econt import startup,set_runbit,read_status,set_fpga,output_align
from i2c import I2C_Client
i2cClient=I2C_Client(forceLocal=1)


def consecutive(data, stepsize=1):
    return np.split(data, np.where(np.diff(data) != stepsize)[0]+1)

def get_max_width(err_counts, channels, padding): # channels 12 for phase scan and 13 for io_scan || padding 4
    max_width_by_ch = []
    second_max_width_by_ch = []
    err_wrapped=np.concatenate([err_counts,err_counts[:padding]])
    for ch in range(channels):
        if channels == 13:
            x = err_wrapped[ch,:]
        else:
            x = err_wrapped[:,ch]
        phases = consecutive(np.argwhere(x==0).flatten())
        sizes = [np.size(a) for a in phases]
        max_width = max(sizes)
        sizes.remove(max_width)
        try:
            second_max_width = max(sizes)
        except:
            second_max_width = 0
        max_width_by_ch.append(max_width)
        second_max_width_by_ch.append(second_max_width)
    return max_width_by_ch, second_max_width_by_ch




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
        with open(f'{odir}/{ioType}_io_delayscan{tag}.csv','w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow([f'CH_{ch}' for ch in errorcounts.keys()])
            for j in range(len(errorcounts[0])):
                writer.writerow([errorcounts[key][j] for key in errorcounts.keys()])
    return errorcounts



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--io', type=str, default='from', help='IO block name')
    parser.add_argument('--odir', type=str, default='./', help='output dir')
    args = parser.parse_args()
    # startup()
    # set_fpga()
    # set_runbit(0)
    # i2cClient.call(args_yaml="configs/alignOutput_TS.yaml",args_i2c='ASIC,emulator',args_write=1)
    # set_runbit(1)
    for chip in range(10):


        print(f">>>>>>>>>>>Test for chip_{chip}>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        errorcounts = delay_scan(args.odir,args.io)
        # errorcounts = delay_scan(odir,ioType='from',tag=tag)
        err_counts_io = list(errorcounts.values())
        print("Error counts form IO delay scan: %s"%err_counts_io)
        max_width_io, second_max_width_io =  get_max_width(err_counts_io, channels=13, padding=10)
        print(f" Max width of io-scan settings {max_width_io}")
        print(f" Second Max width of io-scan settings {second_max_width_io}")
        max_IO_delay = np.array([12] * 13)
        second_max_IO_delay = np.array([11] * 13)
        if ((max_width_io >= max_IO_delay).all() and (second_max_width_io >= second_max_IO_delay).all()):
            io_scan_test = 1
            print(f"Phase width test at eTx passed <<<")
        else:
            io_scan_test = 0
            print(f"Phase width test at eTx failed !!!")

        # print("Outputting word alignment---------------------------------------------")
        # error_counts = output_align(verbose=0,outdir=args.odir, chip_number=chip)
        # if error_counts == 0:
        #     output_alignment_test = 1
        #     print("output word alignment test passed <<<")
        # else:
        #     output_alignment_test = 0
        #     print("output word alignment test failed !!!")
