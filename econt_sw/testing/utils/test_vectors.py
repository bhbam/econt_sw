import os
import numpy as np

import uhal
from .uhal_config import *

import logging
logging.basicConfig()
logger = logging.getLogger('utils:tv')
logger.setLevel(logging.INFO)

class TestVectors():
    """ Class to handle test vectors """
    def __init__(self,tv='testvectors',logLevel=""):
        """Initialization class to setup connection manager and device"""
        set_logLevel(logLevel)
        
        self.man = uhal.ConnectionManager("file://connection.xml")
        self.dev = self.man.getDevice("mylittlememory")
        self.name_sw = names[tv]['switch']
        self.name_st = names[tv]['stream']
        self.name_bram = names[tv]['bram']
        if tv=='testvectors':
            self.nlinks = input_nlinks
        else:
            self.nlinks = output_nlinks
             
    def read_testvector(self,fname,nlinks=12):
        """Read input test vector"""
        import csv
        data = [[] for l in range(nlinks)]
        with open(fname) as f:
            csv_reader = csv.reader(f, delimiter=',')
            for i,row in enumerate(csv_reader):
                if i==0: continue # skip header                                                                                                        
                for l in range(nlinks):
                    data[l].append(row[l])
        return data

    def fixed_hex(self,data,N):
        return np.vectorize(lambda d : '{num:0{width}x}'.format(num=d, width=N))(data)

    def save_testvector(self,fname,data,header=False):
        """
        Save test vector in csv
        TODO: Writes header as TX
        """
        if len(data)>0:
            import csv
            try:
                os.remove(fname)
            except:
                pass
            with open( fname, 'w') as f:
                writer = csv.writer(f, delimiter=',')
                if header:
                    writer.writerow(['TX_DATA_%i'%l for l in range(len(data[0]))])
                for j in range(len(data)):
                    writer.writerow(['{0:08x}'.format(int(data[j][k])) for k in range(len(data[j]))])

    def configure(self,dtype="",idir=""):
        """
        Set test vectors
        dtype [PRBS,PRBS32,PRBS28,debug,zeros]
        """
        testvectors_settings = {
            "output_select": 0x0,
            "n_idle_words": 255,
            "idle_word": 0xaccccccc,
            "idle_word_BX0": 0x9ccccccc,
            "header_mask": 0x00000000,
            "header": 0xa0000000,
            "header_BX0": 0x90000000,
        }
        if dtype == "PRBS":
            logger.info('Sending 32 bit PRBS w header mask')
            # 32-bit PRBS, the headers should not be there
            # ECON-T expects no headers when it is checking 32-bit PRBS. 
            testvectors_settings["output_select"] = 0x1
            testvectors_settings["header_mask"] = 0x00000000
        elif dtype == "PRBS32":
            logger.info('Sending 32 bit PRBS w no header mask')
            testvectors_settings["output_select"] = 0x1
        elif dtype == "PRBS28":
            # 28-bit PRBS, the headers should be there
            # ECON-T expects headers when it is checking 28-bit PRBS. 
            logger.info('Sending 28 bit PRBS w headers')
            testvectors_settings["output_select"] = 0x2
            testvectors_settings["header_mask"] = 0xf0000000
        elif dtype == "debug":
            logger.info('Setting idle words with only headers and zeros')
            # send idle word with only headers and zeros
            testvectors_settings["idle_word"] = 0xa0000000
            testvectors_settings["idle_word_BX0"] = 0x90000000

        logger.info('Test vector settings %s'%testvectors_settings)

        for l in range( self.nlinks ):
            for key,value in testvectors_settings.items():
                self.dev.getNode(self.name_sw+".link"+str(l)+"."+key).write(value)
                self.dev.getNode(self.name_st+".link"+str(l)+".sync_mode").write(0x1)
                self.dev.getNode(self.name_st+".link"+str(l)+".ram_range").write(0x1)
                self.dev.getNode(self.name_st+".link"+str(l)+".force_sync").write(0x0)
            self.dev.dispatch()

        if testvectors_settings["output_select"] == 0:
            out_brams = []
            for l in range(self.nlinks):
                out_brams.append([None] * 4095)
                
            if dtype == "zeros":
                logger.info('Writing zero data w headers in test vectors')
                for l in range(self.nlinks):
                    for i,b in enumerate(out_brams[l]):
                        if i==0:
                            out_brams[l][i] = 0x90000000
                        else:
                            out_brams[l][i] = 0xa0000000
                    self.dev.getNode(self.name_bram.replace('00',"%02d"%l)).writeBlock(out_brams[l])
                # import numpy as np  
                # data = np.array(out_brams).T 
                # self.save_testvector("zeros.csv",data,header=True)

            if idir!="":
                fname = idir+"/../testInput.csv"
                data = self.read_testvector(fname)
                logger.info('Writing test vectors from %s'%idir)
                for l in range(input_nlinks):
                    for i,b in enumerate(out_brams[l]):
                        out_brams[l][i] = int(data[l][i%3564],16)
                    self.dev.getNode(self.name_bram.replace('00',"%02d"%l)).writeBlock(out_brams[l])
                    self.dev.dispatch()

    def set_bypass(self,bypass=1):
        """Set bypass"""
        for l in range(self.nlinks):
            self.dev.getNode(self.name_sw+".link"+str(l)+".output_select").write(bypass)
        self.dev.dispatch()

