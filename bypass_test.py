from set_econt import output_align
from i2c import I2C_Client
from PowerSupplyControls import Agilent3648A
import os, sys, time, logging
ps=Agilent3648A(host="192.168.1.50",addr=8) # This is for 48
i2cClient=I2C_Client(forceLocal=1)
out_dir='data'
chip=9990
odir = f"{out_dir}/chip_{chip}"
if os.path.exists(f'{odir}'):
    os.system(f'rm -r {odir}')
os.system(f'mkdir -p {odir}')
tag=f"chip_{chip}"

logName=f"{odir}/logFile_{tag}.log"
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - {_tag} - %(levelname)-6s %(message)s'.format(_tag=tag),
                    datefmt='%m-%d-%y %H:%M:%S',
                    filename=logName,
                    filemode='a')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# console.setLevel(logging.DEBUG)
_f='%(asctime)s - {_tag} - %(levelname)-6s %(message)s'.format(_tag=tag)
console.setFormatter(logging.Formatter(_f))
logging.getLogger().addHandler(console)

ps.SetLimits_1(v=1.2,i=0.6)
ps.TurnOn()
time.sleep(1)
real_voltage = ps.ReadPower_1()

logging.info("Outputting word alignment")
error_counts = output_align(verbose=0,outdir=odir, chip_number=chip)
if error_counts == 0:
  output_alignment_test = 1
  logging.info("output word alignment test passed <<<")
else:
  output_alignment_test = 0
  logging.warning("output word alignment test failed !!!")
logging.info('\n')
logging.getLogger().handlers.clear()
