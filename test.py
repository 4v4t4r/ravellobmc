#!/usr/bin/env python
#
# Copyright 2015 Ravello Systems Inc.
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

from ravellobmc import RavelloBmc
from ravellobmc import IPMI_PORT
from ravello_sdk import message_queue

import subprocess
import threading
import time
import unittest

my_bmc = None
my_thread = None


def start_bmc():
    global my_bmc
    my_bmc = RavelloBmc({'admin': 'password'},
                        port=IPMI_PORT,
                        address='127.0.0.1',
                        aspect="design",
                        username='ravello_user',
                        password='ravello_pass',
                        app_name='foo',
                        vm_name='bar')
    my_bmc.connect()
    my_bmc.listen()


def is_listening():
    cmd = subprocess.Popen('netstat -u -p -l',
                           shell=True,
                           stdout=subprocess.PIPE)
    output = cmd.communicate()[0]

    pattern = 'localhost:asf-rmcp'

    if pattern in output:
        return True

    return False


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("setup")
        global my_thread
        my_thread = threading.Thread(target=start_bmc)
        my_thread.start()
        # We won't modify pyghmi too much by adding a condition variable
        # linked to the bmc.BMC listen method so we just use a bounded sleep
        while not is_listening():
            time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        global t
        # Again we do not want to modify pyghmi too much so use this internal
        # threading call to stop the BMC thread
        my_thread._Thread__stop()
        my_thread.join()

    def ipmi(self, cmd):
        return subprocess.call(['ipmitool',
                                '-I',
                                'lanplus',
                                '-U',
                                'admin',
                                '-P',
                                'password',
                                '-H',
                                '127.0.0.1',
                                'power',
                                cmd])

    def test_01_init(self):
        assert(message_queue.pop(0) == 'login: ravello_user, ravello_pass')
        assert(message_queue.pop(0) == 'get_application: foo design')

    def test_02_poweroff(self):
        result = self.ipmi('off')
        assert(result == 0)
        assert(message_queue.pop(0) == 'poweroff_vm')

    def test_03_poweron(self):
        result = self.ipmi('on')
        assert(result == 0)
        assert(message_queue.pop(0) == 'start_vm')

    def test_04_shutdown(self):
        result = self.ipmi('soft')
        assert(result == 0)
        assert(message_queue.pop(0) == 'stop_vm')

    def test_05_powerstate(self):
        result = self.ipmi('status')
        assert(result == 0)
        assert(message_queue.pop(0) == 'get_application: foo design')

if __name__ == '__main__':
    unittest.main()
