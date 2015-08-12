Ravello IPMI BMC
================

This module implement an IPMI BMC virtual module able to control the
ravello API.

Installation
============

Use python 2.x

    git clone https://github.com/benoit-canet/pyghmi.git
    cd pyghmi
    python2.x setup.py install

Do the same for the Ravello python SDK

copy the ravellobmc.py script where you want it to be.
(leaving it in the git repository will bind it to the ravello_sdk.py test stub)

Usage
=====

Launch it with --help then launch it for real with python2.x

Use ipmitool to control the proxy.

    ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power status
    ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power on
    ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power off
    ipmitool -I lanplus -U admin -P password -H 127.0.0.1 power soft
