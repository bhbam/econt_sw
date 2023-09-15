import numpy as np

import logging

from utils.fast_command import FastCommands
from utils.link_capture import LinkCapture
from utils.test_vectors import TestVectors
lc = LinkCapture()
fc = FastCommands()
tv = TestVectors()

num_outputs = 13

def find_BX0(lcapture,
             BX0_word=0xf922f922,
             BX0_position=None):
    """
    Finds the BX0s for each eTx.
    """
    lc.configure_acquire([lcapture],"linkreset_ECONt")
    lc.do_capture([lcapture])
    fc.request("link_reset_econt")
    data = lc.get_captured_data([lcapture])[lcapture]
    # tv.save_testvector(f"{lcapture}_latency.csv",data)

    BX0_rows,BX0_cols = (data == BX0_word).nonzero()

    try:
        assert (len(BX0_rows) > 0) & np.any(BX0_cols==0)

        # need to order BX0_rows by column and pad to length 13*2
        rows = []
        for k in range(2):
            for i in range(num_outputs):
                found_idx = False
                for idx,j in np.ndenumerate(BX0_cols):
                    if j == i and not found_idx:
                        rows.append(BX0_rows[idx])
                        BX0_cols = np.delete(BX0_cols, idx)
                        BX0_rows = np.delete(BX0_rows, idx)
                        found_idx = True
                if not found_idx:
                    rows.append(-1)

        BX0_rows = np.array(rows)
        logging.debug('Found alignment word for %s in BX0_rows: %s'%(lcapture,list(BX0_rows)))

    except AssertionError:
        logging.error('BX0 sync word not found anywhere or in link 0')
        return False

    return BX0_rows
        
def match_BX0(
        BX0_rows,
        neTx,
        ref_position=None):
    """
    Check if position at which we found BX0 matches target.
    ----
    - latencies:
       latency values for all eTx
    - BX0_rows: 
       position at which we found BX0 for different elinks
    - neTx:
       number of eTx active
    - ref_position:
       reference position
    """
    logging.debug('Compare BX0')

    orbits = [
        (BX0_rows[0], BX0_rows[:neTx]),
        (BX0_rows[num_outputs], BX0_rows[num_outputs:num_outputs+neTx]),
    ]
    # logging.debug('orbits',orbits)

    keep_latency_scan = True
    new_ref_position = None    
    for orbit,(target,positions) in enumerate(orbits):
        latencies_not_match = None
        all_eTx_match = (positions == target)
        if ref_position is not None:
            # logging.debug(f'Reference position is {ref_position}')
            all_eTx_match_ref = (positions == ref_position)
        else:
            ref_position = target
            # logging.debug(f'Reference position is same as target {ref_position}')
            all_eTx_match_ref = all_eTx_match

        if np.all(all_eTx_match & all_eTx_match_ref):
            # logging.debug(f'All links found BX0 in the same position as reference position {ref_position}')
            new_ref_position = target
            keep_latency_scan = False
            latencies_not_match = ~np.all(all_eTx_match & all_eTx_match_ref)
            break

        elif np.any(~all_eTx_match) and np.any(all_eTx_match_ref):
            # logging.debug('Some links found BX0 in the same position as reference position %s'%(np.any(all_eTx_match & all_eTx_match_ref)))
            if (ref_position - positions[~all_eTx_match_ref][0] < 0):
                # logging.debug('Some links found BX0 in a position later than the reference position')
                new_ref_position = positions[~all_eTx_match_ref][0]
                latencies_not_match = all_eTx_match_ref
            else:
                # logging.debug('Some links found BX0 in a position earlier than the reference position')
                new_ref_position = positions[all_eTx_match_ref][0]
                latencies_not_match = ~all_eTx_match_ref
            break

        elif np.all(all_eTx_match) and np.all(~all_eTx_match_ref) and (ref_position - target < 0):
            # logging.debug('All links found BX0 in a same position earlier than the reference position')
            new_ref_position = target
            keep_latency_scan = False
            latencies_not_match = ~all_eTx_match_ref
            break

        else:
            logging.warning(f'No links found BX0 in same position as reference position {ref_position} for orbit {orbit}')
            continue

    return keep_latency_scan,latencies_not_match,new_ref_position

def scan_latency(
        lcapture,
        BX0_word=0xf922f922,
        neTx=13,
        BX0_position=None,
        starting_value=0,
        reverse=False):
    """
    Scan latency of capture links.
    ------
    - lcapture:
       link capture string
    - BX0_word:
       training pattern to find at BX0
    - neTx:
       number of links active
    - BX0_position:
       reference row position at which we want to find BX0
    - val:
       value of latency to start the scan
    """
    logging.debug(f'Scan latency values for {lcapture} with nlinks {neTx}, with reference BX0 at {BX0_position}')

    # start with an array of latencies per active channel
    latency = np.array([starting_value] * lc.nlinks[lcapture])

    if reverse:
        latencies = range(starting_value,-1,-1)
    else:
        latencies = range(starting_value,20)

    # logging.debug(latencies)
    # loop over latency values
    for val in latencies:
        # replace value in the latency array, if it is not 1
        # logging.debug(f'Setting latency for {lcapture} to {val}')
        latency[latency==-1] = val
        
        # logging.debug(f'Setting latency array %s',latency)
        # logging.debug(f'Setting latency for {lcapture} %s',latency)
        lc.set_latency([lcapture],latency)

        # send a pattern and find rows in which BX0 training pattern is present
        BX0_rows = find_BX0(lcapture,BX0_word,BX0_position)

        # do the BX0 rows match between themselves and a reference BX0_position?
        keep_latency_scan,latencies_not_match,BX0_position = match_BX0(BX0_rows,neTx,BX0_position)
        
        latency[:neTx][latencies_not_match] = -1
        if np.any(latencies_not_match):
            latency[neTx:] = -1
            
        if not keep_latency_scan:
            break 

    return latency,BX0_position

fcConfigRemap={'link_reset_econt':'linkreset_ECONt',
               'link_reset_econd':'linkreset_ECONd'
           }

def align(BX0_word=0xf922f922,
          captureFC='link_reset_econt',
          neTx=13):

    """
    New, simplified, latency alignment process.
    Sets latency to 0 for both lc-ASIC and lc-emulator
    Finds the BX0s locations in the. By default it works for ouput align.
    For bypass alignment use BX0_word=0xffffffff,captureFC='link_reset_econd',neTx=10
    """

    logging.debug(f"Capturing on {captureFC} for {neTx} eTx")

    lc.set_latency(['lc-ASIC','lc-emulator'],[0]*13)
    lcaptures=['lc-ASIC','lc-emulator']
    lc.configure_acquire(lcaptures,fcConfigRemap[captureFC])
    lc.do_capture(lcaptures)
    fc.request(captureFC)
    data = lc.get_captured_data(lcaptures)

    BX0_ASIC_idx=np.argwhere(data['lc-ASIC'][:3564]==BX0_word)[:neTx]
    BX0_emulator_idx=np.argwhere(data['lc-emulator'][:3564]==BX0_word)[:neTx]
    BX0_ASIC=np.array([-1]*neTx,dtype=int)
    BX0_emulator=np.array([-1]*neTx,dtype=int)

    BX0_ASIC[BX0_ASIC_idx[:,1]]=BX0_ASIC_idx[:,0]
    BX0_emulator[BX0_emulator_idx[:,1]]=BX0_emulator_idx[:,0]
    #Check that BX0 pattern found in all eTx
    try:
        assert ((BX0_ASIC>-1).all())
        assert ((BX0_emulator_idx>-1).all())
    except:
        logging.error(f"Unable to locate BX0 pattern ({BX0_word:08x})")
        logging.error("    Locations in lc-ASIC     : %s"%list(BX0_ASIC))
        logging.error("    Locations in lc-emulator : %s"%list(BX0_emulator))
        logging.debug("False") 
        return False
    if neTx !=13 :    
       BX0_ASIC=np.array([BX0_ASIC[0]]*13)
       BX0_emulator=np.array([BX0_emulator[0]]*13)

    #Set latency, delaying all eTx to latest word from either emulator or ASIC
    maxBX0=max(BX0_emulator.max(),BX0_ASIC.max())
    newLat_ASIC=maxBX0-BX0_ASIC
    newLat_emulator=maxBX0-BX0_emulator
    logging.info("Align ASIC latency adjusted by BX %s "%(newLat_ASIC))
    logging.info("Align Emulator latency adjusted by BX %s "%(newLat_emulator))
    lc.set_latency(['lc-ASIC'],newLat_ASIC)
    lc.set_latency(['lc-emulator'],newLat_emulator)

    # checking the alifnment after seeting them to required values
    lcaptures=['lc-ASIC','lc-emulator']
    lc.configure_acquire(lcaptures,fcConfigRemap[captureFC])
    lc.do_capture(lcaptures)
    fc.request(captureFC)
    data = lc.get_captured_data(lcaptures)
    logging.info('Good Latency Alignment  :   %s'%(data['lc-ASIC']==data['lc-emulator']).all())


    return True


if __name__=='__main__':
#  print(align())
   print(align(BX0_word=0xffffffff,captureFC='link_reset_econd',neTx=10))

