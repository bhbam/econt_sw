import time
import argparse
import csv
import numpy as np
from set_econt import set_runbit, startup, set_fpga
from i2c import I2C_Client
i2cClient=I2C_Client(forceLocal=1)
from utils.asic_signals import ASICSignals
from utils.io import IOBlock
resets = ASICSignals()
"""resets.send_reset(reset='hard',i2c='ASIC')
resets.send_reset(reset='hard',i2c='emulator')
startup()
set_fpga()"""
"""
Delay scan on IO blocks.

Usage:
   python testing/delay_scan.py --io from
"""

def consecutive(data, stepsize=1):
    return np.split(data, np.where(np.diff(data) != stepsize)[0]+1)



def get_phase_width(err_counts):
    max_width_by_ch = []
    for ch in range(13):
        x = np.transpose(err_counts[ch])
        phases = consecutive(np.argwhere(x==0).flatten())
        sizes = [np.size(a) for a in phases]
        remove_indexs = []
        remove_sizes=[]
        try:
            for l in phases:
                if l[0]==1 or l[-1]==62:
                    indices = [i for i, arr in enumerate(phases) if np.array_equal(arr, l)]
                    remove_indexs.append(indices[0])
                    remove_sizes.append(sizes[indices[0]])
            for i in remove_sizes:
                sizes.remove(i)
            max_width = np.max(sizes)
        except:
            max_width = 0
        max_width_by_ch.append(max_width)
    return max_width_by_ch



def get_max_width(err_counts, channels, padding): # channels 12 for phase scan and 13 for io_scan || padding 4
    max_width_by_ch = []
    seco =nd_max_width_by_ch []
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
for i in range(3):
   set_runbit(0)
   i2cClient.call(args_yaml="configs/alignOutput_TS.yaml",args_i2c='ASIC,emulator',args_write=True)
   set_runbit(1)

   resets.send_reset(reset='hard',i2c='ASIC')
   resets.send_reset(reset='hard',i2c='emulator')
   startup()
   set_fpga()
   set_runbit(0)
   i2cClient.call(args_yaml="configs/alignOutput_TS.yaml",args_i2c='ASIC,emulator',args_write=True)
   set_runbit(1)
   _,errorcounts = delay_scan('delay_scan_data_chip_270', 'from',i)
   #print(errorcounts)
   err_counts_io = list(errorcounts.values())
   #print(err_counts_io)
   max_width_io =  get_phase_width(err_counts_io)
   #max_width_io = get_max_width(err_counts_io,13,10)
   print(">>>>>>>>>>>>>>>>>>>>Run>>>>>>>>>>>>>>>>> ", i)
   print("Max width:  ",  max_width_io)
   max_IO_delay = np.array([14] * 13)
   if (max_width_io >= max_IO_delay).all():
      print("Pass")
   else:
      print("Fail")
   #print(err_counts_io)
