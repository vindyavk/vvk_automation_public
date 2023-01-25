import re
#import pdb
import config
import pytest
import unittest
import logging
import subprocess
import os
import json
import ib_utils.ib_NIOS as ib_NIOS
#import commands
import json, ast
import requests
from time import sleep as sleep
import pexpect
import paramiko
import time
import sys
from paramiko import client
#from logger import logger
from ib_utils.start_stop_logs import log_action as log
from ib_utils.file_content_validation import log_validation as logv
from ib_utils.ib_system import search_dump as search_dump
from ib_utils.ib_validaiton import compare_results as compare_results


"""
TEST Steps:
      1.  Input/Preparaiton      : Create a network, Range and request leases
      2.  Search                 : Search with Default Filter
      3.  Validation             : Validating Search result against input data
"""



def start_subscriber_collection_services_for_added_site(member):
    for mem in member:
        get_ref=ib_NIOS.wapi_request('GET', object_type='member:parentalcontrol?name='+mem)
        get_ref=json.loads(get_ref)
        ref=get_ref[0]["_ref"]
        print ref
        logging.info(ref)
        data={"enable_service":True}
        reference=ib_NIOS.wapi_request('PUT', object_type=ref,fields=json.dumps(data))
        logging.info(reference)
        print reference
        grid =  ib_NIOS.wapi_request('GET', object_type="grid")
        ref = json.loads(grid)[0]['_ref']
        publish={"member_order":"SIMULTANEOUSLY"}
        request_publish = ib_NIOS.wapi_request('POST', object_type = ref + "?_function=publish_changes",fields=json.dumps(publish))
        time.sleep(1)
        request_restart = ib_NIOS.wapi_request('POST', object_type = ref + "?_function=requestrestartservicestatus")
        restart = ib_NIOS.wapi_request('POST', object_type = ref + "?_function=restartservices")
        time.sleep(20)
        for mem in member:
            get_ref=ib_NIOS.wapi_request('GET', object_type='member:parentalcontrol?name='+mem)
            get_ref=json.loads(get_ref)
            if get_ref[0]["enable_service"]==True:
                return True
                print("subscriber service is started in "+mem)
            else:
                return None
                print("Not able to start subscriber service "+mem)
        time.sleep(40)

def mem_ref_string_pc(hostname):
    response = ib_NIOS.wapi_request('GET', object_type="member:parentalcontrol")
    logging.info(response)
    if type(response)!=tuple:
        ref1 = json.loads(response)
        for key in ref1:
            if key.get('name') == hostname:
                mem_ref = key.get('_ref')
                break
    else:
        print("Failed to get member ref string")
        mem_ref = "NIL"

    return mem_ref

def change_default_route():
    ref=ib_NIOS.wapi_request('GET', object_type="grid")
    print("#############",ref)
    ref=json.loads(ref)[0]['_ref']
    #data={"dns_resolver_setting": {"resolvers": [config.resolver_ip]}}
    data={"dns_resolver_setting": {"resolvers": ["10.120.3.10"]}}
    ref1=ib_NIOS.wapi_request('PUT', object_type=ref,fields=json.dumps(data))
    child = pexpect.spawn('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@'+config.grid_vip)
    child.logfile=sys.stdout
    child.expect('#')
    child.sendline('ip route del default via 10.35.0.1 dev eth1 table main')
    child.expect('#')
    child.sendline('ip route add default via 10.36.0.1 dev eth0 table main')
    child.sendline('exit')
    child.expect(pexpect.EOF)
    time.sleep(20)

def enable_mgmt_port_for_dns():
    ref=ib_NIOS.wapi_request('GET', object_type="member:dns")
    ref=json.loads(ref)[0]['_ref']
    data={"use_mgmt_port":True}
    ref1=ib_NIOS.wapi_request('PUT', object_type=ref,fields=json.dumps(data))
    logging.info (ref1)
    time.sleep(120)
    
def Start_DCA_service():
    logging.info("starting DCA service in the Grid Master...\n")
    get_ref = ib_NIOS.wapi_request('GET', object_type="member:dns", grid_vip=config.grid_vip)
    logging.info(get_ref)
    print get_ref
    res = json.loads(get_ref)
    print res
    ref1 = json.loads(get_ref)[0]['_ref']
    data = {"enable_dns": True,"enable_dns_cache_acceleration": True}
    response = ib_NIOS.wapi_request('PUT',ref=ref1,fields=json.dumps(data), grid_vip=config.grid_vip)
    print response
    sleep(10)
    print (response)
    sleep(30)
    print("DCA service started in the Grid Master")


def enable_GUI_and_API_access_through_LAN_and_MGMT():
    ref=ib_NIOS.wapi_request('GET', object_type="grid",grid_vip=config.grid_vip)
    logging.info (ref)
    ref=json.loads(ref)[0]['_ref']
    logging.info(ref)
    data={"enable_gui_api_for_lan_vip":True}
    ref1=ib_NIOS.wapi_request('PUT', object_type=ref,fields=json.dumps(data),grid_vip=config.grid_vip)
    logging.info (ref1)
    time.sleep(120)


def stop_subscriber_collection_services_for_added_site(member):#config.grid_fqdn
    get_ref=ib_NIOS.wapi_request('GET', object_type='member:parentalcontrol?name='+member)
    get_ref=json.loads(get_ref)
    ref=get_ref[0]["_ref"]
    logging.info(ref)
    data={"enable_service":False}
    reference=ib_NIOS.wapi_request('PUT', object_type=ref,fields=json.dumps(data))
    logging.info(reference)
    grid =  ib_NIOS.wapi_request('GET', object_type="grid")
    ref = json.loads(grid)[0]['_ref']
    publish={"member_order":"SIMULTANEOUSLY"}
    request_publish = ib_NIOS.wapi_request('POST', object_type = ref + "?_function=publish_changes",fields=json.dumps(publish))
    time.sleep(1)
    request_restart = ib_NIOS.wapi_request('POST', object_type = ref + "?_function=requestrestartservicestatus")
    restart = ib_NIOS.wapi_request('POST', object_type = ref + "?_function=restartservices")
    get_ref=ib_NIOS.wapi_request('GET', object_type='member:parentalcontrol?name='+member)
    get_ref=json.loads(get_ref)
    if get_ref[0]["enable_service"]==False:
        logging.info ("Test case passed")
        time.sleep(40)
        logging.info ("subscriber service is stopped")
        return get_ref[0]["enable_service"]
    else:
        logging.info("Not able to stop subscriber service")
        return None



class  Query_Count_details_by_subscriber_id(unittest.TestCase):

    @pytest.mark.run(order=1)
    def test_001_Start_DNS_Service(self):
        enable_mgmt_port_for_dns()
        Start_DCA_service()
        sleep(200)
        change_default_route()
        logging.info("Start DNS Service")
        get_ref = ib_NIOS.wapi_request('GET', object_type="member:dns")
        logging.info(get_ref)
        logging.info(get_ref)
        res = json.loads(get_ref)
        for i in res:
            ref=i["_ref"]
            logging.info("Modify a enable_dns")
            data = {"enable_dns": True}
            response = ib_NIOS.wapi_request('PUT', ref=ref, fields=json.dumps(data))
            sleep(20)
            logging.info(response)
            read  = re.search(r'200',response)
            for read in  response:
                assert True
        logging.info("Test Case 5 Execution Completed")

    @pytest.mark.run(order=2)
    def test_002_Validate_DNS_service_Enabled(self):
        logging.info("Validate DNS Service is enabled")
        get_tacacsplus = ib_NIOS.wapi_request('GET', object_type="member:dns",params="?_return_fields=enable_dns")
        print(get_tacacsplus)
        logging.info(get_tacacsplus)
        res = json.loads(get_tacacsplus)
        logging.info(res)
        for i in res:
            logging.info("found")
            assert i["enable_dns"] == True
        logging.info("Test Case 6 Execution Completed")
        logging.info("============================")

    @pytest.mark.run(order=3)
    def test_003_modify_grid_dns_properties(self):
        logging.info("Mofifying GRID dns properties")
        get_ref=ib_NIOS.wapi_request('GET', object_type="grid:dns")
        get_ref1=json.loads(get_ref)[0]['_ref']
        logging.info(get_ref1)
        #data={"allow_recursive_query":True,"allow_query":[{"_struct": "addressac","address":"Any","permission":"ALLOW"}],"forwarders":[config.forwarder_ip],"logging_categories":{"log_rpz":True,"log_queries":True,"log_responses":True}}
        data={"allow_recursive_query":True,"allow_query":[{"_struct": "addressac","address":"Any","permission":"ALLOW"}],"forwarders":["10.39.16.160"],"logging_categories":{"log_rpz":True,"log_queries":True,"log_responses":True}}
        put_ref=ib_NIOS.wapi_request('PUT', object_type=get_ref1,fields=json.dumps(data))
        logging.info(put_ref)
        if type(put_ref)!=tuple:
            logging.info("Test Case 8 Execution Passed")
            assert True
        else:
            logging.info("Test Case 8 Execution Failed")
            assert False

    @pytest.mark.run(order=4)
    def test_004_validate_grid_dns_properties(self):
        logging.info("Validating GRID dns properties")
        get_ref=ib_NIOS.wapi_request('GET', object_type="grid:dns?_return_fields=allow_recursive_query,forwarders")
        get_ref1=json.loads(get_ref)
        #if get_ref1[0]["allow_recursive_query"]==True and get_ref1[0]["forwarders"]==[config.forwarder_ip]:
        if get_ref1[0]["allow_recursive_query"]==True and get_ref1[0]["forwarders"]==["10.39.16.160"]:
            logging.info("Test Case 8 Execution Passed")
            assert True
        else:
            logging.info("Test Case 8 Execution Failed")
            assert False

    @pytest.mark.run(order=5)
    def test_005_modify_grid_settings(self):
        logging.info("Mofifying GRID properties")
        response = ib_NIOS.wapi_request('GET', object_type="grid")
        response = json.loads(response)
        response=response[0]["_ref"]
        #data={"dns_resolver_setting": {"resolvers": [config.resolver_ip]}}
        data={"dns_resolver_setting": {"resolvers": ["127.0.0.1"]}}
        res = ib_NIOS.wapi_request('PUT', object_type=response,fields=json.dumps(data))
        print(res)
        logging.info(res)
        if type(res)!=tuple:
            logging.info("Test Case 9 Execution Passed")
            assert True
        else:
            logging.info("Test Case 9 Execution Failed")
            assert False

    @pytest.mark.run(order=6)
    def test_006_validate_grid_settings(self):
        logging.info("Validating GRID properties")
        response = ib_NIOS.wapi_request('GET', object_type="grid?_return_fields=dns_resolver_setting")
        response = json.loads(response)
        response=response[0]["dns_resolver_setting"]["resolvers"]
        #if response==[config.resolver_ip]:
        if response==["127.0.0.1"]:
            logging.info("Test Case 10 Execution Passed")
            assert True
        else:
            logging.info("Test Case 10 Execution Failed")
            assert False

    @pytest.mark.run(order=7)
    def test_007_enable_parental_control(self):
        logging.info("enabling parental control")
        response = ib_NIOS.wapi_request('GET', object_type="parentalcontrol:subscriber")
        response = json.loads(response)
        response=response[0]["_ref"]
        logging.info(response)
        data={"enable_parental_control": True,"cat_acctname":"infoblox_sdk", "cat_password":"LinWmRRDX0q","category_url":"https://dl.zvelo.com/","proxy_url":"http://10.197.38.38:8001", "proxy_username":"client", "proxy_password":"infoblox","pc_zone_name":"pc.com", "cat_update_frequency":1}
        res = ib_NIOS.wapi_request('PUT', object_type=response,fields=json.dumps(data))
        print(res)
        logging.info(res)
        if type(res)==tuple:
            if res[0]==400 or res[0]==401:
                logging.info("Test case 11 execution failed")
                assert False
            else:
                logging.info("Test Case 11 execution passed")
        else:
            logging.info("Test Case 11 execution passed")
            assert True

    @pytest.mark.run(order=8)
    def test_008_validate_parental_control_enabled(self):
        logging.info("validating parental control is enabled")
        response = ib_NIOS.wapi_request('GET', object_type="parentalcontrol:subscriber?_return_fields=enable_parental_control")
        print response
        response = json.loads(response)
        response=response[0]["enable_parental_control"]
        if response==True:
            logging.info("Test Case 12 execution passed")
            assert True
        else:
            logging.info("Test Case 12 execution failed")
            assert False

    @pytest.mark.run(order=9)
    def  test_009_add_subscriber_site(self):
        logging.info("Adding subscriber site site2")
        data={"name":"site2","maximum_subscribers":100000,"members":[{"name":config.grid_fqdn}],"nas_gateways":[{"ip_address":"2.2.2.2","name":"nas1","shared_secret":"test123"}]}
        get_ref=ib_NIOS.wapi_request('POST', object_type="parentalcontrol:subscribersite",fields=json.dumps(data))
        logging.info(get_ref)
        print(get_ref)
        if type(get_ref)!=tuple:
            reference=ib_NIOS.wapi_request('GET', object_type="parentalcontrol:subscribersite")
            reference=json.loads(reference)
            if reference[0]["name"]==data["name"]:
                logging.info("Test case 10 execution passed")
                assert True
            else:
                logging.info("Test case 13 execution Failed")
                assert False
        else:
            logging.info(get_ref)
            logging.info("Test case 13 execution failed")
            assert False

    @pytest.mark.run(order=10)
    def test_010_Enable_DCA_subscriber_Allowed_and_Blocked_list_support(self):
        logging.info("Enable DCA subscriber Allowed and Blocked list support")
        get_ref=ib_NIOS.wapi_request('GET', object_type="parentalcontrol:subscribersite")
        get_ref=json.loads(get_ref)[0]["_ref"]
        data={"dca_sub_bw_list":True}
        res = ib_NIOS.wapi_request('PUT', object_type=get_ref,fields=json.dumps(data))
        print res
        if type(res)!=tuple:
            logging.info("Test case execution passed")
            time.sleep(30)
            assert True
        else:
            logging.info("Test case execution Failed")
            assert False

    @pytest.mark.run(order=11)
    def test_011_Enable_DCA_subscriber_Allowed_and_Blocked_list_support(self):
        logging.info("Enable DCA subscriber Allowed and Blocked list support")
        get_ref=ib_NIOS.wapi_request('GET', object_type="parentalcontrol:subscribersite")
        get_ref=json.loads(get_ref)[0]["_ref"]
        data={"dca_sub_query_count":True}
        res = ib_NIOS.wapi_request('PUT', object_type=get_ref,fields=json.dumps(data))
        print res
        if type(res)!=tuple:
            logging.info("Test case execution passed")
            time.sleep(30)
            assert True
        else:
            logging.info("Test case execution Failed")


    @pytest.mark.run(order=12)
    def  test_012_validate_for_subscriber_site(self):
        logging.info("validating subscriber site site2 added")
        reference=ib_NIOS.wapi_request('GET', object_type="parentalcontrol:subscribersite")
        reference=json.loads(reference)
        if reference[0]["name"]=="site2":
            logging.info("Test case 14 execution passed")
            assert True
        else:
            logging.info("Test case 14 execution failed")
            assert False

    @pytest.mark.run(order=13)
    def test_013_Start_the_subscriber_service_on_members(self):
        logging.info("Start the subscriber service on members")
        ref=start_subscriber_collection_services_for_added_site([config.grid_fqdn])
        if ref!=None:
            logging.info("Test case 15 executed successfully")
            assert True
        else:
            logging.info("Test case 15 execution failed")
            assert False

    @pytest.mark.run(order=14)
    def test_014_Validate_subscriber_service_is_running(self):
        logging.info("Validating subscriber collection services started")
        members=[config.grid_fqdn]
        for mem in members:
            grid_ref = mem_ref_string_pc(mem)
            print grid_ref
            get_ref=ib_NIOS.wapi_request('GET', object_type=grid_ref)
            for ref in get_ref:
                if ref!=tuple:
                    logging.info("Test Case 17 Execution Passed")
                    assert True
                else:
                    logging.info("Test Case 17 Execution Failed")
                    assert False

    @pytest.mark.run(order=15)
    def test_015_start_ufclient_Messages_logs(self):
        logging.info("Starting Syslog Messages Logs")
        log("start","/storage/zvelo/log/category_download.log",config.grid_vip)
        logging.info("Test case 8 execution failed")
        time.sleep(1100)
        # adding extra sleep for download to complete
        time.sleep(1320)

    @pytest.mark.run(order=16)
    def test_016_stop_ufclient__Messages_logs(self):
        logging.info("Starting Syslog Messages Logs")
        log("stop","/storage/zvelo/log/category_download.log",config.grid_vip)
        logging.info("Test case 9 execution failed")
        sleep(30)

    @pytest.mark.run(order=17)
    def test_017_validate_for_ufcclient_data(self):
        logging.info("Validating Sylog Messages Logs")
        LookFor="zvelodb download completed | No updates available for database"
        logs=logv(LookFor,"/storage/zvelo/log/category_download.log",config.grid_vip)
        if logs!=None:
            logging.info(logs)
            logging.info("Test Case 10 Execution Completed")
            assert True
        else:
            logging.info("Test Case 10 Execution Failed")
            assert False

    @pytest.mark.run(order=18)
    def test_018_modify_grid_settings(self):
        logging.info("Mofifying GRID properties")
        response = ib_NIOS.wapi_request('GET', object_type="grid")
        response = json.loads(response)
        response=response[0]["_ref"]
        data={"dns_resolver_setting": {"resolvers": ["127.0.0.1"]}}
        res = ib_NIOS.wapi_request('PUT', object_type=response,fields=json.dumps(data))
        logging.info(res)
        if type(res)!=tuple:
            logging.info("Test Case 9 Execution Passed")
            assert True
        else:
            logging.info("Test Case 9 Execution Failed")
            assert False

    @pytest.mark.run(order=19)
    def test_019_validate_grid_settings(self):
        logging.info("Validating GRID properties")
        response = ib_NIOS.wapi_request('GET', object_type="grid?_return_fields=dns_resolver_setting")
        response = json.loads(response)
        response=response[0]["dns_resolver_setting"]["resolvers"]
        if response==["127.0.0.1"]:
            logging.info("Test Case 10 Execution Passed")
            assert True
        else:
            logging.info("Test Case 10 Execution Failed")
            assert False

    @pytest.mark.run(order=20)
    def  test_020_modify_subscriber_site(self):
        logging.info("Modifying subscriber site site2")
        response = ib_NIOS.wapi_request('GET', object_type="parentalcontrol:subscribersite")
        response = json.loads(response)
        response=response[0]["_ref"]
        data={"blocking_ipv4_vip1": "1.1.1.1","blocking_ipv4_vip2": "2.2.2.2","msps":[{"ip_address": "10.196.128.13"}],"spms": [{"ip_address": "10.12.11.11"}],"maximum_subscribers":100000,"members":[{"name":config.grid_fqdn}],"nas_gateways":[{"ip_address":"2.2.2.2","name":"nas1","shared_secret":"test123"}]}
        get_ref=ib_NIOS.wapi_request('PUT', object_type=response,fields=json.dumps(data))
        logging.info(get_ref)
        print(get_ref)
        if type(get_ref)!=tuple:
            reference=ib_NIOS.wapi_request('GET', object_type="parentalcontrol:subscribersite?_return_fields=blocking_ipv4_vip1,blocking_ipv4_vip2")
            reference=json.loads(reference)
            if reference[0]["blocking_ipv4_vip1"]==data["blocking_ipv4_vip1"] and reference[0]["blocking_ipv4_vip2"]==data["blocking_ipv4_vip2"]:
                logging.info("Test case 10 execution passed")
                assert True
            else:
                logging.info("Test case 13 execution Failed")
                assert False
        else:
            logging.info(get_ref)
            logging.info("Test case 13 execution failed")
            assert False

    @pytest.mark.run(order=21)
    def test_021_Add_Subscriber_Record_without_Proxy_all_set_and_Different_PCP_Policy_bit_than_above(self):
        try:
            logging.info("Add Subscriber Record without Proxy-All set and different PCP Policy bit than the above")
            child = pexpect.spawn('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no admin@'+config.grid_vip)
            child.logfile=sys.stdout
            child.expect('password:',timeout=None)
            child.sendline('infoblox')
            child.expect('Infoblox >')
            
            child.sendline('set subscriber_secure_data add '+config.client_ip+' 32 N/A N/A ACS:Acct-Session-Id=9999732d-34590e17;NAS:NAS-PORT=1813;AN2:NAS-PORT=1813;AN1:NAS-IP-Address=10.36.1.255;AN0:Calling-Station-Id=1366247804;PXY:Proxy-All=1;PCP:Parental-Control-Policy=00000000001000040000000000020040;SSP:Subscriber-Secure-Policy=1f;PXP:PXY_PRI=2620010a6000781400000000000006fb;PXS:PXY_SEC=0a23d2ca;SUB:User-Name=acm;')
            
            #child.sendline('set subscriber_secure_data add '+config.client_ip+' 32 N/A N/A "ACS:Acct-Session-Id=9999735888;NAS:NAS-PORT=1813;PCP:Parental-Control-Policy=00000000000000000000000000020040;SUB:Calling-Station-Id=110361288;"')
            
            child.expect('Record successfully added')
            logging.info("Test Case 27 Execution Passed")
            assert True
        except:
            logging.info("Test Case 27 Execution Failed")
            assert False

    @pytest.mark.run(order=22)
    def test_022_Validate_Subscriber_Record_without_Proxy_all_set_and_Different_PCP_Policy_bit_than_above(self):
        logging.info("Validate Subscriber Record without Proxy-All set different PCP Policy bit than the above")
        child = pexpect.spawn('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no admin@'+config.grid_vip)
        child.logfile=sys.stdout
        child.expect('password:',timeout=None)
        child.sendline('infoblox')
        child.expect('Infoblox >')
        child.sendline('show subscriber_secure_data')
        child.expect('Infoblox >')
        c=child.before
        assert re.search(r'.*'+config.client_ip+'\/32\|LID\:N\/A\|IPS\:N\/A.*PCP\:Parental-Control-Policy=00000000001000040000000000020040.*',c)
        #assert re.search(r'.*'+config.client_ip+'\/32\|LID\:N\/A\|IPS\:N\/A.*PCP\:Parental-Control-Policy=00000000000000000000000000020040.*',c)
        logging.info("Test case 28 execution completed")

    @pytest.mark.run(order=23)
    def test_023_start_Syslog_Messages_logs_on_IBFLEX_Member(self):
        logging.info("Starting Syslog Messages Logs on IB-FLEX Member")
        log("start","/var/log/syslog",config.grid_vip)
        logging.info("test case 29 passed")
        sleep(10)

        # Restart Services
        print("Restarting Services...")
        grid =  ib_NIOS.wapi_request('GET', object_type="grid")
        ref = json.loads(grid)[0]['_ref']
        request_restart = ib_NIOS.wapi_request('POST', object_type = ref + "?_function=requestrestartservicestatus")
        restart = ib_NIOS.wapi_request('POST', object_type = ref + "?_function=restartservices")
        sleep(60)


    @pytest.mark.run(order=24)
    def test_024_Send_Query_from_PCP_bit_match_Subscriber_client_for_PCP_Domain_times_Using_IB_FLEX_Member_Validate_returns_Blocked_IPs_in_response_from_Bind_As_Not_DCA_Cache(self):
        logging.info("Perform Query from PCP bit match Subscriber client for PCP Domain times.com using IB-FLEX Member and get PCP Blocked IPs response from Bind as times.com not in DCA cache")
        dig_cmd = 'sshpass -p infoblox ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o BatchMode=no  root@'+str(config.client_ip)+' "dig @'+str(config.grid_vip)+' playboy.com +noedns -b '+config.client_ip+'"'
        dig_result = subprocess.check_output(dig_cmd, shell=True)
        print dig_result
        assert re.search(r'.*QUERY, status: NOERROR.*',str(dig_result))
        assert re.search(r'.*site2-blocking.pc.com.*IN.*A.*1.1.1.1.*',str(dig_result))
        assert re.search(r'.*site2-blocking.pc.com.*IN.*A.*2.2.2.2.*',str(dig_result))
        logging.info("Test Case 30 Execution Completed")

    @pytest.mark.run(order=25)
    def test_025_stop_Syslog_Messages_Logs_on_IB_FLEX_Member(self):
        logging.info("Stopping Syslog Logs on master")
        log("stop","/var/log/syslog",config.grid_vip)
        logging.info("Test Case 31 Execution Completed")

    @pytest.mark.run(order=26)
    def test_026_Validate_Named_CEF_Log_Logs_when_get_response_from_Bind_for_PCP_domain_times_com(self):
        logging.info("Validate Named CEF Log for times.com  when get response from Bind")
        LookFor="named.*info CEF.*playboy.com.*CAT=0x00000000000000000000000000020000"
        logs=logv(LookFor,"/var/log/syslog",config.grid_vip)
        logging.info(logs)
        print logs
        if logs!=None:
            logging.info(logs)
            logging.info("Test Case 32 Execution Passed")
            assert True
        else:
            logging.info("Test Case 32 Execution Failed")
            assert False


    # Deleting subscriber secure data

    @pytest.mark.run(order=27)
    def test_027_Deleting_subscriber_secure_data(self):
    
        print ("Deleting subscriber secure data...")

      # logging.info("Not performing reset_storage in Emergency mode")
        child = pexpect.spawn("ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no admin@"+config.grid_vip, maxread=4000)
        try:

            child.expect("password:")
            child.sendline("infoblox")
            child.expect("Infoblox >")

            child.sendline('set subscriber_secure_data delete '+config.client_ip+' 32 N/A N/A')
            child.expect("Record successfully deleted")
            
            child.expect("Infoblox >",timeout=100)
            child.sendline("exit")
            
            sleep(300)


        except Exception as e:
            print(e)
            child.close()
            assert False


        finally:
            child.close()

