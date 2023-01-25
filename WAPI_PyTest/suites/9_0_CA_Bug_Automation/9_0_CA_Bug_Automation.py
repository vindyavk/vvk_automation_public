#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = "Vindya V K"
__email__  = "vvk@infoblox.com"

#############################################################################
# Grid Set up required:                                                     #
#  1. Grid Master (SA)+ 2 Members (IB_FLEX)  - 9.0.0-48631                  #
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


#####################################################################################################
# BUGS INCLUDED IN THIS SCRIPT:                                                                     #
#                                                                                                   #
# 1. NIOS-86741     (Automated by Vindya)                                                           #
# 2. NIOS-86540     (Automated by Vindya)                                                           #

#####################################################################################################


logging.basicConfig(format='%(asctime)s - %(name)s(%(process)d) - %(levelname)s - %(message)s',filename="9.0_CA_bugs.log" ,level=logging.DEBUG,filemode='w')

def display_message(x=""):
    # Additional function used to log and print using a single line
    logging.info(x)
    print(x)
    
def prepration():
    display_message("Adding core and memory to flex members")

    subprocess.check_output("reboot_system -H "+config.grid1_member1_id+" -a poweroff -c "+config.owner,shell=True)
    subprocess.check_output("reboot_system -H "+config.grid1_member2_id+" -a poweroff -c "+config.owner,shell=True)
    
    subprocess.check_output("vm_specs -H "+config.grid1_member1_id+" -C 8 -M 32 -c "+config.owner,shell=True)
    subprocess.check_output("vm_specs -H "+config.grid1_member2_id+" -C 8 -M 32 -c "+config.owner,shell=True)
    
    subprocess.check_output("reboot_system -H "+config.grid1_member1_id+" -a poweron -c "+config.owner,shell=True)
    subprocess.check_output("reboot_system -H "+config.grid1_member2_id+" -a poweron -c "+config.owner,shell=True)
    
    sleep(400) # Waiting for vms to come up

class Bondi_CA_bugs(unittest.TestCase):

###################### NIOS_86741 ###################################
# Login as admin and execute CLI command 'rotate log syslog'

    @pytest.mark.run(order=1)
    def test_001_NIOS_86741_Executing_CLI_command__rotate_log_syslog(self):
        display_message("\n========================================================\n")
        display_message("Executing CLI command 'rotate log syslog'")
        display_message("\n========================================================\n")

        try:
            child = pexpect.spawn('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no admin@'+config.grid_vip)
            child.logfile=sys.stdout
            child.expect("password:")
            child.sendline("infoblox")
            child.expect("Infoblox >")
            child.sendline("rotate log syslog")
            child.expect("The selected log file has been rotated to syslog.0.gz")
            child.expect("Infoblox >")
            print("SUCCESS: ")
            assert True

        except Exception as e:
            print(e)
            child.close()
            print("FAILURE: ")
            assert False

        finally:
            child.close()

        display_message("\n***************. Test Case 1 Execution Completed .***************\n")


# Login as root and check if /var/log/syslog is present

    @pytest.mark.run(order=2)
    def test_002_NIOS_86741_Checking_for_syslog(self):
        display_message("\n========================================================\n")
        display_message("Logging in as root and checking if syslog folder is peresent ")
        display_message("\n========================================================\n")

        try:
            child = pexpect.spawn('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@'+config.grid_vip)
            child.logfile=sys.stdout
            child.expect(".*#")
            child.sendline("ls -ltr /var/log/syslog* > output.txt")
            child.expect(".*#")
            os.system("sshpass -p 'infoblox' scp -pr root@"+config.grid_vip+":output.txt .")
            
            with open('output.txt') as file:
                output=file.readlines()
                print(type(output))
                if '/var/log/syslog\n' in output[-1]:
                    print("SUCCESS: ")
                    assert True
                else:
                    print("FAILURE: ")
                    assert False

        except Exception as e:
            print(e)
            child.close()
            print("FAILURE: ")
            assert False

        finally:
            child.close()

        display_message("\n***************. Test Case 2 Execution Completed .***************\n")


# Clean Up

    @pytest.mark.run(order=3)
    def test_003_NIOS_86741_cleanup(self):
        display_message("\n============================================\n")
        display_message("CLEANUP: Reverting back to original setup...")
        display_message("\n============================================\n")

        child = pexpect.spawn('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@'+config.grid_vip)
        child.logfile=sys.stdout
        child.expect(".*#")
        child.sendline("rm -rf output.txt")
        child.expect(".*#")
        os.system("rm -rf output.txt")

        print("\n***************. Test Case 3 Execution Completed .***************\n")


###################### NIOS_86540 ###################################
# Login as admin and execute CLI command 'rotate log syslog'

    @pytest.mark.run(order=4)
    def test_004_NIOS_86540_Stop_DHCP_service_on_members(self):
        prepration()

        display_message("\n========================================================\n")
        display_message("Stop DHCP service on members")
        display_message("\n========================================================\n")

        get_ref = ib_NIOS.wapi_request('GET', object_type="member:dhcpproperties?_return_fields=enable_dhcp", grid_vip=config.grid_vip)
        res = json.loads(get_ref)
        for i in res:
            data = {"enable_dhcp": False}
            response = ib_NIOS.wapi_request('PUT', ref=i['_ref'], fields=json.dumps(data), grid_vip=config.grid_vip)
            get_ref = ib_NIOS.wapi_request('GET', object_type="member:dhcpproperties?_return_fields=enable_dhcp", grid_vip=config.grid_vip)
            display_message(get_ref)

            if type(response) == tuple:
                if response[0]==400 or response[0]==401:
                    display_message("FAILURE: Couldnt stop DHCP service on one or more members")
                    assert False
                break
            else:
                display_message("SUCCESS: DHCP service stopped on all members")
                assert True
                break


        display_message("\n***************. Test Case 4 Execution Completed .***************\n")



    @pytest.mark.run(order=5)
    def test_005_NIOS_86540_Start_DNS_service_on_members(self):
        display_message("\n========================================================\n")
        display_message("Start DNS service on members")
        display_message("\n========================================================\n")

        get_ref = ib_NIOS.wapi_request('GET', object_type="member:dns?_return_fields=enable_dns", grid_vip=config.grid_vip)
        res = json.loads(get_ref)
        for i in res:
            if config.grid1_member1_fqdn in i['_ref'] or config.grid1_member2_fqdn in i['_ref']:
                data = {"enable_dns": True}
                response = ib_NIOS.wapi_request('PUT', ref=i['_ref'], fields=json.dumps(data), grid_vip=config.grid_vip)
                get_ref = ib_NIOS.wapi_request('GET', object_type="member:dns?_return_fields=enable_dns", grid_vip=config.grid_vip)
                display_message(get_ref)

                if type(response) == tuple:
                    if response[0]==400 or response[0]==401:
                        display_message("FAILURE: Couldnt start DNS service on one or more members")
                        assert False
                    break
                else:
                    display_message("SUCCESS: DNS service started on all members")
                    assert True
                    break
            
            else:
                continue


        display_message("\n***************. Test Case 5 Execution Completed .***************\n")
        
        
        
    @pytest.mark.run(order=6)
    def test_006_NIOS_86540_Start_DCS_service_on_members(self):
        display_message("\n========================================================\n")
        display_message("Start DCA service on members")
        display_message("\n========================================================\n")

        get_ref = ib_NIOS.wapi_request('GET', object_type="member:dns?_return_fields=enable_dns_cache_acceleration", grid_vip=config.grid_vip)
        res = json.loads(get_ref)
        for i in res:
            if config.grid1_member1_fqdn in i['_ref'] or config.grid1_member2_fqdn in i['_ref']:
                data = {"enable_dns_cache_acceleration": True}
                response = ib_NIOS.wapi_request('PUT', ref=i['_ref'], fields=json.dumps(data), grid_vip=config.grid_vip)
                get_ref = ib_NIOS.wapi_request('GET', object_type="member:dns?_return_fields=enable_dns_cache_acceleration", grid_vip=config.grid_vip)
                display_message(get_ref)

                if type(response) == tuple:
                    if response[0]==400 or response[0]==401:
                        display_message("FAILURE: Couldnt start DCA service on one or more members")
                        assert False
                    break
                else:
                    display_message("SUCCESS: DCA service started on all members")
                    assert True
                    break
            
            else:
                continue


        display_message("\n***************. Test Case 6 Execution Completed .***************\n")



    @pytest.mark.run(order=7)
    def test_007_NIOS_86540_Start_TP_service_on_members(self):
        display_message("\n========================================================\n")
        display_message("Start TP service on members")
        display_message("\n========================================================\n")

        get_ref = ib_NIOS.wapi_request('GET', object_type="member:threatprotection?_return_fields=enable_service", grid_vip=config.grid_vip)
        res = json.loads(get_ref)
        for i in res:
            if config.grid1_member1_fqdn in i['_ref'] or config.grid1_member2_fqdn in i['_ref']:
                data = {"enable_service": True}
                response = ib_NIOS.wapi_request('PUT', ref=i['_ref'], fields=json.dumps(data), grid_vip=config.grid_vip)
                get_ref = ib_NIOS.wapi_request('GET', object_type="member:threatprotection?_return_fields=enable_service", grid_vip=config.grid_vip)
                display_message(get_ref)

                if type(response) == tuple:
                    if response[0]==400 or response[0]==401:
                        display_message("FAILURE: Couldnt start TP service on one or more members")
                        assert False
                    break
                else:
                    display_message("SUCCESS: TP service started on all members")
                    assert True
                    break
            
            else:
                continue


        display_message("\n***************. Test Case 7 Execution Completed .***************\n")


    @pytest.mark.run(order=8)
    def test_008_NIOS_86540_Enable_Parental_control_and_add_site_with_members(self):
        display_message("\n========================================================\n")
        display_message("Enable Parental control and add a site with members")
        display_message("\n========================================================\n")

        get_ref = ib_NIOS.wapi_request('GET', object_type="parentalcontrol:subscriber?_return_fields=enable_parental_control", grid_vip=config.grid_vip)
        res = json.loads(get_ref)[0]

        data = {"enable_parental_control": True, "cat_acctname": "vvk", "cat_update_frequency": 24, "category_url": "https://dl.zvelo.com/", "pc_zone_name": "vvk"}
        response = ib_NIOS.wapi_request('PUT', ref=res['_ref'], fields=json.dumps(data), grid_vip=config.grid_vip)
        get_ref = ib_NIOS.wapi_request('GET', object_type="parentalcontrol:subscriber?_return_fields=enable_parental_control", grid_vip=config.grid_vip)
        display_message(get_ref)

        if type(response) == tuple:
            if response[0]==400 or response[0]==401:
                display_message("FAILURE: Could not enable Parental control")
                assert False
            
        else:
            display_message("SUCCESS: Parental control enabled successfully\n")

        
        ### Adding site with members ###
        data = {"name": "vvk_site", "members":[{"name":config.grid1_member1_fqdn},{"name":config.grid1_member2_fqdn}]}
        response = ib_NIOS.wapi_request('POST', object_type="parentalcontrol:subscribersite", fields=json.dumps(data), grid_vip=config.grid_vip)
        display_message(response)
        get_ref = ib_NIOS.wapi_request('GET', object_type="parentalcontrol:subscribersite?_return_fields=members,name", grid_vip=config.grid_vip)
        display_message(get_ref)

        if type(response) == tuple:
            if response[0]==400 or response[0]==401:
                display_message("FAILURE: Could not add Parental control site")
                assert False
            
        else:
            display_message("SUCCESS: Parental control site added successfully with members")
            assert True
          

        display_message("\n***************. Test Case 8 Execution Completed .***************\n")


    @pytest.mark.run(order=9)
    def test_009_NIOS_86540_Restarting_services(self):
        display_message("\n========================================================\n")
        display_message("Restarting Services...")
        display_message("\n========================================================\n")

        grid = ib_NIOS.wapi_request('GET', object_type="grid")
        ref = json.loads(grid)[0]['_ref']
        request_restart = ib_NIOS.wapi_request('POST', object_type = ref + "?_function=requestrestartservicestatus")
        restart = ib_NIOS.wapi_request('POST', object_type = ref + "?_function=restartservices")
        sleep(35)
        display_message("Restart completed successfully")

        display_message("\n***************. Test Case 9 Execution Completed .***************\n")


    @pytest.mark.run(order=10)
    def test_010_NIOS_86540_Validating_synopsis_for__set_subscriber_secure_data(self):
        display_message("\n========================================================\n")
        display_message("Executing CLI command 'set subscriber_secure_data' and validating 'Synopsis' for 'set subscriber_secure_data'")
        display_message("\n========================================================\n")

        try:
            child = pexpect.spawn('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no admin@'+config.grid1_member1_vip)
            child.logfile=sys.stdout
            child.expect("password:")
            child.sendline("infoblox")
            child.expect("Infoblox >")
            child.sendline("set subscriber_secure_data ?")
            child.expect("Infoblox >")
            output=child.before
            
            wrong_synopsis = "set subscriber_secure_data bypass <on|off> [grid | site <\"site-name\">]"
            wrong_description = "Use \"set subscriber_secure_data bypass <on|off> [grid | site <\"site-name\">]\" to configure bypass subscriber service policies on entire grid, all members of the given site or local member only"
            
            correct_synopsis = "set subscriber_secure_data bypass <on|off>"
            correct_description = "Use \"set subscriber_secure_data bypass <on | off>\" to configure bypass subscriber service policies on the given member"
            
            if (wrong_synopsis in output) or (wrong_description in output):
                print("FAILURE: Something went wrong...please check and reopen the bug.")
                assert False
                
            elif (correct_synopsis in output) and (correct_description in output):
                print("SUCCESS: Synopsis and description for 'subscriber_secure_data bypass' is correct.")
                assert True

        except Exception as e:
            print(e)
            child.close()
            print("FAILURE: Something went wrong...please check and reopen the bug.")
            assert False

        finally:
            child.close()

        display_message("\n***************. Test Case 10 Execution Completed .***************\n")


    @pytest.mark.run(order=11)
    def test_011_NIOS_86540_Validating_synopsis_for__set_subscriber_secure_data_bypass(self):
        display_message("\n========================================================\n")
        display_message("Executing CLI command 'show subscriber_secure_data' and validating 'Synopsis' for 'show subscriber_secure_data bypass'")
        display_message("\n========================================================\n")

        try:
            child = pexpect.spawn('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no admin@'+config.grid1_member1_vip)
            child.logfile=sys.stdout
            child.expect("password:")
            child.sendline("infoblox")
            child.expect("Infoblox >")
            child.sendline("set subscriber_secure_data ?")
            child.expect("Infoblox >")
            output=child.before
            
            wrong_synopsis = "show subscriber_secure_data bypass [grid | site] [\"site-name\"]"
            wrong_description = "EX: show subscriber_secure_data bypass site \"Site1\""
            
            correct_synopsis = "show subscriber_secure_data bypass"
            correct_description = "EX: show subscriber_secure_data bypass"
            
            if (wrong_synopsis in output) or (wrong_description in output):
                print("FAILURE: Something went wrong...please check and reopen the bug.")
                assert False
                
            elif (correct_synopsis in output) and (correct_description in output):
                print("SUCCESS: Synopsis and description for 'subscriber_secure_data bypass' is correct.")
                assert True

        except Exception as e:
            print(e)
            child.close()
            print("FAILURE: Something went wrong...please check and reopen the bug.")
            assert False

        finally:
            child.close()

        display_message("\n***************. Test Case 11 Execution Completed .***************\n")
