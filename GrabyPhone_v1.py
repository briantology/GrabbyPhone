import requests
import xmltodict
import csv
import logging
import time
from timeit import default_timer as timer
from threading import Thread
from collections import OrderedDict

# Define which XML tags to display in output csv file, add any correct tags to this list in order you want it to appear in the CSV file
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
'TFTPServer1'
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
writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n', fieldnames=fieldnames)
writer.writeheader()

no_web_access = open('no_web_access.txt', 'w')

def parse_xml(net_port_keys, device_keys, net):
    device_network_dict = {}
    for k, v in net.items():
        # exception to handle DefaultRouter on 79XX devices
        if k == 'DefaultRouter1':
            device_network_dict['DefaultRouter'] = v
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


        if net_config_data['NetworkConfiguration']:
            net = net_config_data['NetworkConfiguration']
            # use this if need to find phones with alternate
            if input_option == "1":
                if net.get('AltTFTP') == 'Yes':
                    print("Working on phone ", str(ip))
                    parse_xml(net_port_keys, device_keys, net)
            # return all devices
            else:
                parse_xml(net_port_keys, device_keys, net)
                print("Working on phone ", str(ip))
        else:
            raise SystemExit("No network configuration returned")



    except:
        no_web_access.write(ip + '\n')
        print("Couldn't get network configuration for device {}.".format(ip))





# Create Logging file
logging.basicConfig(filename=time.strftime("%B_%d_%Y_%I.%M.%S_%p_Grabby_Log.txt"), level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')

# Create list of Phone  IP addresses that we are going to loop through
ip_list = []


input_option = input("Enter 1 to look for devices with Alternate TFTP set or hit enter to look for all phones: ")

# Open the file!
with open('ip_input.csv', newline='') as csvfile:
    # Create the csv object
    spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    # Take IP addresses from the csv and add them to the loop
    for row in spamreader:
        ip_list.append(', '.join(row))

# Start the Timer
startdevicediscovery = timer()
# Lets get started checking Ip Phones for ALT TFTP set to Yes
for ip in ip_list:
    t = Thread(target=do_phone, args=(ip,))
    try:
        t.start()
    except:
        # print("error4")
        pass
    # End timer!
time.sleep(2)
end_phone_discover_timer = timer()
csvfile.close()
no_web_access.close()
#print("This operation took {} seconds.".format(round(end_phone_discover_timer - startdevicediscovery, 9)))