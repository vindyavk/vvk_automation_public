"""
 Copyright (c) Infoblox Inc., 2016
 Report Name          : Top Device Identified
 Report Category      : DHCP Fingerprint.
 Number of Test cases : 1
 Execution time       : 302.61 seconds
 Execution Group      : Hour Group (HG)
 Description          : DHCP Fingerprint Requested Leases'.

 Author   : Manimaran Avudayappan
 History  : 05/24/2016 (Created)
 Reviewer : Raghavendra MN
"""
import pytest
import unittest
import logging
import subprocess
import json
import os
import ib_utils.ib_validaiton as ib_validation
import ib_utils.ib_system as ib_system
import ib_utils.ib_NIOS as ib_NIOS
import ib_utils.ib_get as ib_get
import config
import pexpect
import sys
import random
import ib_utils.ib_NIOS as ib_NIOS
import ib_utils.ib_get as ib_get
from logger import logger
from time import sleep
from ib_utils.ib_system import search_dump as search_dump
from ib_utils.ib_validaiton import compare_results as compare_results
"""
TEST Steps:
      1.  Input/Preparation  : Preparation called by separte script as reports will be updated every one hour
                                   a. Create a custom network view network_view_dhcp,
                                       10.0.0.0/8
                                       51.0.0.0/24 with range 51.0.0.1 to 51.0.0.100.
                                       Request 10 Leases for Voip Phones/Adapters, Switches and 1 lease for Apple Airport , AP Meraki and Alps Electric
                                       sudo /import/tools/qa/tools/dras_opt55/dras -i "+config.grid_member1_vip+" -n 10 -w -D -O 55:0103060c0f2a424378
      2.  Search     : Performing Search operation with default/custom filter
      3.  Validation : comparing Search results with Retrieved 'Top Device Identified' report without delta.
"""

class TopDeviceIdentified(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        logger.info('-'*15+"START:Top Device Identified report"+'-'*15)

        cls.test1=[]
        temp={}
        temp["Fingerprint"]="3Com Switches"
        temp["Total"]="10"
        cls.test1.append(temp)
        
        temp={}
        temp["Fingerprint"]="Snom VoIP solutions"
        temp["Total"]="10"
        cls.test1.append(temp)
	
	logger.info("Creating input in json format for Top Device Identified report validation ")
        logger.info(json.dumps(cls.test1, sort_keys=True, indent=4, separators=(',', ': ')))

    def test_1_top_device_identified(self):
        logger.info("TestCase:"+sys._getframe().f_code.co_name)
        search_str=r"search index=ib_dhcp_summary report=si_dhcp_top_os_by_network * (CIDR>=1) * * | dedup MAC_DUID | eval  FINGER_PRINT=if(isnull(OS_NUMBER) OR OS_NUMBER==0,FP,SFP)         | noop | eval  DEVICE_CLASS=if(isnull(DEVICE_CLASS), \"Modified or Deleted\", DEVICE_CLASS) | eventstats count as COUNT_SUM  | stats count as Total by FINGER_PRINT  COUNT_SUM  | eval percentage = round(Total/COUNT_SUM  * 100) | rename percentage as \"% of all devices\", FINGER_PRINT as \"Fingerprint\"  | sort 0 -num(Total) | head 10  | table \"Fingerprint\" Total \"% of all devices\""
        cmd = config.search_py + " \"" + search_str + "\" --output_mode=json"
        logger.info (cmd) 
        os.system(cmd)
        try:
            retrived_data=open(config.json_file).read()
        except:
            logger.error('search operation failed due to %s',e)
            raise Exception("Search operation failed, Please check Grid Configuration")
        output_data = json.loads(retrived_data)
        results_list = output_data['results']
        search_dump(sys._getframe().f_code.co_name+"_search_output.txt",self.test1,results_list)
        logger.info("dumping search results in '%s' 'dumps' directory",sys._getframe().f_code.co_name+"_search_output.txt")
        logger.info("compare_results")
        result = compare_results(self.test1,results_list)
        if result == 0:
            logger.info("Search validation result: %s (PASS)",result)
        else:
            logger.error("Search validation result: %s (FAIL)",result)
        msg = 'Validation is not matching for object which is retrieved from DB %s', result
        assert result == 0, msg 

    @classmethod
    def teardown_class(cls):
        logger.info('-'*15+"END:Top Device Identified report"+'-'*15)
	
