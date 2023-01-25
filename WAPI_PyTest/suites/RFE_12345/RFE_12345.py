import re
import sys
import config
import pytest
import unittest
import logging
import subprocess
import os
import json
import ib_utils.ib_NIOS as ib_NIOS
from time import sleep
import commands
import json, ast
import requests
import time
import pexpect


def getting_the_ipv6_address_range_of_client():
    output = os.popen('hostname -I')
    output = output.read()
    output1 = output.split()[1]
    ipv6_range = output1.split('::')[0]
    print(ipv6_range)
    return ipv6_range

class Network(unittest.TestCase):
        @pytest.mark.run(order=1)
        def test_001_start_IPv4_service(self):
                logging.info("start the ipv4 service")
                get_ref = ib_NIOS.wapi_request('GET', object_type="member:dhcpproperties", grid_vip=config.grid1_master_vip)
                logging.info(get_ref)
                res = json.loads(get_ref)
                ref1 = json.loads(get_ref)[0]['_ref']
                print ref1

                data = {"enable_dhcp": True}
                response = ib_NIOS.wapi_request('PUT',ref=ref1,fields=json.dumps(data), grid_vip=config.grid1_master_vip)
                logging.info(response)
                logging.info("============================")
                print response

        @pytest.mark.run(order=2)
        def test_002_start_IPv6_service(self):
                logging.info("start the ipv6 service")
                get_ref = ib_NIOS.wapi_request('GET', object_type="member:dhcpproperties", grid_vip=config.grid1_master_vip)
                logging.info(get_ref)
                res = json.loads(get_ref)
                ref1 = json.loads(get_ref)[0]['_ref']
                print ref1

                data = {"enable_dhcpv6_service": True}
                response = ib_NIOS.wapi_request('PUT',ref=ref1,fields=json.dumps(data), grid_vip=config.grid1_master_vip)
                logging.info(response)
                logging.info("============================")
                print response

                
        @pytest.mark.run(order=3)
        def test_003_Make_member_as_GMC(self):
            print("\n========================================================\n")
            print("Make Member1 as Master candidate")
            print("\n========================================================\n")

            get_ref = ib_NIOS.wapi_request('GET', object_type='member', grid_vip=config.grid1_master_vip)
            get_ref = json.loads(get_ref)[1]['_ref']

            data = {"master_candidate":True}
            response = ib_NIOS.wapi_request('PUT', ref=get_ref, fields=json.dumps(data),grid_vip=config.grid1_master_vip)
            print(response)

            if type(response) == tuple:
                if response[0] == 400 or response[0] == 401:
                    print("Failure: Make the member as Master candidate")
                    assert False
                else:
                    print("Success: Make the member as Master candidate")
                    assert True

           


    # Validating if the member is GMC or not
        @pytest.mark.run(order=4)
        def test_004_validate_member_as_GMC(self):
            print("\n========================================================\n")
            print("Validating if the member is Grid Master Candidate")
            print("\n========================================================\n")

            try:
                child = pexpect.spawn('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no admin@'+config.grid1_member1_vip)
                child.logfile=sys.stdout
                child.expect("password:")
                child.sendline("infoblox")
                child.expect("Infoblox >")
                child.sendline('show status')
                child.expect("Infoblox >")
                output = child.before
                print(output)
                if "Master Candidate: true" in output:
                    assert True
                else:
                    assert False

            except Exception as e:
                print(e)
                child.close()
                assert False

            finally:
                child.close()
