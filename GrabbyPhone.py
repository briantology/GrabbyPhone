'''
GrabbyPhone Edited by Brian Wcisel
ucmapi library created by Kris Serphine
Scripting assistance by Chris D.
Sponsored by The Weyland Yutani Corporation
'''

import requests
import xmltodict
import logging
from timeit import default_timer as timer
from threading import Thread
from ucmapi import Axl, Ris
import os
import urllib3
import csv
import sys
import re
import time

# Logging disabled by default
# logging.basicConfig(filename=time.strftime("%B_%d_%Y_%I.%M.%S_%p_Grabby_Log.txt"), level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

print("")
print("####################_Starting GrabbyPhone_####################")
print("###################_A Tool by Brian Wcisel_####################")
print("")

def phone_discovery():
    # Regular Expressions for validations
    fqdnRE = re.compile(r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.){2,}([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9]){2,}$')
    ipAddRE = re.compile(r'\d+\.\d+\.\d+\.\d+')

    # Disable those pesky cert warnings.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # The following line defines the directory where the AXL files are located, it assumes the directory is in the same
    # folder as the program
    schema_dir = os.path.dirname(os.path.abspath(__file__))

    # Building the AXL schema path
    axl_schema = f"{schema_dir}\\11.0\\AXLAPI.wsdl"
    ris_schema_path = f"{schema_dir}\\RISService70.xml"

    # Ask the user a buncha questions about cluster access.
    host_choice = input("Please enter the FQDN of a CUCM Publisher or Subscriber: ")
    user_choice = input("Please enter the user name(with axl permissions): ")
    password_choice = input("Please enter the password: ")

    # Input Validations, why? because it makes no sense to send empty or incorrect values to the SOAP API if we can help it.
    # Checking FQDN or IP to make sure they fit the expected format
    if re.match(fqdnRE, host_choice):
        pass
    elif re.match(ipAddRE, host_choice):
        pass
    else:
        print("A valid IP address or Hostname was not entered, please try again.")
        time.sleep(10)
        sys.exit()
    # Username check
    if user_choice:
        pass
    else:
        print("No credentials were entered, please try again")
        time.sleep(10)
        sys.exit()
    # Password Check
    if password_choice:
        pass
    else:
        print("No user credentials were entered, please try again")
        time.sleep(10)
        sys.exit()

    # Define the search Scope
    search_scope_choice = input("To limit your search to a specific device pool, input '1', otherwise press 'enter' to discover all phones: ")

    # Device Pool selection logic
    if search_scope_choice == "1":
        device_pool_choice = input("Enter the name of the device pool: ")
        # Validating selection
        if device_pool_choice:
            pass
        else:
            print("Invalid entry, please try again and use a valid device pool name")
            time.sleep(10)
            sys.exit()

    # Create AXL Connection
    try:
        axl = Axl(host=host_choice, user=user_choice, password=password_choice, wsdl=axl_schema, verify=False)
    except:
        print("AXL PROBLEM! A connection error has occurred, please check network connectivity and/or credentials")
        time.sleep(10)
        sys.exit()

    # AXL search criteria - What do we want to find.  Here it is all phones that start with SEP

    if search_scope_choice == "1":
        search_criteria = {'devicePoolName': device_pool_choice}
    else:
        search_criteria = {'name': 'SEP%'}

    print("Attempting to discover phone details, thank you for standing by.")

    # Define which details to return
    return_tags = {'name': ''}
    try:
        phones1 = axl.list(obj='Phone', request=search_criteria, rt=return_tags)
    except:
        print("RIS PROBLEM! A connection error has occurred, please check network connectivity and credentials!")
        time.sleep(10)
        sys.exit()
    # Define a simple dict that will have keys as device names and values as IP addresses
    phone_dict = {}

    for phone1 in phones1:
        # print(phone1.name)
        #     print('Name: %s, Model: %s' % (phone.name, phone.model))

        # Fill in the device names
        phone_dict[phone1.name] = ""

    # Define RIS connection
    ris = Ris(host=host_choice, user=user_choice, password=password_choice, wsdl=ris_schema_path, verify=False)

    # Define RIS 'connection'
    phones = ris.select_phones_by_name(list(phone_dict), status='Any')

    # Loop through RIS Object and try to match Device Name to key, if key is there, make value the IP address.  Basic search.
    for phone in phones:
        try:
            # print(phone.ip_address)
            phone_dict[phone.Name] = phone.ip_address
        except:
            # For debugging purposes
            print(f"{phone} failed")

    output_list = []
    # This should print out a list of Device Names and IP addresses
    for k, v in phone_dict.items():
        if v != "":
            output_list.append(v)

    # Open File
    with open('ip_input.csv', 'w', newline='') as outputfile:
        # Create Writer Object
        wr = csv.writer(outputfile)

        # Write Data to File
        for item in output_list:
            wr.writerow([item])

    print(f"Successfully discovered {len(output_list)} phones!")



#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! PROGRAM START !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
mode_selection = input("Input '1' to connect to your cluster and automatically discover phones, otherwise press 'Enter' to discover phones listed in 'ip_input.csv' file: ")

# Checking to see if we are connecting to the cluster for automatic discovery
if mode_selection == '1':
    phone_discovery()

# Start Phone Discovery
# Define which XML tags to display in output csv file, add any correct tags to this list in order you want it to appear in the CSV file
# field names are a optional keyword argument for writing CSV files.
fieldnames = [
'MACAddress',
'phoneDN',
'modelNumber',
'versionID',
'hardwareRevision',
'serialNumber',
'DHCPEnabled',
'DHCPServer',
'IPAddress',
'SubNetMask',
'DefaultRouter',
'DNSServer1',
'DNSServer2',
'DNSServer3',
'DomainName',
'AltTFTP',
'TFTPServer1',
'TFTPServer2',
'CallManager1',
'CallManager2',
'CallManager3',
'CallManager4',
'CallManager5'
'VLANId',
'AdminVLANId',
'CDPNeighborDeviceId',
'CDPNeighborIP',
'CDPNeighborPort',
'LLDPNeighborDeviceId',
'LLDPNeighborIP',
'LLDPNeighborPort',
'PortSpeed',
]



csvfile = open('Results.csv', 'w')
# Define CSV Output object which will be used to write the results of the program
writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n', fieldnames=fieldnames)
# Write the headers to the output CSV Object
writer.writeheader()

# Define set for Ip addresses of phones that do not have webpage enabled
no_web_access_set = set()

def parse_xml(net_port_keys, device_keys, net):
    # Define network dictionary which will be used to store each device's return XML.
    device_network_dict = {}
    #Unpack dictionary, loop through items
    for k, v in net.items():
        # exception to handle DefaultRouter on 79XX devices
        if k == 'DefaultRouter1':
            device_network_dict['DefaultRouter'] = v
        # If key matches fieldname in list then add a new entry to the output dict with key and value
        if k in fieldnames:
            device_network_dict[k] = v

    if net_port_keys['PortInformation']:
        port = net_port_keys['PortInformation']
        for k, v in port.items():
            if k in fieldnames:
                device_network_dict[k] = v
    else:
        raise SystemExit("No port configuration returned")

    if device_keys['DeviceInformation']:
        device_info = device_keys['DeviceInformation']
        for k, v in device_info.items():
            if k in fieldnames:
                device_network_dict[k] = v
    else:
        raise SystemExit("No device configuration returned")

    # Write results of dictionary to CSV
    writer.writerow(device_network_dict)

def do_phone(ip):
    try:
        # This gets the Request and parses the result to a dictionary object.
        net_config_data = xmltodict.parse(requests.get('http://' + ip + '/NetworkConfigurationX', timeout=2).text)

        try:
            # This gets Request and parses the result to a dictionary object.
            net_port_keys = xmltodict.parse(requests.get('http://' + ip + '/PortInformationX?1', timeout=2).text)
        except:
            print("Couldn't get port configuration.")
        try:
            # This gets Request and parses the result to a dictionary object.
            device_keys = xmltodict.parse(requests.get('http://' + ip + '/DeviceInformationX', timeout=2).text)
        except:
            print("Couldn't get device info configuration.")

        # Check for existence
        if net_config_data['NetworkConfiguration']:
            # Define a new xmltodict object named net and containing the ordered dict of networkconfiguration 'node'
            net = net_config_data['NetworkConfiguration']

            # If Alternate FTP selected by user then print this.
            if input_option == "1":
                if net.get('AltTFTP') == 'Yes':
                    # print("Working on phone ", str(ip))
                    parse_xml(net_port_keys, device_keys, net)
            # return all devices
            else:
                # Call the parse xml function
                parse_xml(net_port_keys, device_keys, net)
                # print("Working on phone ", str(ip))
        else:
            raise SystemExit("No network configuration returned")


    except:
            no_web_access_set.add(ip)
            print("Couldn't get network configuration for device {}.".format(ip))

# Create Logging file


# Create list of Phone  IP addresses that we are going to loop through
ip_list = []

# Shameless Self Promotion :)


# Request mode of operation from user
input_option = input("Input '1' to find only ALT TFTP phones, otherwise press 'Enter' to scan all devices: ")

# Open the input file!  Or try to at least...
try:
    with open('ip_input.csv', newline='') as csvfile:
        # Create the csv object
        spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
        # Take IP addresses from the csv and add them to the loop
        for row in spamreader:
            ip_list.append(', '.join(row))

# File exception handling
except FileNotFoundError as not_found:
    print("")
    print("ERROR! 'ip_input.csv' is not detected, make sure the input file is in the same directory as the program and run it again.")

# Start the Timer
startdevicediscovery = timer()
# Lets get started checking Ip Phones for ALT TFTP set to Yes

# Multi-threading element
list_threads = []

# Multi-threading loop
for ip in ip_list:
    t = Thread(target=do_phone, args=(ip,))
    list_threads.append(t)
    try:
        t.start()
    except:
        # print("error4")
        pass
    # End timer!

# Multi-threading element
for t in list_threads:
    t.join()

# Open output file for phones with no web access or are simply unreachable.
no_web_access = open('no_web_access_or_unreachable.txt', 'w')

# Write the results
for i in no_web_access_set:
    no_web_access.write(i + '\n')

# Close the output files
csvfile.close()
no_web_access.close()

# End the Timer
end_phone_discover_timer = timer()

# Report the run time
print("")
print("This operation took {} seconds.".format(round(end_phone_discover_timer - startdevicediscovery, 9)))

time.sleep(10)
sys.exit