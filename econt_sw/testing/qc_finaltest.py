from set_econt import startup,set_phase,set_phase_of_enable,set_runbit,read_status,set_fpga,word_align,output_align,bypass_align,bypass_compare
from utils.asic_signals import ASICSignals
from i2c import I2C_Client
from PRBS import scan_prbs
from PLL import scanCapSelect
from delay_scan import delay_scan
#from PowerSupplyControls import Agilent3648A
import argparse,os,pickle,pprint
import numpy as np
import sys,copy,logging,datetime,sqlite3,socket,os,time,csv,argparse
from sqlite3_database import create_database, add_many_column, show_all_plan
from PowerSupplyControls import getPowerSupply

ps=getPowerSupply('192.168.1.50',6)
i2cClient=I2C_Client(forceLocal=1)
#-----------------------------------------
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

def find_nearest_value(target, values):
    nearest_value = None
    smallest_difference = float('inf')
    for value in values:
        difference = abs(value - target)
        if difference < smallest_difference:
            smallest_difference = difference
            nearest_value = value
    return nearest_value
#--------------------------------------------------
def qc_i2c(i2c_address=0x20):
    rw_test = 0
    sys.path.append( 'zmq_i2c/')
    def is_match(pairs,pairs_read):
        no_match = {}
        for key, value in pairs.items():
            register_value = int.from_bytes(value[0], 'little')
            if key in pairs_read.keys():
                size_byte = value[1]
                if isinstance(pairs_read[key][0], list):
                    read_value = int.from_bytes(pairs_read[key][0], 'little')
                else:
                    read_value = pairs_read[key][0]
            if read_value != register_value:
                no_match[key] = read_value
        return no_match
    time.sleep(5)
    def ping_all_addresses():
        rw_one_test = 0
        rw_zero_test = 0
        default_pairs = board.translator.pairs_from_cfg(allowed=['RW'])
        pairs_one = copy.deepcopy(default_pairs)
        pairs_zero = copy.deepcopy(default_pairs)
        for key, value in pairs_one.items():
            size_byte = value[1]
            pairs_one[key][0] = int("1"*8*size_byte,2).to_bytes(size_byte,'little')
            pairs_zero[key][0] = int("0").to_bytes(size_byte,'little')
        #DO NOT TURN OFF ERX_MUX_1
        # This is the FCMD_CLK input, disabling it disables i2c clock
        pairs_zero[1267][0]=b'\x01'
        logging.info(f"Writing ones to all registers")
        board.write_pairs(pairs_one)
        pairs_one_read = board.read_pairs(pairs_one)
        no_match_one = is_match(pairs_one,pairs_one_read)
        # print("pairs_one---------- ", pairs_one)
        # print("pairs_one_read---------- ", pairs_one_read)
        if len(no_match_one)==0:
            rw_one_test = 1
            logging.info(f"No mismatch during read write 1 to all registers")
        else:
            logging.warning("Read one pairs do not match %s",no_match_one)
            np.savetxt(f"{odir}/rw_pair_one_comparion_{tag}.txt", np.array([pairs_one, pairs_one_read]), delimiter=' ', fmt='%s', header='')
        logging.info(f"Writing zeros to all registers")
        board.write_pairs(pairs_zero)
        pairs_zero_read = board.read_pairs(pairs_zero)
        no_match_zero = is_match(pairs_zero,pairs_zero_read)
        # print("no_match_zero---------- ", no_match_zero)
        if len(no_match_zero)==0:
            rw_zero_test = 1
            logging.info(f"No mismatch during read write 0 to all registers")
        else:
            logging.warning("Read zero pairs do not match %s",no_match_zero)
            np.savetxt(f"{odir}/rw_pair_zero_comparion_{tag}.txt", np.array([pairs_zero, pairs_zero_read]), delimiter=' ', fmt='%s', header='')
        return rw_one_test, rw_zero_test
    from econ_interface import econ_interface
    board = econ_interface(i2c_address, 1, fpath="zmq_i2c/")
    rw_one, rw_zero = ping_all_addresses()
    rw_test = 0
    if (rw_one and rw_zero):
        rw_test = 1
        logging.info(f"Read Write test passed <<<")
    else:
        logging.warning("Read Write test failed!!!")
    return rw_test
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def econt_qc(board,odir,tag,voltage=1.2, current=2.6, good_capSelect_Value=27,pll_width_th=11, thresold_max_width=3,thresold_second_max_width=2,max_IO_delay_scan_width_thresold = 13, second_max_IO_delay_scan_width_thresold = 12):
    start_time = time.time()
    logging.info(f"---------------------------------Test Begain--------------------------------")
    logging.info(f"All test data  file are stored in output directory {odir}")
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # power voltage and current to chip test given
    voltage = voltage
    current = current
    dirs = [
        "configs/test_vectors/mcDataset/STC_type0_eTx5/",
        "configs/test_vectors/mcDataset/STC_type1_eTx2/",
        "configs/test_vectors/mcDataset/STC_type2_eTx3/",
        "configs/test_vectors/mcDataset/STC_type3_eTx4/",
        "configs/test_vectors/mcDataset/RPT_13eTx/",
        "configs/test_vectors/mcDataset/TS_Thr47_13eTx/",
        "configs/test_vectors/mcDataset/BC_12eTx/",
        "configs/test_vectors/mcDataset/BC_1eTx/",
    ]
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Deafult valuses
    rw_test = -1
    pll_test , pll_width = -1, -1
    phase_width_test, max_width, second_max_width = -1, [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
    input_word_alignment_test = -1
    io_scan_test, max_width_io, second_max_width_io = -1, [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1],[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
    output_alignment_test = -1
    alignment_bypass_test = -1
    comparing_various_config_test = -1
    track_mode_test = -1
    track_mode_1_test = -1
    track_mode_2_test = -1
    track_mode_3_test = -1
    over_all_run = -1
    over_all_test = -1
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    try:
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Stress test i2c (read write test)
        try:
           rw_test = qc_i2c()
        except:
           logging.warning("Read Write test incomplete ???")
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Do a hard reset
        logging.info(f"Hard reset")
        resets = ASICSignals()
        resets.send_reset(reset='hard',i2c='ASIC')
        resets.send_reset(reset='hard',i2c='emulator')
        # Initialize
        logging.info("Initializing")
        startup()
        set_fpga()
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # PLL VCO Cap select scan and set value back
        logging.info(f"Scan over PLL VCOCapSelect values")
        goodVOCCapValue = 27
        try:
            #TODO: find good value automatically
            VOCCapselected, state  = scanCapSelect(verbose=1, odir=odir, tag=tag)
            pll_thresold = pll_width_th
            if len(VOCCapselected) ==0:
                logging.info("No Good PLL VOCCapSelect values")
                pll_test = 0
                logging.info(f"Trying to Set VCOCapSelect value to {goodVOCCapValue}")
            else:
                logging.info(f"Good PLL VOCCapSelect values: %s"%VOCCapselected)
                np.savetxt(f"{odir}/good_capSelected_values_{tag}.txt", np.array([VOCCapselected]), delimiter=" ", fmt="%d", header="")
                state = np.array(state)
                phase = consecutive(np.argwhere(state==9))
                size = [np.size(a) for a in phase]
                pll_width = np.max(size)
                logging.info(f"Good PLL width  {pll_width}")
                if (pll_width >= pll_thresold) and (goodVOCCapValue in VOCCapselected):
                    pll_test = 1
                    logging.info(f" PLL test passed <<<")
                else:
                    pll_test = 0
                    logging.warning(f" PLL test failed!!")
                    if goodVOCCapValue not in VOCCapselected:
                        logging.warning(f"Default value {goodVOCCapValue} does not does not give PUSM 9")
                        goodVOCCapValue = find_nearest_value(goodVOCCapValue, VOCCapselected)
                        logging.warning(f"VOCCapSelect value is set to {goodVOCCapValue} which is nearest to 27 and give PUSM 9")
            logging.info(f"Setting VCOCapSelect value to {goodVOCCapValue}")
            i2cClient.call(args_name='PLL_CBOvcoCapSelect',args_value=f'{goodVOCCapValue}')
        except:
            logging.warning(f"PLL test incomplete ???")
            logging.info(f"Try to Setting VCOCapSelect value to {goodVOCCapValue}")
            i2cClient.call(args_name='PLL_CBOvcoCapSelect',args_value=f'{goodVOCCapValue}')
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # logging.info(f"Scan phase w PRBS err counters and width")
        try:
            err_counts, best_setting = scan_prbs(32,'ASIC',0.05,range(0,12),1,verbose=0,odir=odir,tag=tag)
            np.savetxt(f"{odir}/best_phase_scan_seting_{tag}.txt", np.array([best_setting]), delimiter=" ", fmt="%d", header="")
            logging.info(f"Best phase settings found to be {str(best_setting)}")
            max_width, second_max_width =  get_max_width(err_counts, channels=12, padding=4)
            # print("max_width -----> ", max_width)
            np.savetxt(f"{odir}/width_of_phase_scan_seting_{tag}.txt", np.array([max_width, second_max_width]), delimiter=" ", fmt="%d", header="")
            logging.info(f" Max width of good phase settings {max_width}")
            logging.info(f" Second Max width of good phase settings {second_max_width}")
            width1 = np.array([thresold_max_width] * 12)
            width2 = np.array([thresold_second_max_width] * 12)
            np.savetxt(f"{odir}/phase_width_comparion_{tag}.txt", np.array([max_width >= width1, second_max_width >= width2]), delimiter=' ', fmt='%d', header='')
            if ((max_width >= width1).all() and (second_max_width >= width2).all()):
                phase_width_test = 1
                logging.info(f"Phase width test at eRx is passed <<<")
            else:
                phase_width_test = 0
                logging.warning(f"Phase width test at eRx is failed !!!")
        except:

            logging.warning(f"Phase width test at eRx is incomplete ???")

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Other init steps
        set_phase(best_setting=','.join([str(i) for i in best_setting]))
        set_phase_of_enable(0)
        set_runbit(1)
        read_status()
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Input word alignment

        logging.info("Align input words")

        try:
            set_fpga()
            input_word_alignment_test = word_align(bx=None,emulator_delay=None)
            if input_word_alignment_test == 1:
                logging.info(f"Input word alignment test passed <<<")
            else:
                logging.warning(f"Input word alignment test failed !!!")
        except:
            logging.warning(f"Input word alignment test is incomplete ???")
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Scan IO delay scan and width and io_delay_scan_test

        logging.info('from IO delay scan')
        try:
            set_runbit(0)
            i2cClient.call(args_yaml="configs/alignOutput_TS.yaml",args_i2c='ASIC,emulator',args_write=1)
            set_runbit(1)
            logging.debug(f"Configured ASIC/emulator with all eTx")
            bitcounts,errorcounts = delay_scan(odir,ioType='from',tag=tag)
            err_counts_io = list(errorcounts.values())
            logging.debug("Error counts form IO delay scan: %s"%err_counts_io)
            max_width_io, second_max_width_io =  get_max_width(err_counts_io, channels=13, padding=10)
            np.savetxt(f"{odir}/width_of_io_scan_seting_{tag}.txt", np.array([max_width_io, second_max_width_io]), delimiter=" ", fmt="%d", header="")
            logging.info(f" Max width of io-scan settings {max_width_io}")
            logging.info(f" Second Max width of io-scan settings {second_max_width_io}")
            max_IO_delay = np.array([max_IO_delay_scan_width_thresold] * 13)
            second_max_IO_delay = np.array([second_max_IO_delay_scan_width_thresold] * 13)
            np.savetxt(f"{odir}/io_delay_width_comparion_{tag}.txt", np.array([max_width_io >= max_IO_delay,second_max_width_io >= second_max_IO_delay]), delimiter=" ", fmt="%d", header="")
            if ((max_width_io >= max_IO_delay).all() and (second_max_width_io >= second_max_IO_delay).all()):
                io_scan_test = 1
                logging.info(f"Phase width test at eTx passed <<<")
            else:
                io_scan_test = 0
                logging.warning(f"Phase width test at eTx failed !!!")
        except:

            logging.warning(f"Phase width test at eTx is incomplete ???")
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Output alignment
        try:
            logging.info("Outputting word alignment")
            error_counts = output_align(verbose=0,outdir=odir, chip_number=chip)
            if error_counts == 0:
                output_alignment_test = 1
                logging.info("output word alignment test passed <<<")
            else:
                output_alignment_test = 0
                logging.warning("output word alignment test failed !!!")
        except:
            logging.warning("output alignment test incomplete ???")
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Bypass alignment
        logging.info("Alignment bypass mode")
        try:
           #bypass_alignment = bypass_align(idir="configs/test_vectors/alignment/",start_ASIC=0,start_emulator=13)
           bypass_alignment = bypass_align(idir="configs/test_vectors/alignment/")
           if bypass_alignment==1:
              alignment_bypass_test = 1
              logging.info("Alignment bypass test passed <<<")
           else:
              alignment_bypass_test = 0
              logging.warning("Alignment bypass test failed !!!")
        except:
            logging.warning("Alignment bypass test is incomplete ???")
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Compare for various configurations
        logging.info("Comparing various configurations")
        try:
            total_error_config = 0
            dict = {}
            # STC_type0_eTx5_error,STC_type1_eTx2_error, STC_type2_eTx3_error, STC_type3_eTx4_error, RPT_13eTx_error, TS_Thr47_13eTx_error, BC_12eTx_error , BC_1eTx_error = 0, 0, 0 ,0, 0, 0, 0, 0
            # error_types= [STC_type0_eTx5_error,STC_type1_eTx2_error, STC_type2_eTx3_error, STC_type3_eTx4_error, RPT_13eTx_error, TS_Thr47_13eTx_error, BC_12eTx_error , BC_1eTx_error]
            for i in range(len(dirs)):
                dict[dirs[i]] = bypass_compare(dirs[i], odir)
                total_error_config = total_error_config + dict[dirs[i]]
                # print(f"{error_types[i]}","---------->", dict[dirs[i]])
            with open(f'{odir}/error_counts_for_vorious_config_{tag}.csv', 'w') as csvfile:
                for key in dict.keys():
                    csvfile.write("%s, %s\n"%(key, dict[key]))
            if total_error_config == 0:
                comparing_various_config_test = 1
                logging.info("comparing various configurations test passed <<<")
            else:
                comparing_various_config_test = 0
                logging.warning("various configurations test failed !!!")
        except:
            logging.warning("Comparing various configurations test is incomplete ???")
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Test the different track modes and train channels
        logging.info('Testing track modes')
        try:
            startup()
            set_fpga()
            for trackmode in range(1, 4):
                i2cClient.call(args_name='EPRXGRP_TOP_trackMode', args_value=f'{trackmode}')
                phaseSelect_vals = []
                error_t =[]
                if trackmode == 3:
                    set_phase(best_setting=','.join([str(i) for i in best_setting]))
                for trainchannel in range(0,50):
                    i2cClient.call(args_name='CH_EPRXGRP_*_trainChannel', args_value='1')
                    i2cClient.call(args_name='CH_EPRXGRP_*_trainChannel', args_value='0')
                    x = i2cClient.call(args_name='CH_EPRXGRP_*_status_phaseSelect',args_i2c='ASIC')
                    selected_phase_settings = [x['ASIC']['RO'][f'CH_EPRXGRP_{channel}INPUT_ALL']['status_phaseSelect'] for channel in range(0, 12)]
                    phaseSelect_vals.append(selected_phase_settings)
                    # print(f"-----selected_phase_settings for trackmode {trackmode} for run {trainchannel}--------------", selected_phase_settings)
                    errors_ =[]
                    for i,j in enumerate(selected_phase_settings):
                      errors_.append(np.transpose(err_counts)[i][j])
                      total_errors1 = np.sum(errors_)
                    error_t.append(total_errors1)
                with open(f'{odir}/trackmode{trackmode}_phaseSelect_{chip}board.csv', 'w') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(zip(*phaseSelect_vals))
                total_error2 = np.sum(error_t)
                if trackmode == 1:
                    if total_error2 == 0:
                        track_mode_1_test = 1
                        logging.info(f"trackmode {trackmode} test passed <<<  ")
                    else:
                        track_mode_1_test = 0
                        logging.warning(f"total error in trackmode {trackmode} in all run --->   {total_error2}")
                        logging.warning(f"trackmode {trackmode} test failed !!!  ")
                if trackmode == 2:
                    if total_error2 == 0:
                        track_mode_2_test = 1
                        logging.info(f"trackmode {trackmode} test passed <<<   ")
                    else:
                        track_mode_2_test = 0
                        logging.warning(f"total error in trackmode {trackmode} in all run --->   {total_error2}")
                        logging.warning(f"trackmode {trackmode} test failed !!!  ")
                if trackmode == 3:
                    if total_error2 == 0:
                        track_mode_3_test = 1
                        logging.info(f"trackmode {trackmode} test passed <<<   ")
                    else:
                        track_mode_3_test = 0
                        logging.warning(f"total error in trackmode {trackmode} in all run ---> {total_error2}")
                        logging.warning(f"trackmode {trackmode} test failed !!!  ")
            if track_mode_1_test==1 and track_mode_2_test==1 and track_mode_3_test==1:
                track_mode_test = 1
                logging.info(f"trackmode test passed <<<")
            else:
                track_mode_test = 0
                logging.warning(f"trackmode test failed !!!")
        except:
            logging.warning("Trackmode Test is not completed ???")
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # Soft reset
        logging.info(f"Soft reset")
        resets.send_reset(reset='soft',i2c='ASIC')
        resets.send_reset(reset='soft',i2c='emulator')
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        over_all_run = 1
        logging.info(f"Over all Run                     ---->   {over_all_run}")
    except:
        logging.warning("Test is not completed ???")
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
    logging.info(f"--------------------------------- All Test Results -------------------------------")
    logging.info(f"Read Write Test                      ---->   {rw_test}")
    logging.info(f"PLL Test                             ---->   {pll_test}")
    logging.info(f"Phase Width Test                     ---->   {phase_width_test}")
    logging.info(f"Input Word Alignment Test            ---->   {input_word_alignment_test}")
    logging.info(f"IO Phase Width Test                  ---->   {io_scan_test}")
    logging.info(f"Output Alignment Test                ---->   {output_alignment_test}")
    logging.info(f"Bypass Alignment Test                ---->   {alignment_bypass_test}")
    logging.info(f"Comparing various Configuration Test ---->   {comparing_various_config_test}")
    logging.info(f"Track Mode Test                      ---->   {track_mode_test}")

    if(rw_test==1 and pll_test==1 and phase_width_test==1 and input_word_alignment_test==1 and \
    io_scan_test==1 and output_alignment_test==1 and alignment_bypass_test ==1 and\
    comparing_various_config_test==1 and track_mode_test ==1):
        over_all_test = 1
        logging.info("----------->    pass all the tests     <----------------")
    else:
        over_all_test = 0
        logging.warning("!!!!!!!!!!   failed to pass all tests   !!!!!!!!!!!!!!!!!!")
    end_ = datetime.datetime.now()
    test_end_time  = end_.strftime("%Y-%m-%d_%H:%M:%S")
    end_time = time.time()
    logging.info(f"Total time taken for test --------->   {end_time - start_time} sec")
    logging.info(f"----------------------------------- Test Finalized ---------------------------------")
    return  voltage, current, over_all_test, rw_test,pll_test,phase_width_test,input_word_alignment_test,\
    io_scan_test,output_alignment_test,alignment_bypass_test,comparing_various_config_test,track_mode_test,\
    pll_width,max_width[0],max_width[1],max_width[2],max_width[3],max_width[4],max_width[5],max_width[6],\
    max_width[7],max_width[8],max_width[9],max_width[10],max_width[11],second_max_width[0],second_max_width[1],\
    second_max_width[2],second_max_width[3],second_max_width[4],second_max_width[5],second_max_width[6],\
    second_max_width[7],second_max_width[8],second_max_width[9],second_max_width[10],second_max_width[11],\
    max_width_io[0],max_width_io[1],max_width_io[2],max_width_io[3],max_width_io[4],max_width_io[5],max_width_io[6],\
    max_width_io[7],max_width_io[8],max_width_io[9],max_width_io[10],max_width_io[11],max_width_io[12],\
    second_max_width_io[0],second_max_width_io[1],second_max_width_io[2],second_max_width_io[3],second_max_width_io[4],\
    second_max_width_io[5],second_max_width_io[6],second_max_width_io[7],second_max_width_io[8],second_max_width_io[9],\
    second_max_width_io[10],second_max_width_io[11],second_max_width_io[12], over_all_run
#===============================================================================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--chip', '-c', type=int, default=9999, help='Chip number')
    parser.add_argument('--odir', '-o', type=str, default='data', help='output dir')
    parser.add_argument('--database', '-d', type=str, default='Econt_database', help='Database name')
    args = parser.parse_args()
    chip = args.chip
    out_dir = args.odir
    database = args.database
    start_ = datetime.datetime.now()
    test_start_time  = start_.strftime("%Y-%m-%d_%H:%M:%S")
    odir = f"{out_dir}/chip_{chip}"
    if os.path.exists(f'{odir}'):
        os.system(f'rm -r {odir}')
    os.system(f'mkdir -p {odir}')
    tag=f"chip_{chip}"
    logName=f"{odir}/logFile_{tag}.log"
    logging.basicConfig(level=logging.INFO,
    #logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - {_tag} - %(levelname)-6s %(message)s'.format(_tag=tag),
                        datefmt='%m-%d-%y %H:%M:%S',
                        filename=logName,
                        filemode='a')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    #console.setLevel(logging.DEBUG)
    _f='%(asctime)s - {_tag} - %(levelname)-6s %(message)s'.format(_tag=tag)
    console.setFormatter(logging.Formatter(_f))
    logging.getLogger().addHandler(console)
#------------------------------------------
# Power supply
    ps.SetLimits(1.2,0.6)
    ps.TurnOn()
    time.sleep(1)
    real_voltage = ps.ReadPower()
    np.savetxt(f"{odir}/power_voltage_current_{tag}.txt", np.array([real_voltage]), delimiter=" ", fmt="%s", header="")
    logging.info(f"power status, voltage and current  to chip : {real_voltage[0]},  {real_voltage[1]}, {real_voltage[2]}")
    voltage = real_voltage[1]
    current = real_voltage[2]
#------------------------------------------------
#setting thresold value
    pll_th = 14
    max_eRx_th = 4
    sec_max_eRx_th = 3
    max_eTx_th = 14
    sec_max_eTx_th = 12
    logging.info(f"Thresold for PLL good width used : {pll_th}")
    logging.info(f"Thresold for max good Phase width used at eRx: {max_eRx_th}")
    logging.info(f"Thresold for 2nd max good Phase width used at eRx: {sec_max_eRx_th}")
    logging.info(f"Thresold for max good Phase width used at eTx: {max_eTx_th}")
    logging.info(f"Thresold for 2nd max good Phase width used at eTx: {sec_max_eTx_th}")
#------------------------------------------------
    voltage, current, over_all_test, rw_test, pll_test, phase_width_test, input_word_alignment_test, io_scan_test,\
    output_alignment_test, alignment_bypass_test, comparing_various_config_test, track_mode_test,pll_width,\
    eRx_0,eRx_1,eRx_2,eRx_3,eRx_4,eRx_5,eRx_6,eRx_7,eRx_8,eRx_9,eRx_10,eRx_11,eRx2_0,eRx2_1,eRx2_2,eRx2_3,eRx2_4,\
    eRx2_5,eRx2_6,eRx2_7,eRx2_8,eRx2_9,eRx2_10,eRx2_11,eTx_0,eTx_1,eTx_2,eTx_3,eTx_4,eTx_5,eTx_6,eTx_7,eTx_8,eTx_9,\
    eTx_10,eTx_11,eTx_12,eTx2_0,eTx2_1,eTx2_2,eTx2_3,eTx2_4,eTx2_5,eTx2_6,eTx2_7,eTx2_8,eTx2_9,eTx2_10,eTx2_11,eTx2_12,\
    test_end_check = econt_qc( chip, odir, tag, voltage, current, 27,pll_th, max_eRx_th, sec_max_eRx_th, max_eTx_th, sec_max_eTx_th)
    ps.TurnOff() # for turning off power supply for during swapping chip
#----------------------------------------------------------------------------------------------

#Updating database
    if os.path.exists(f"{database}.db") == False:
        create_database(database_name=f'{database}', table_name=f'{database}')

    stuff=[(chip, test_start_time, voltage, current, over_all_test, rw_test, pll_test, phase_width_test, input_word_alignment_test,\
    io_scan_test, output_alignment_test, alignment_bypass_test, comparing_various_config_test, track_mode_test, pll_th, max_eRx_th,\
    sec_max_eRx_th, max_eTx_th, sec_max_eTx_th,int(pll_width),eRx_0,eRx_1,eRx_2,eRx_3,eRx_4,eRx_5,eRx_6,eRx_7,eRx_8,eRx_9,eRx_10,\
    eRx_11,eRx2_0,eRx2_1,eRx2_2,eRx2_3,eRx2_4,eRx2_5,eRx2_6,eRx2_7,eRx2_8,eRx2_9,eRx2_10,eRx2_11,eTx_0,eTx_1,eTx_2,eTx_3,eTx_4,eTx_5,\
    eTx_6,eTx_7,eTx_8,eTx_9,eTx_10,eTx_11,eTx_12,eTx2_0,eTx2_1,eTx2_2,eTx2_3,eTx2_4,eTx2_5,eTx2_6,eTx2_7,eTx2_8,eTx2_9,eTx2_10,\
    eTx2_11,eTx2_12)]

    add_many_column(stuff,database_name=f'{database}', table_name=f'{database}')
    logging.info(f" data up dated to databse {database}")
    show_all_plan(database_name=f'{database}', table_name=f'{database}')
    logging.getLogger().handlers.clear()

#==================================================================================

