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
# 3. NIOS-89203     (Automated by Rizvi)                                                            #
# 4. NIOS-89518     (Automated by Rizvi)                                                            #
# 5. NIOS-89426     (Automated by Rizvi)                                                            #
# 6. NIOS-88861     (Automated by Rizvi)                                                            #
# 7. NIOS-86458     (Automated by Rizvi)                                                            #
# 8. NIOS-89017     (Automated by Rizvi)                                                            #
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
                                       
####################### NIOS-86695 ###################################          >>> VINDYA <<<
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


####################### NIOS-89203 ###################################      >>> RIZVI <<<

      @pytest.mark.run(order=1)
      def test_001_NIOS_89203_Validate_set_debug_tools_synopsis(member):

        child = pexpect.spawn('ssh -o StrictHostKeyChecking=no admin@'+config.grid_vip)
        child.logfile=sys.stdout
        child.expect('password:')
        child.sendline('infoblox')
        child.expect('Infoblox >')
        child.sendline('set maintenancemode')
        child.expect('Maintenance Mode ')
        child.sendline('set debug_tools')
        child.expect('Maintenance Mode >')
        c=child.before
        child.close()
        if "set debug_tools remove_tcpdump_log" in c:
            print("remove_tcpdump_log is displayed in synopsis of set debug tools")
            assert True
        else:
            assert False
            print("remove_tcpdump_log is  not displayed in  synopsis of set debug tools")
            
            
####################### NIOS-89518 ###################################
      
      @pytest.mark.run(order=2)
      def test_002_NIOS_89518_add_forwarder_enable_recursion_queries_responses(self):
          Restart_services()
          get_grid_dns_ref = ib_NIOS.wapi_request('GET', object_type='grid:dns')
          grid_dns_ref = json.loads(get_grid_dns_ref)[0]['_ref']
          data = {"allow_recursive_query": True,"logging_categories":{"log_queries": True,'log_responses': True} ,"forwarders":[config.grid2_master_vip]}
          response = ib_NIOS.wapi_request('PUT', ref=grid_dns_ref, fields=json.dumps(data))
          display_message("Response for enable recursion  ,queries,responses and filter_aaaa on Grid DNS")
          display_message(response)
          if bool(re.match("\"grid:dns*.",str(response))):
            display_message("Recursion,queries,responses  enabled and forwarder added ")
            Restart_services()
            assert True
          else:
            display_message("recursion,queries,responses  not enabled  and add forwarder failed")
            assert False

       
      @pytest.mark.run(order=3)
      def test_003_NIOS_89518_add_syslog_backup_size_sever(self):
        get_grid_ref = ib_NIOS.wapi_request('GET', object_type='grid')
        grid_ref= json.loads(get_grid_ref)[0]['_ref']
        data={"external_syslog_backup_servers": [{"address": config.client_ip,"directory_path": "/tmp","enable": True,"port": 22,"protocol": "SCP","username": config.client_user,"password":config.client_password}],  "syslog_size": 10}
        response = ib_NIOS.wapi_request('PUT', ref=grid_ref, fields=json.dumps(data))
        display_message("Response for enable recursion  ,queries,responses and filter_aaaa on Grid DNS")
        display_message(response)
        if bool(re.match("\"grid*.",str(response))):
            display_message("SCP server and sysslog size  added successfully")
            Restart_services()
            assert True
        else:
            display_message("SCP server and sysslog size  not added successfully")
            assert False
    
        
      @pytest.mark.run(order=4)
      def test_004_NIOS_89518_rotate_sys_log(self):
            log("start","/infoblox/var/infoblox.log",config.grid_vip)
            child = pexpect.spawn('ssh -o StrictHostKeyChecking=no admin@'+config.grid_vip)
            child.logfile=sys.stdout
            child.expect('password:')
            child.sendline('infoblox')
            child.expect('Infoblox >')
            child.sendline('rotate log syslog')
            child.expect('Infoblox >')
            output=child.before
            print("RIZ",output)
            child.close()
            if  "The selected log file has been rotated to syslog.0.gz" in output:
                assert True
                display_message("The syslog has been rotated successfully")
            else:
                assert False
                display_message("The syslog rotation unsuccessful")
                
      @pytest.mark.run(order=5)
      def test_005_NIOS_89518_Validate_infoblox_log(self):
            display_message("Validate /infoblox/var/infoblox.log  for errors ")
            log("stop","/infoblox/var/infoblox.log",config.grid_vip)
            
            log1=logv("Syslog backup (Backup of rotated syslog file successfully completed. Sending rotated syslog file '/var/log/syslog.0.gz' to the SCP server on "+ config.client_ip,"/infoblox/var/infoblox.log",config.grid_vip)
            if log1 :
                display_message("syslog  is copied successflly toscp server")
                assert True
            else:
                display_message("syslog is not copied successfully to scp server")
                assert False

      @pytest.mark.run(order=6)
      def test_006_NIOS_89518_Validate_client_server(self):
            child = pexpect.spawn('ssh -o StrictHostKeyChecking=no '+config.client_user+'@'+config.client_ip,timeout=30)
            child.logfile=sys.stdout
            child.expect(':')
            child.sendline('infoblox')
            child.expect('~]\$')
            child.sendline('ls -ltr /tmp')
            child.expect('~]\$')
            output=child.before
            child.close()
            print(output)
            if "syslog.0.gz" in output:
                assert True
                display_message ("syslog.0.gz file is present on scp server")
            else:
                assert False
                display_message("syslog.0.gz file is not  present on scp server")
    
    
    
####################### NIOS-89426 ###################################
    
      
      @pytest.mark.run(order=7)
      def test_007_NIOS_89426_Validate_Ext_server_log_DNSUNBOUND(self):
        grid =  ib_NIOS.wapi_request('GET', object_type="grid")
        ref = json.loads(grid)[0]['_ref']
        data = {'syslog_servers': [{'address': '1.1.1.1','category_list': ['DNS_IDNSD',],'only_category_list': True}]}
        response = ib_NIOS.wapi_request('PUT', object_type =ref,fields=json.dumps(data))
        if response!=400 or 401 or 402:
            if "DNS_UNBOUND" in response:
                assert False
                display_message("Print DNS_UNBOUND is listing in External Servers log list")
            else:
                assert True
                display_message("Print DNS_UNBOUND is not listing in External Servers log list")
        else:
                display_message("Print DNS_UNBOUND is not listing in External Servers log list")
    
    
####################### NIOS-88861 ###################################
    
      @pytest.mark.run(order=8)
      def test_008_NIOS_88861_create_nonsuperuser_group(self):
        print("\n====================================")
        print("create_nonsuperuser_group")
        print("======================================")
        data={"name":"grp1","access_method": ["API","GUI"]}
        response = ib_NIOS.wapi_request('POST',object_type="admingroup",fields=json.dumps(data))
        print(response)
        if type(response) == tuple:
            if response[0]==400 or response[0]==401:
                print("Failure: group not created")
                assert False
        else:
            print("Success: created non super user group")
            assert True
    
      @pytest.mark.run(order=9)
      def test_009_NIOS_88861_create_nonsuperuser(self):
        print("\n====================================")
        print("create_nonsuperuser_user")
        print("======================================")
        
        data = {"name":config.non_su_user_name,"password":config.non_su_password,"admin_groups": ["grp1"]}
        response = ib_NIOS.wapi_request('POST',object_type="adminuser",fields=json.dumps(data))
        print(response)
        sleep(30)
        if type(response) == tuple:
            if response[0]==400 or response[0]==401:
                print("Failure: user not created")
                assert False
        else:
            print("Success: created non super user ")
            assert True

      @pytest.mark.run(order=10)
      def test_010_NIOS_88861_import_CSV_file(self):
        log("start","/infoblox/var/infoblox.log",config.grid_vip)
        Restart_services()
        print("Importing test.csv filie...")
        dir_name = os.getcwd()
        base_filename =config.file_name
        token = common_util.generate_token_from_file(dir_name,base_filename)
        print(token)
        new_token=str(token)
        data = {"token":new_token,"action":"START", "doimport":True, "on_error":"CONTINUE","update_method":"OVERRIDE"}
        response = ib_NIOS.wapi_request("POST", object_type="fileop", fields=json.dumps(data),params="?_function=csv_import",user="infoblox1", password="infoblox1")
        print(response)
        if  response[0]==400 and "CSV import permission is required to import a CSV file." in response[1] :
                print("You don not have permissions to  import csv file")
                assert True
        else:
            print("Success: Import test.csv file")
            assert False
        print("Restart DNS Services")
        grid =  ib_NIOS.wapi_request("GET", object_type="grid", grid_vip=config.grid_vip)
        ref = json.loads(grid)[0]["_ref"]
        data= {"member_order" : "SIMULTANEOUSLY","restart_option":"FORCE_RESTART","service_option": "ALL"}
        request_restart = ib_NIOS.wapi_request("POST", object_type = ref + "?_function=restartservices",fields=json.dumps(data),grid_vip=config.grid_vip)
        sleep(20)

    
      @pytest.mark.run(order=11)
      def test_011_NIOS_88861_Validate_infoblox_log(self):
            display_message("Validate /infoblox/var/infoblox.log  for errors ")
            log("stop","/infoblox/var/infoblox.log",config.grid_vip)

            log1=logv("com.infoblox.exception.IbapServerInternalErrorException: com.infoblox.model.ibap.Fault_Exception: Internal Error","/infoblox/var/infoblox.log",config.grid_vip)
            if log1 :
                display_message("Import csv file success")
                assert False
            else:
                display_message("Import csv file unsuccessful")
                assert True
      
      
####################### NIOS-86458 ###################################
      
      @pytest.mark.run(order=12)
      def test_012_test_NIOS_86458_Create_authzone_Unknown_record_type_APL(self):
        log("start","/infoblox/var/infoblox.log",config.grid_vip)
        display_message("Create auth zone")

        data = {"fqdn":"rz1.com","view":"default","grid_primary":[{"name":config.grid1_master_fqdn}]}
        response = ib_NIOS.wapi_request('POST', object_type="zone_auth", fields=json.dumps(data), grid_vip=config.grid_vip)
        display_message(response)
        if type(response)== tuple:
            display_message("Creating auth_zone Failed")
            assert False
        else:
            display_message("Creating auth_zone  Success")
            Restart_services()
            assert True


      @pytest.mark.run(order=13)
      def test_013_test_NIOS_86458_Create_authzone_Unknown_record_type_APL(self):
        display_message("Create Unknwon record with TYPE APL")
        log("stop","/infoblox/var/infoblox.log",config.grid_vip)
        data={"name": "h1.rz1.com","record_type": "APL","subfield_values": []}
        response=ib_NIOS.wapi_request('POST', object_type="record:unknown", fields=json.dumps(data), grid_vip=config.grid_vip)
        display_message(response)
        if type(response)== tuple:
            display_message("Creating Unknown record with TYPE APL  Failed")
            assert False
        else:
            display_message("Creating Unknown record with TYPE APL  Success")
            assert True

      @pytest.mark.run(order=14)
      def test_014_test_NIOS_86458_Validate_Infoblox_log_for_errors(self):
        display_message("Validate Infoblox.log for errors ")
        log("stop","/infoblox/var/infoblox.log",config.grid_vip)
        log1=logv(".*Required Value(s) Missing: record_rdata_hash.*","/infoblox/var/infoblox.log",config.grid_vip)
        if log1 :
            display_message("Error log message found")
            assert False
        else:
            display_message("No Error logs found")
            assert True
      
      
####################### NIOS-89017 ###################################
      
      @pytest.mark.run(order=15)
      def test_015_NIOS_89017_Create_IPv4_Container_in_defaultnetwork_view(self):
                logging.info("Create an IPv4 Container in defaultnetwork view")
                network_data = {"network":"10.0.0.0/8","network_view": "default"}
                response = ib_NIOS.wapi_request('POST', object_type="networkcontainer", fields=json.dumps(network_data), grid_vip=config.grid_vip)
                print (response)
                print("Created the ipv4 container in default view")
                logging.info("Restart DHCP Services")
                grid =  ib_NIOS.wapi_request('GET', object_type="grid",grid_vip=config.grid_vip)
                ref = json.loads(grid)[0]['_ref']
                data= {"member_order" : "SIMULTANEOUSLY","restart_option":"FORCE_RESTART","service_option": "ALL"}
                sleep(20)
                print("Network Container  Execution Completed")
            
                logging.info("Verify an ipv4 container")
                new_data =  ib_NIOS.wapi_request('GET', object_type="networkcontainer?_return_fields=subscribe_settings,network", grid_vip=config.grid_vip)
                response = eval(json.dumps(new_data))
                sleep(10)
                print(response)
                if('"network": "10.0.0.0/8"')in response:
                        assert True
                        print("Network Container Execution verified")
                else:
                        assert False
                        print("Network Container Execution not verified")
        
      @pytest.mark.run(order=16)
      def test_016_NIOS_89017_Create_IPv4_Network(self):
        network_data = {"network": "10.0.0.0/16","network_view": "default","members":[{"_struct": "dhcpmember","ipv4addr":config.grid_vip}]}
        #network_data = {"network": "20.0.0.0/8",
         #               "members": [{"_struct": "dhcpmember", "ipv4addr": config.master01lan1v4, "name": config.grid_fqdn}],
          #              "extattrs": {"IB Discovery Owned": {"value": "ib"}}}
        response = ib_NIOS.wapi_request('POST', object_type="network", fields=json.dumps(network_data),grid_vip=config.grid1_master_vip)
        #print(response)
        #read = re.search(r'201', response)
        #for read in response:
         #   assert True
        #print("Created the ipv4network 10.0.0.0/16 in default view")
        logging.info("Restart DHCP Services")
        grid = ib_NIOS.wapi_request('GET', object_type="grid",grid_vip=config.grid1_master_vip)
        ref = json.loads(grid)[0]['_ref']
        data = {"member_order": "SIMULTANEOUSLY", "restart_option": "FORCE_RESTART", "service_option": "ALL"}
        request_restart = ib_NIOS.wapi_request('POST', object_type=ref + "?_function=restartservices",
                                               fields=json.dumps(data),grid_vip=config.grid1_master_vip)
        logging.info("Wait for 15 seconds")
        sleep(15)
        new_data = ib_NIOS.wapi_request('GET', object_type="network",grid_vip=config.grid1_master_vip)
        new_data = json.loads(new_data)
        print("result of adding ipv4 network", new_data)
       # print("data",data)
        sleep(20)  # wait for 20 secs for the member to get started
        if (new_data[0]['network'] == network_data["network"]):
            assert True
            print("10.0.0.0/16 network added successfully")
        else:
            assert False
            print("10.0.0.0/16 network addition failed")
        

      @pytest.mark.run(order=17)
      def test_017_NIOS_89017_Create_Auth_zone(self):
        display_message("Create auth zone")

        data = {"fqdn":"test_nx21.com","view":"default","grid_primary":[{"name":config.grid1_master_fqdn}]}
        response = ib_NIOS.wapi_request('POST', object_type="zone_auth", fields=json.dumps(data), grid_vip=config.grid_vip)
        display_message(response)
        if type(response)== tuple:
            display_message("Creating auth_zone Failed")
            assert False
        else:
            display_message("Creating auth_zone  Success")
            Restart_services()
            assert True

      @pytest.mark.run(order=18)
      def test_018_NIOS_89017_Host_record(self):
        data ={"ipv4addrs": [{"configure_for_dhcp": False,"ipv4addr": "10.0.0.16"}], "name": "h3.test_nx21.com","view": "default","use_ttl":True,"ttl":8400}
        response = ib_NIOS.wapi_request('POST', object_type="record:host", fields=json.dumps(data), grid_vip=config.grid_vip)
        print(response)
        #read  = re.search(r'201',response)
        #for read in  response:
         #       assert True
       # logging.info("Host record created for the zone h3.test_nx21.com and network 10.0.0.0/16")
        get_ref = ib_NIOS.wapi_request('GET', object_type="record:host", grid_vip=config.grid_vip)
        print(get_ref)

        ref2= json.loads(get_ref)[0]['_ref']
        print("#### Reference",ref2)
        if "h3.test_nx21.com" in ref2:
            print("Host record created for the zone h3.test_nx21.com and network 10.0.0.0/16")
        else:
            print("Host record created for the zone h3.test_nx21.com and network 10.0.0.0/16")
        ttl_data={"ttl":9600}
        response2=ib_NIOS.wapi_request('PUT', ref=ref2 ,object_type="record:host",fields=json.dumps(ttl_data), grid_vip=config.grid_vip)
        if response2[0]==400 or response2[0]==401 or response2[0]==402:
                print("Host record TTL Tab update failed")
        else:
                print("Host record TTL Tab update success")
        

      @pytest.mark.run(order=19)
      def test_019_NIOS_89017_Validate_sys_log_for_errors(self):
        display_message("Validate var/log/syslog for errors ")
        log("stop","/var/log/syslog",config.grid_vip)
        log1=logv("Attempt to insert object with the same key as an already existing object","/var/log/syslog",config.grid_vip)
        if log1 :
            display_message("Error logs found")
            assert False
        else:
            display_message("No Error logs found")
            assert True



