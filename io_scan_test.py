
from set_econt import set_runbit
from i2c import I2C_Client
from delay_scan import delay_scan
import numpy as np
import sys,copy
import logging
import datetime
import os, time, datetime
i2cClient=I2C_Client(forceLocal=1)
for chip in range(20):



    odir = f"data/chip_{chip}"
    os.system(f'mkdir -p {odir}')
    tag=f"chip_{chip}"


    # os.system(f'mkdir -p {odir}')


    logName=f"{odir}/logFile_{tag}.log"
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - {_tag} - %(levelname)-6s %(message)s'.format(_tag=tag),
                        datefmt='%m-%d-%y %H:%M:%S',
                        filename=logName,
                        filemode='a')
    console = logging.StreamHandler()
    # console.setLevel(logging.INFO)
    console.setLevel(logging.DEBUG)
    _f='%(asctime)s - {_tag} - %(levelname)-6s %(message)s'.format(_tag=tag)
    console.setFormatter(logging.Formatter(_f))
    logging.getLogger().addHandler(console)


    logging.info('from IO delay scan')
    try:
        set_runbit(0)
        i2cClient.call(args_yaml="configs/alignOutput_TS.yaml",args_i2c='ASIC,emulator',args_write=1)
        set_runbit(1)
        logging.debug(f"Configured ASIC/emulator with all eTx")
        # errorcounts = delay_scan(odir,ioType='from',tag=tag)
        # err_counts_io = list(errorcounts.values())

    except:

        logging.warning(f"Phase width test at eTx is incomplete ???")

    logging.getLogger().handlers.clear()
