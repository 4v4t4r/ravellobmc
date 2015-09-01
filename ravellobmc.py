#!/usr/bin/env python
#
# Copyright 2015 Ravello Systems Inc.
#
# Based on fakebmc Copyright 2015 Lenovo
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
__author__ = 'benoit.canet@nodalink.com'

# This is a virtual IPMI BMC doing power query against the Ravello API server
# to play:
# python2.x ravellobmc.py --help
# python2.x ravellobmc.py arguments
#
# ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power status
# Chassis Power is off
# # ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power on
# Chassis Power Control: Up/On
# # ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power status
# Chassis Power is on

import argparse
import logging
import pyghmi.ipmi.bmc as bmc
import signal
import sys
import threading
import time

from ravello_sdk import RavelloClient

IPMI_PORT = 623

global my_bmc
global my_thread
global my_lock


def start_bmc(args, ipmi_password, api_password):
    global my_bmc
    global my_lock

    my_lock = threading.Lock()
    my_lock.acquire()

    my_bmc = RavelloBmc({'admin': ipmi_password},
                        port=IPMI_PORT,
                        address=args.address,
                        aspect=args.aspect,
                        username=args.api_username,
                        password=api_password,
                        app_name=args.app_name,
                        vm_name=args.vm_name)

    if not my_bmc.connect():
        my_lock.release()
        msg = "Failed to connect to API server. Exiting"
        logging.error(msg)
        print(msg)
        sys.exit(1)

    # We must release the lock here to avoid a dead lock since
    # bmc.listen() is a busy loop
    my_lock.release()

    my_bmc.listen()


class RavelloBmc(bmc.Bmc):
    """Ravello IPMI virtual BMC."""

    def get_vm(self, application, name):
        """Get a VM by name."""
        vms = application.get(self._aspect, {}).get('vms', [])
        for vm in vms:
            if vm['name'] == name:
                return vm

        msg = 'vm not found: {0}'.format(name)
        logging.error(msg)
        raise ValueError(msg)

    def connect(self):
        """Connect to the Ravello API server with the given credentials."""
        try:
            self._client = RavelloClient()
            self._client.login(self._username, self._password)
            c = self._client
            self._app = c.get_application_by_name(self._app_name,
                                                  aspect=self._aspect)
            self._vm = self.get_vm(self._app, self._vm_name)
            return True
        except Exception as e:
            msg = "Exception while connecting to API server:" + str(e)
            logging.error(msg)
            print(msg)
            return False

    def __init__(self, authdata, port, address, aspect, username, password,
                 app_name, vm_name):
        """Ravello virtual BMC constructor."""
        self._client = None
        super(RavelloBmc, self).__init__(authdata,
                                         address=address,
                                         port=port)
        self._aspect = aspect
        self._username = username
        self._password = password
        self._app_name = app_name
        self._vm_name = vm_name

    def disconnect(self):
        """Disconnect from the Ravello API server."""
        if not self._client:
            return

        self._client.logout()
        self._client.close()

    def __del__(self):
        """Ravello virtual BMC destructor."""
        self.disconnect()

    # Disable default BMC server implementations

    def cold_reset(self):
        """Cold reset reset the BMC so it's not implemented."""
        raise NotImplementedError

    def get_boot_device(self):
        """Desactivated IPMI call."""
        raise NotImplementedError

    def get_system_boot_options(self, request, session):
        """Desactivated IPMI call."""
        raise NotImplementedError

    def set_boot_device(self, bootdevice):
        """Desactivated IPMI call."""
        raise NotImplementedError

    def set_kg(self, kg):
        """Desactivated IPMI call."""
        raise NotImplementedError

    def set_system_boot_options(self, request, session):
        """Desactivated IPMI call."""
        raise NotImplementedError

    def power_reset(self):
        """Reset a VM."""
        # Shmulik wrote "Currently, limited to: "chassis power on/off/status"
        raise NotImplementedError

    # Implement power state BMC features
    def get_power_state(self):
        """Get the power state of a Ravello VM."""

        try:
            # query the vm again to have an updated status
            c = self._client
            self._app = c.get_application_by_name(self._app_name,
                                                  aspect=self._aspect)
            self._vm = self.get_vm(self._app, self._vm_name)

            if self._vm['state'] == 'STARTED':
                return "on"
        except Exception as e:
            logging.error('get_power_state:' + str(e))
            return 0xce

        return "off"

    def power_off(self):
        """Cut the power without waiting for clean shutdown."""
        try:
            self._client.poweroff_vm(self._app, self._vm)
        except Exception as e:
            logging.error('power_off:' + str(e))
            return 0xce

    def power_on(self):
        """Start a vm."""
        try:
            self._client.start_vm(self._app, self._vm)
        except Exception as e:
            logging.error('power_on:' + str(e))
            return 0xce

    def power_shutdown(self):
        """Gently power off while waiting for clean shutdown."""
        try:
            self._client.stop_vm(self._app, self._vm)
        except Exception as e:
            logging.error('power_shutdown:' + str(e))
            return 0xce


def parse_args():
    parser = argparse.ArgumentParser(
        prog='ravellobmc',
        description='The Ravello virtual BMC',
    )

    # Use a compact format for declaring command line options
    arg_list = []
    arg_list.append(['address', 'Address to listen on; defaults to localhost'])
    arg_list.append(['aspect', 'Aspect'])
    arg_list.append(['api-username', 'User name'])
    arg_list.append(['app-name', 'Name of the Ravello application'])
    arg_list.append(['vm-name', 'Name of the VMX virtual machine'])

    # expand the list of command line options
    for arg in arg_list:
        parser.add_argument('--%s' % arg[0],
                            dest=arg[0].replace('-', '_'),
                            type=str,
                            help=arg[1],
                            required=True)

    parser.add_argument('--debug',
                        dest='debug',
                        action='store_true',
                        help='Enable Ravello SDK debugging')

    return parser.parse_args()


def exit_signal(signal, frame):
    global my_bmc
    global my_thread
    global my_lock
    my_thread._Thread__stop()
    my_thread.join()

    my_lock.acquire()
    my_bmc.disconnect()
    my_lock.release()

    sys.exit(0)

if __name__ == '__main__':
    args = parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    # Ask for password on stdin so they do not appears in process list
    print("Please enter IPMI proxy password")
    ipmi_password = sys.stdin.readline().strip()

    print("Please enter Ravello API server password")
    api_password = sys.stdin.readline().strip()

    global my_thread
    my_thread = threading.Thread(target=start_bmc,
                                 args=(args, ipmi_password, api_password))
    my_thread.start()

    signal.signal(signal.SIGINT,  exit_signal)

    while True:
        time.sleep(1)
