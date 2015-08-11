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

VM_ID = {'name': 'bar', 'state': "STARTED"}
APP_ID = {'id': 'foo',
          'design': {'vms': [VM_ID]}}

message_queue = []


class RavelloClient(object):

    def __init__(self):
        self._message_queue = []

    def log_msg(self, msg):
        global message_queue
        message_queue.append(msg)
        print(msg)

    def login(self, username, password):
        """ Stub of the login method """
        msg = "login: %s, %s" % (username, password)
        self.log_msg(msg)

    def logout(self):
        """ Stub of the logout method """
        msg = "logout"
        self.log_msg(msg)

    def close(self):
        """ Stub of the close method """
        msg = "close"
        self.log_msg(msg)

    def get_application_by_name(self, name, aspect):
        """ Stub of the get_application method """
        msg = "get_application: %s %s" % (name, aspect)
        self.log_msg(msg)
        return APP_ID

    def poweroff_vm(self, app, vm):
        """ Stub of the get_vm method """
        msg = "poweroff_vm"
        self.log_msg(msg)
        assert(app == APP_ID)
        assert(vm == VM_ID)

    def start_vm(self, app, vm):
        msg = "start_vm"
        self.log_msg(msg)
        assert(app == APP_ID)
        assert(vm == VM_ID)

    def stop_vm(self, app, vm):
        msg = "stop_vm"
        self.log_msg(msg)
        assert(app == APP_ID)
        assert(vm == VM_ID)
