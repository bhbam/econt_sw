import time
import argparse
import csv

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
_,error = delay_scan('delay_scan_data_chip_325', 'from',0)
print(error)
    
