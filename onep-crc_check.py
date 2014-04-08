#! /usr/bin/env python

# *------------------------------------------------------------------
# * onep-crc_check.py
# *
# * Simple script to check CRC errors on all interfaces and shut down
# * the interfaces with errors greater than a given threshold
# *
# * Cisco ONE-P Python SDK
# *
# * Copyright (c) 2011-2014 by Cisco Systems, Inc.
# * All rights reserved.
# *------------------------------------------------------------------
# *
#
# Must have a Cisco device capable of communicating with ONE-P APIs.
# Network Element must also have onep configured with the socket
# transport and have the correct onep services activated.
# Depending on OnePK SDK release, supported tranport type could be
# TCP and TLS. Check on device using the following CLIs:
# conf t --> onep --> transport  type ?
#
# A network interface must be configured with a valid IP address and
# pingable.
#
# To use this script you should:
# 1) Copy the file to a server with OpePK SDK
# 2) setup the variables in the section below
# 3) run the script: python onep-crc_check.py
#from onep.element.NetworkElement import NetworkElement
from onep.element.SessionConfig import SessionConfig
from onep.interfaces.InterfaceStatistics import InterfaceStatistics
from onep.interfaces.InterfaceFilter import *

#####################################################################
# Variables to be changed
#
# transport- Transport type: either TIPC or TLS
#            check tranport types supported on your image by
#            conf t --> onep --> transport  type ?
# cert     - certificate to be used for authentication in cse of TLS
#            transport
# appName  - OnePK application Name
# switchIP - management Switch IP address
# user     - switch userID
# pswd     - switch password
#
# crcThreshold -  CRC errors Threshold
#
transport= 'TLS'
cert     = '<path>/cacert.pem'
appName  = "crc_check"
switchIP = "<ip>"
user     = "<user>"
pswd     = "<pswd>"

crcThreshold = "10"
#####################################################################

#
# Set up session connection configuration and connect to the switch
#
ne = NetworkElement(switchIP, appName)

if  transport == 'TLS':
    session_config = SessionConfig(SessionConfig.SessionTransportMode.TLS)
    session_config.ca_certs = cert
    ne.connect(user, pswd, session_config)
elif transport == 'TIPC':
    session_config = SessionConfig(SessionConfig.SessionTransportMode.TIPC)
    ne.connect(user, pswd, session_config)
else:
    print "Please set-up a valid transport type: TIPC or TLS"
    exit(0)
#
#
# Get Interface list
#
rx_CRC = InterfaceStatistics.InterfaceStatisticsParameter.ONEP_IF_STAT_RX_PKTS_CRC
filter =  InterfaceFilter(None, NetworkInterface.InterfaceTypes.ONEP_IF_TYPE_ETHERNET)
intf_list_ne = ne.get_interface_list(filter)

#
# For every Interface, check the CRC errors
#
for intf_ne in intf_list_ne:
    try:
        int = ne.get_interface_by_name(intf_ne.name)
        int_stats =  int.get_statistics()
        rx_CRC_pkts=int_stats.get_param(rx_CRC)
        print "CRC_pkts: ", rx_CRC_pkts,"on int", intf_ne.name
        #
        # If CRC error are greater than the threshold, generate a syslog message,
        # print the values and shut down the interface
        #
        if rx_CRC_pkts > crcThreshold:
            string_print = "CRC threshold of ",crcThreshold," exceeded. Shutting down interface ",intf_ne.name
            ne.create_syslog_message (ne.OnepSyslogSeverity.ONEP_SYSLOG_CRITICAL,
                                      str(string_print));

            #print locally
            print "Interface: ",intf_ne.name,"RX_PKTS_CRC",rx_CRC_pkts
            print "Shutting interface", intf_ne.name

            #shut interface
            int.shut_down(1)
    except:
        continue

ne.disconnect();
