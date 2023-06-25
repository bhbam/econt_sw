import numpy as np
from i2c import I2C_Client
from PowerSupplyControls import Agilent3648A
import csv,argparse,os,pickle,pprint,time,datetime,sys,copy,logging,sqlite3,socket
from sqlite3_database import create_database, add_many_column, show_all_plan
from qc_finaltest import econt_qc

ps=Agilent3648A(host="192.168.1.50",addr=8)
i2cClient=I2C_Client(forceLocal=1)

parser = argparse.ArgumentParser()
parser.add_argument('--chip', '-c', type=int, default=9999, help='Chip number')
parser.add_argument('--odir', '-o', type=str, default='data', help='output dir')
parser.add_argument('--database', '-d', type=str, default='Econt_database', help='Chip number')
args = parser.parse_args()
chip = args.chip
out_dir = args.odir
database = args.database

pll_th = 14
max_eRx_th = 4
sec_max_eRx_th = 3
max_eTx_th = 14
sec_max_eTx_th = 12

start_ = datetime.datetime.now()
test_start_time  = start_.strftime("%Y-%m-%d_%H:%M:%S")
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
voltage = real_voltage[1]
current = real_voltage[2]
np.savetxt(f"{odir}/power_voltage_current_{tag}.txt", np.array([real_voltage]), delimiter=" ", fmt="%s", header="")
logging.info(f"power status, voltage and current  to chip : {real_voltage[0]},  {real_voltage[1]}, {real_voltage[2]}")

voltage, current, over_all_test, rw_test, pll_test, phase_width_test, input_word_alignment_test, io_scan_test, output_alignment_test, alignment_bypass_test, comparing_various_config_test, track_mode_test,pll_width,eRx_0,eRx_1,eRx_2,eRx_3,eRx_4,eRx_5,eRx_6,eRx_7,eRx_8,eRx_9,eRx_10,eRx_11,eRx2_0,eRx2_1,eRx2_2,eRx2_3,eRx2_4,eRx2_5,eRx2_6,eRx2_7,eRx2_8,eRx2_9,eRx2_10,eRx2_11,eTx_0,eTx_1,eTx_2,eTx_3,eTx_4,eTx_5,eTx_6,eTx_7,eTx_8,eTx_9,eTx_10,eTx_11,eTx_12,eTx2_0,eTx2_1,eTx2_2,eTx2_3,eTx2_4,eTx2_5,eTx2_6,eTx2_7,eTx2_8,eTx2_9,eTx2_10,eTx2_11,eTx2_12, test_end_check = econt_qc(chip, odir, tag, voltage, current, 27,pll_th, max_eRx_th, sec_max_eRx_th, max_eTx_th, sec_max_eTx_th)
time.sleep(1)
ps.TurnOff()

if os.path.exists(f"{database}.db") == False:
      create_database(database_name=f'{database}', table_name=f'{database}')

stuff=[(chip, test_start_time, voltage, current, over_all_test, rw_test, pll_test, phase_width_test, input_word_alignment_test, io_scan_test, output_alignment_test, alignment_bypass_test, comparing_various_config_test, track_mode_test, pll_th, max_eRx_th, sec_max_eRx_th, max_eTx_th, sec_max_eTx_th,int(pll_width),eRx_0,eRx_1,eRx_2,eRx_3,eRx_4,eRx_5,eRx_6,eRx_7,eRx_8,eRx_9,eRx_10,eRx_11,eRx2_0,eRx2_1,eRx2_2,eRx2_3,eRx2_4,eRx2_5,eRx2_6,eRx2_7,eRx2_8,eRx2_9,eRx2_10,eRx2_11,eTx_0,eTx_1,eTx_2,eTx_3,eTx_4,eTx_5,eTx_6,eTx_7,eTx_8,eTx_9,eTx_10,eTx_11,eTx_12,eTx2_0,eTx2_1,eTx2_2,eTx2_3,eTx2_4,eTx2_5,eTx2_6,eTx2_7,eTx2_8,eTx2_9,eTx2_10,eTx2_11,eTx2_12)]

add_many_column(stuff,database_name=f'{database}', table_name=f'{database}')
logging.info(f" data up dated to databse {database}")
show_all_plan(database_name=f'{database}', table_name=f'{database}')
logging.getLogger().handlers.clear()
