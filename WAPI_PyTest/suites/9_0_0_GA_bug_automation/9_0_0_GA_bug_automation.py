#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Vindya V K"
__email__  = "vvk@infoblox.com"

#############################################################################
# Grid Set up required:                                                     #
#  1. Grid Master (SA)  - 9.0.0-OFFICIAL-BUILD                              #
#  2. Licenses : DNS, DHCP, Grid, NIOS                                      #
#                                                                           #
#############################################################################

#### REQUIRED LIBRARIES ####
import os
import sys
import json
import config
import pytest
import unittest
import logging
from time import sleep
import ib_utils.ib_NIOS as ib_NIOS
import ib_utils.common_utilities as common_util
import pexpect
import subprocess
from ib_utils.start_stop_logs import log_action as log
from ib_utils.file_content_validation import log_validation as logv


#####################################################################################################
# BUGS COVERED IN THIS SCRIPT:                                                                      #
#                                                                                                   #
# 1. NIOS-86695     (Automated by Vindya)                                                           #
# 2. NIOS-88913     (Automated by Vindya)                                                           #
#####################################################################################################


logging.basicConfig(format='%(asctime)s - %(name)s(%(process)d) - %(levelname)s - %(message)s',filename="9.0.0_GA_bugs.log" ,level=logging.DEBUG,filemode='w')

def display_message(x=""):
    # Additional function used to log and print using a single line
    logging.info(x)
    print(x)


def Restart_services():
    display_message("\n========================================================\n")
    display_message("Restarting Services...")
    display_message("\n========================================================\n")

    grid = ib_NIOS.wapi_request('GET', object_type="grid")
    ref = json.loads(grid)[0]['_ref']
    request_restart = ib_NIOS.wapi_request('POST', object_type = ref + "?_function=requestrestartservicestatus")
    restart = ib_NIOS.wapi_request('POST', object_type = ref + "?_function=restartservices")
    sleep(35)
    display_message("\n***************. Restart completed successfully .***************\n")


def start_DHCP_service(fqdn="",grid=""):
#fqdn= config.grid1_master_fqdn or config.grid1_member1_fqdn
#grid= Master,Member1,Member2,All members, etc...
    display_message("\n========================================================\n")
    display_message("Starting DHCP service on "+ grid)
    display_message("\n========================================================\n")

    get_ref = ib_NIOS.wapi_request('GET', object_type="member:dhcpproperties?_return_fields=enable_dhcp", grid_vip=config.grid_vip)
    res = json.loads(get_ref)
    display_message(get_ref)
    for i in res:
        if fqdn in i['_ref']:
            data = {"enable_dhcp": True}
            response = ib_NIOS.wapi_request('PUT', ref=i['_ref'], fields=json.dumps(data), grid_vip=config.grid_vip)
            get_ref = ib_NIOS.wapi_request('GET', object_type="member:dhcpproperties?_return_fields=enable_dhcp", grid_vip=config.grid_vip)
            display_message(get_ref)

            if type(response) == tuple:
                if response[0]==400 or response[0]==401:
                    display_message("FAILURE: Couldnt start DHCP service on one or more members")
                    assert False
                break
            else:
                display_message("SUCCESS: DHCP service started on " + grid)
                assert True
                break
        
        else:
            continue
    display_message("\n***************. End of function - start_DHCP_service().***************\n")


class Bondi_GA_bugs(unittest.TestCase):
                                       
####################### NIOS-86695 ###################################
# Create a custom DHCP optionspace

    @pytest.mark.run(order=1)
    def test_001_NIOS_86695_create_custom_DHCP_optionspace(self):
    
        start_DHCP_service(config.grid1_master_fqdn,"Master")

        display_message("\n========================================================\n")
        display_message("Creating a custom DHCP optionspace")
        display_message("\n========================================================\n")

        get_ref = ib_NIOS.wapi_request('GET', object_type="dhcpoptionspace", grid_vip=config.grid_vip)
        res = json.loads(get_ref)
        display_message(get_ref)

        data = {"name":"DHCP_test_space"}
        response = ib_NIOS.wapi_request('POST', object_type="dhcpoptionspace", fields=json.dumps(data), grid_vip=config.grid_vip)
        display_message(response)

        if response[0]==400 or response[0]==401 or response[0]==404 or response[0]==500:
            display_message("FAILURE: Could not create DHCP option space...")
            assert False
        else:
            display_message()
            display_message("\n--------------------------------------------------------\n")
            display_message("Validating DHCP option space - DHCP_test_space")
            display_message("\n--------------------------------------------------------\n")

            response = ib_NIOS.wapi_request('GET', object_type="dhcpoptionspace?name=DHCP_test_space", grid_vip=config.grid_vip)
            print(response)
            response=json.loads(response)[0]
            display_message(response)

            if 'DHCP_test_space' in response['_ref']:
                display_message(response["_ref"])
                display_message("SUCCESS: DHCP option space was successfully created!")
                assert True
            else:
                display_message("FAILURE: Could not create DHCP option space...")
                assert False


        display_message("\n***************. Test Case 1 Execution Completed .***************\n")


# Create a DHCP option definition for the above DHCP option space

    @pytest.mark.run(order=2)
    def test_002_NIOS_86695_create_DHCP_option_definition(self):

        display_message("\n========================================================\n")
        display_message("Creating DHCP option definiation for the option space 'DHCP_test_space'")
        display_message("\n========================================================\n")

#        get_ref = ib_NIOS.wapi_request('GET', object_type="dhcpoptiondefinition?_return_fields=space,type,code,name", grid_vip=config.grid_vip)
#        res = json.loads(get_ref)
#        display_message(get_ref)

        data = {"name": "policy-filter", "code": 21, "space": "DHCP_test_space", "type": "array of ip-address"}
        response = ib_NIOS.wapi_request('POST', object_type="dhcpoptiondefinition", fields=json.dumps(data), grid_vip=config.grid_vip)
        display_message(response)

        if response[0]==400 or response[0]==401 or response[0]==404 or response[0]==500:
            display_message("FAILURE: Could not create DHCP option space...")
            assert False
        else:
            display_message()
            display_message("\n--------------------------------------------------------\n")
            display_message("Validating DHCP option definition")
            display_message("\n--------------------------------------------------------\n")

            response = ib_NIOS.wapi_request('GET', object_type="dhcpoptiondefinition?space=DHCP_test_space", grid_vip=config.grid_vip)
            print(response)
            response=json.loads(response)[0]
            display_message(response)

            if 'policy-filter' in response['name']:
                display_message(response["_ref"])
                display_message("SUCCESS: DHCP option space was successfully created!")
                assert True
            else:
                display_message("FAILURE: Could not create DHCP option space...")
                assert False


        display_message("\n***************. Test Case 2 Execution Completed .***************\n")


# Restarting Services and validating logs

    @pytest.mark.run(order=3)
    def test_003_NIOS_86695_restart_services_and_validate_logs(self):

        display_message("\n========================================================\n")
        display_message("Restarting services and validate logs")
        display_message("\n========================================================\n")


        log("start","/infoblox/var/infoblox.log",config.grid_vip)
        log("start","/var/log/syslog",config.grid_vip)
        sleep(10)
        
        Restart_services()
        
        log("stop","/infoblox/var/infoblox.log",config.grid_vip)
        log("stop","/var/log/syslog",config.grid_vip)

        error_message1 = "Unable to start DHCPv4 service because no valid configuration files are available"
        error_message2 = "No DHCPv4 configuration files found. Rebuilding conf file dhcpd.conf"

        log1=logv(error_message1,"/infoblox/var/infoblox.log",config.grid_vip)
        print(log1)
        log2=logv(error_message2,"/var/log/syslog",config.grid_vip)
        print(log2)
        
        if log1 == None and log2 == None:
            print("SUCCESS: ")
            assert True

        else:
            print("FAILURE: ")
            assert False
        
        display_message("\n***************. Test Case 3 Execution Completed .***************\n")



####################### NIOS-88913 ###################################

