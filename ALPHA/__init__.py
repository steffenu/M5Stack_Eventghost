import traceback

import eg
import socket
import wx
import threading
import json

import os
import glob
from uuid import getnode as get_mac

from scapy.config import conf
from scapy.layers.l2 import Ether, ARP, getmacbyip # for some reason not picked up by function below
from scapy.sendrecv import srp

import logging


# Create a custom logger
logger = logging.getLogger(__name__)
# Create handlers
#c_handler = logging.StreamHandler()
#c_handler.setLevel(logging.DEBUG) #  DEBUG 10 INFO 20  WARNING 30
# Create formatters and add it to handlers
#c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
#f_format = logging.Formatter('%(levelname)s - %(message)s')
#c_handler.setFormatter(f_format)
# Add handlers to the logger
#logger.addHandler(c_handler)

logging.getLogger().setLevel(logging.INFO) # set to info or warning to disable
logging.basicConfig(format='%(levelname)s -  %(funcName)s() - %(message)s') # default == WARNING



#import logging
#logging.basicConfig(level=logging.DEBUG , format='%(levelname)s -  %(funcName)s() - %(message)s') # default == WARNING




eg.RegisterPlugin(
    name = "M5Stack",
    guid = "{98FCA09F-9ED0-4F49-BE88-75AC96FA81D8}",
    author = "Medy",
    version = "0.0.1",
    kind = "other",
    description = "Notifications for M5Stack"
)

class DefaultValues:
    default_TCP_PORT = "7300"



#1. Send UDP Discovery Messages with EG info (hostname - port for tcp communication
#2. Recieve TCP Response (SERVER)
#3  Add new Devices To list



class M5Stack(eg.PluginBase):
    class Text:
        eventPrefix = "Event prefix:"
        zone = "Broadcast zone:"
        port = "UDP port:"
        listenAddr = "Listening address:"
        selfBroadcast = "Respond to self broadcast"
        delim = "Payload delimiter"
        message_1 = "Broadcast listener on"
        message_2 = "Self broadcast is"

    text = Text

    def __init__(self):
        group1 = self.AddGroup(
            "Notfications",
            """
            Select from a range of templates to display Notifcations on your M5Stack Device 
            """

        )

        group1.AddAction(EventCard)
        group1.AddAction(List)
        group1.AddAction(KeyValue)
        group1.AddAction(Single)



        group2 = self.AddGroup(
            "Settings",
            """
            Advanced settings to customize / update your device 
            """

        )

        group2.AddAction(Setup)
        group2.AddAction(ARP)
        # Brightness
        # Buttons
        # Background Color

        group3 = self.AddGroup(
            "Other",
            """
            Additional Screens
            """

        )


        THREAD= threading.Thread(target=self.theaded_TCP_SERVER, args=())
        THREAD.start()

        THREAD2= threading.Thread(target=self.UDP_CONFIG_RECIEVER, args=())
        THREAD2.start()



    def Configure(self, prefix="Broadcast", zone="255.255.255.255", port=7200,
                  listenAddr=""):


        addrs = socket.gethostbyname_ex(socket.gethostname())[2]
        listenAddr = addrs[0]

        text = self.text
        panel = eg.ConfigPanel(self)

        addrs = socket.gethostbyname_ex(socket.gethostname())[2]
        addrs.sort(key=lambda a: [int(b) for b in a.split('.', 4)])

        try:
            addr = addrs.index(listenAddr)
        except ValueError:
            addr = 0

        editCtrl = panel.TextCtrl(prefix)
        zoneCtrl = panel.TextCtrl(zone)
        portCtrl = panel.SpinIntCtrl(port, min=1, max=65535)
        listenAddrCtrl = panel.Choice(addr, addrs)


        panel.AddLine(text.eventPrefix, editCtrl)
        panel.AddLine(text.zone, zoneCtrl)
        panel.AddLine(text.port, portCtrl)

        panel.AddLine(text.listenAddr, listenAddrCtrl)

        while panel.Affirmed():
            panel.SetResult(
                editCtrl.GetValue(),
                zoneCtrl.GetValue(),
                int(portCtrl.GetValue()),
                addrs[listenAddrCtrl.GetValue()]
            )
    # !!! ITS IMPORTANT TO OPEN THE PORT IN WINDOWS FIREWALL !!!
    def UDP_CONFIG_RECIEVER(self):


        server_address = ('0.0.0.0', 7200)

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(server_address)

        logger.info('starting UDP SERVER on %s port %s' % (server_address[0],server_address[1]))

        #logging.info('starting UDP SERVER on %s port %s' % (server_address[0],server_address[1]))

        #print('starting  UDP SERVER on %s port %s' % (server_address))

        while True:
            data, addr = s.recvfrom(1024)
            decoded_data = data.decode()
            logger.info('decoded_data %s' % decoded_data)
            print("decoded_data", decoded_data)

            if decoded_data:
                if "file_request" in decoded_data:
                    print("DEVICE IS REQUESTING FILE UPDATE")
                    device_json = self.JSONFormatter(decoded_data)
                    self.FILE_SENDING(device_json['host_ip'][0])
                    continue
                self.broadcast() # send config to whole network , Altenative would be using tcp , or single udp send
                #sent = s.sendto(data, addr)

                json_loader = self.JSONFormatter(decoded_data) #new device formatted

                device_list = self.LoadJsonFromFile() # returns Object from LoadJsonfromFile()
                new_device = self.check_if_new_device(json_loader,device_list) # returns json device


                self.WriteJsonToFile(new_device)

                print(' ## PARING NEW Device ## ')

    def FILE_SENDING(self, device_ip):

        try:

            plugin_dir = eg.localPluginDir #    C:\ProgramData\EventGhost\plugins
            plugin = '\\M5Stack\\'
            folder = 'MAIN'


            files_to_send = []

            for (root,dirs,files) in os.walk( plugin_dir + plugin + folder, topdown=True):
                if files:
                    for x in files:
                        if not ".txt" in x:
                            files_to_send.append(root + '\\' + x)

            #print ("files_to_send" , files_to_send)

            #images_png = glob.glob(path + "SETUP\*.png")
            #images_png = glob.glob("\SETUP\*.png")
            #images_png = glob.glob(path + "MAIN\PAIRING\*.png")
            # try using plugin directory

            logger.info('FILES TO SEND: %s' % files_to_send)
            #print("FILES TO SEND:", images_png)

            #print("ITERATION")
            # SEND EVERY IMAGE  IN THE IMAGE / SETUP DIRECTORY via TCP
            # https://www.thepythoncode.com/article/send-receive-files-using-sockets-python

            # !!!! OPEN CLOSE ACCEPT VS only 1 connection
            # https://stackoverflow.com/a/35246192/11678858

            SEPARATOR = "<SEPARATOR>"
            BUFFER_SIZE = 4096  # send 4096 bytes each time step

            # s.connect((host, port))

            # the ip address or hostname of the server, the receiver
            # host = "192.168.1.101"
            # the port, let's use 5001
            # port = 5001

            host = device_ip
            # the port, let's use 5001
            port = 7300

            for x in files_to_send:

                # the name of file we want to send, make sure it exists

                # create the client socket
                s = socket.socket()

                logger.info('Connecting to %s on port %s' % (host, port))
                #print("Connecting to", host, port)
                s.connect((host, port))

                logger.info('[+] Connected')
                #print("[+] Connected.")

                filename = x
                logger.info('filename %s' % filename)
                #print("filename", filename)
                # get the file size
                filesize = os.path.getsize(filename)
                # send the filename and filesize
                filename_for_reciever = os.path.basename(filename)

                s.sendall(str(filename_for_reciever) + str(SEPARATOR) + str(filesize).encode())

                # Brings the socket into recv mode to avoid the next sendall to append to the stream
                while True:
                    confirmation = s.recv(BUFFER_SIZE)
                    if confirmation:
                        logger.info('confirmation %s' % confirmation)
                        #print(confirmation)
                        break

                # s.shutdown(1)
                # SHUT_RD or 0 Further receives are disallowed
                # SHUT_WR or 1 Further sends are disallowed
                # SHUT_RDWR or 2 Further sends and receives are disallowed

                # start sending the file
                logger.info('JUST SEND : %s %s %s' % (str(filename), str(SEPARATOR), str(filesize)))
                #print("JUST SEND :", str(filename) + str(SEPARATOR) + str(filesize))
                # progress = tqdm.tqdm(range(filesize), "Sending", unit="B", unit_scale=True, unit_divisor=1024)

                f = open(filename, "rb")
                while True:
                    # read the bytes from the file
                    bytes_read = f.read(BUFFER_SIZE)
                    if not bytes_read:
                        # file transmitting is done
                        f.close()
                        s.close()
                        break
                    # we use sendall to assure transimission in
                    # busy networks
                    s.sendall(bytes_read)
            # close the socket
            s = socket.socket()
            s.connect((host, port))
            s.send("ALL FILES SEND")

            s.close()

        except:
            print("## TRANSMISSION ERROR in FILE SENDING")

    # def FILE_SENDING(self , device_ip):
    #
    #     path = eg.configDir + '\plugins\M5Stack\\'
    #
    #     #images_png = glob.glob(path + "SETUP\*.png")
    #     images_png = glob.glob("\SETUP\*.png")
    #     # try using plugin directory
    #
    #     logger.info('FILES TO SEND: %s' % images_png)
    #     #print("FILES TO SEND:", images_png)
    #
    #     #print("ITERATION")
    #     # SEND EVERY IMAGE  IN THE IMAGE / SETUP DIRECTORY via TCP
    #     # https://www.thepythoncode.com/article/send-receive-files-using-sockets-python
    #
    #     # !!!! OPEN CLOSE ACCEPT VS only 1 connection
    #     # https://stackoverflow.com/a/35246192/11678858
    #
    #     SEPARATOR = "<SEPARATOR>"
    #     BUFFER_SIZE = 4096  # send 4096 bytes each time step
    #
    #     # s.connect((host, port))
    #
    #     # the ip address or hostname of the server, the receiver
    #     # host = "192.168.1.101"
    #     # the port, let's use 5001
    #     # port = 5001
    #
    #     host = device_ip
    #     # the port, let's use 5001
    #     port = 7300
    #
    #     for x in images_png:
    #
    #         # the name of file we want to send, make sure it exists
    #
    #         # create the client socket
    #         s = socket.socket()
    #
    #         logger.info('Connecting to %s on port %s' % (images_png, port))
    #         #print("Connecting to", host, port)
    #         s.connect((host, port))
    #
    #         logger.info('[+] Connected')
    #         #print("[+] Connected.")
    #
    #         filename = x
    #         logger.info('filename %s' % filename)
    #         #print("filename", filename)
    #         # get the file size
    #         filesize = os.path.getsize(filename)
    #         # send the filename and filesize
    #         filename_for_reciever = os.path.basename(filename)
    #
    #         s.sendall(str(filename_for_reciever) + str(SEPARATOR) + str(filesize).encode())
    #
    #         # Brings the socket into recv mode to avoid the next sendall to append to the stream
    #         while True:
    #             confirmation = s.recv(BUFFER_SIZE)
    #             if confirmation:
    #                 logger.info('confirmation %s' % confirmation)
    #                 #print(confirmation)
    #                 break
    #
    #         # s.shutdown(1)
    #         # SHUT_RD or 0 Further receives are disallowed
    #         # SHUT_WR or 1 Further sends are disallowed
    #         # SHUT_RDWR or 2 Further sends and receives are disallowed
    #
    #         # start sending the file
    #         logger.info('JUST SEND : %s %s %s' % (str(filename), str(SEPARATOR), str(filesize)))
    #         #print("JUST SEND :", str(filename) + str(SEPARATOR) + str(filesize))
    #         # progress = tqdm.tqdm(range(filesize), "Sending", unit="B", unit_scale=True, unit_divisor=1024)
    #
    #         f = open(filename, "rb")
    #         while True:
    #             # read the bytes from the file
    #             bytes_read = f.read(BUFFER_SIZE)
    #             if not bytes_read:
    #                 # file transmitting is done
    #                 f.close()
    #                 s.close()
    #                 break
    #             # we use sendall to assure transimission in
    #             # busy networks
    #             s.sendall(bytes_read)
    #     # close the socket
    #     s = socket.socket()
    #     s.connect((host, port))
    #     s.send("ALL FILES SEND")
    #
    #     s.close()

    # TODO - TO RECEIVE BUTTON EVENTS
    def theaded_TCP_SERVER(self):
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to the port
        # https://stackoverflow.com/questions/8033552/python-socket-bind-to-any-ip
        # Binding to '' has the same effect as to '0.0.0.0' makes the transition to IPv6 easier.
        # when listening on 127.0.0.1 the service is only bound to the loopback interface (only available on the local machine)
        #127.0.0.1 is normally the IP address assigned to the "loopback" or local-only interface. This is a "fake" network adapter that can only communicate within the same host.
        #https://stackoverflow.com/questions/38256851/why-does-my-python-tcp-server-need-to-bind-to-0-0-0-0-and-not-localhost-or-its
        #https://stackoverflow.com/questions/39314086/what-does-it-mean-to-bind-a-socket-to-any-address-other-than-localhost/39314221
        server_address = ('0.0.0.0', 7300)

        logger.info('starting TCP SERVER on %s port %s' % (server_address[0],server_address[1]))
        #print('starting  TCP SERVER on %s port %s' % (server_address))
        sock.bind(server_address)

        # Listen for incoming connections
        sock.listen(5)

        while True:
            # Wait for a connection
            logger.info('waiting for a connection')
            #print('waiting for a connection')
            connection, client_address = sock.accept()
            try:
                logger.info('connection from %s' % client_address)
                #print('connection from', client_address)

                # Receive the data in small chunks and retransmit it
                while True:
                    data = connection.recv(1024)
                    logger.info('received %s' % data)
                    #print('received "%s"' % data)
                    if data:
                        logger.debug('data recieved')
                        print('data recieved')
                        #connection.sendall(data)
                    else:
                        logger.debug('no more data from %s' % client_address)
                        #print('no more data from', client_address)
                        break

            finally:
                # Clean up the connection
                connection.close()

    def broadcast(self):

        broadcast_adress = '192.168.1.255'

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)

        # TODO USE SCAPY INSTEAD
        mac = get_mac()
        mac = ':'.join(("%012X" % mac)[i:i + 2] for i in range(0, 12, 2))


        host_info = {'host_name': host_name, 'host_ip': host_ip, 'host_mac': mac, 'host_port': 7300,
                     'broadcast_adress': broadcast_adress}

        print ("UDP BROADCAST:" , host_info)


        s.sendto(str(host_info), ('192.168.1.255', 7300))

    def arp(self):

        #from scapy.all import * # for some reason doestn work at top level
        from scapy.layers.l2 import Ether, ARP
        from scapy.sendrecv import srp
        gw = conf.route.route("0.0.0.0")[2] # gateway 192.168.1.1
        gw_and_cidre = gw + "/24"
        # ('ARP:', u'192.168.1.1/24')
        logger.info('ARP:", "Gateway = %s' % gw_and_cidre)
        #print("ARP:", "Gateway =" , gw_and_cidre)

        # COMPLETE ARP REQUEST
        ans , unans = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=str(gw_and_cidre)), timeout=2, verbose=False)
        arp_list = {}
        for x in range(0, len(ans)):
            arp_list_item = {x: {"mac": ans[x][1][ARP].hwsrc, "ip": ans[x][1][ARP].psrc}}
            arp_list.update(arp_list_item)

        #print(arp_list)
        return arp_list

    # CHECK if DEVICE MAC and IP MATCH .. then send message :)
    def confirm_ip(self,data):

        """ data
                'mode': "event_card",
                'device': chosen_device , # ip & mac [192.168 , ff:ff:ff:]
                'title': value2,
                'message': value3,
                'event': value4
                'event_duration': value6,
                'image': value7,
        """

        destination_mac = data['device'][1] # device we want to send to
        stored_ip = data['device'][0] # previously stored IP Adress .. might not be the current one (dhcp changes)

        logger.info('searching %s in your network' % destination_mac)
        #print("searching" , destination_mac , "in your network")
        # ARP PING [ SINGLE ]
        # ideally MAC adress matches with the one we stored
        #response = self.arp_ping(data['device'][0]) # selected device IP
        mac = getmacbyip(stored_ip) # scapy method
        # print ("mac by ip" , mac)

        if mac == destination_mac:
            # THIS IS THE CORRECT DEVICE
            # SEND MESSAGE
            self.send_message(data) # data has CORRECT IP

        elif mac != destination_mac and mac != None:
            # DIFFERENT DEVICE FOUND
            # MAKE FULL ARP REQUEST TO FIND MAC
            # IF FOUND SEND MESSAGE TO CORRECT IP

            network_devices = self.arp()
            # find mac in network devices
            # {0: {'ip': '192.168.1.1', 'mac': 'e8:de:27:f6:f8:26'}, 1: {'ip': '192.168.1.101', 'mac': 'd0:50:99:3b:49:00'},
            device_found = self.lookup_mac_in_arp(network_devices, data) # True IP if MAC FOUND , Flase if Not
            if device_found:
                # 'device': chosen_device , # ip & mac [192.168 , ff:ff:ff:]
                # # data DOES NOT HAVE the correct IP , we  give it the one we found in ARP
                # WHICH IS THE CURRENT IP OF THE MAC we have stored
                data['device'] = [device_found, destination_mac]
                self.send_message(data)

                # UPDATING DEVICE IP IN OUR STORED DATA
                # THIS WILL MAKE THE NEXT SEND MESSAGE WORK WITH A ARP PING , instead of ARP BROADCAST
                # REDUCES NETWORK TRAFFIC ;)
                device_list = self.LoadJsonFromFile()
                new_device = {'mac': destination_mac, 'dhcp_hostname': 'ARP', 'host_ip': [device_found]}
                updated_device_list = self.check_if_new_device(new_device, device_list)
                self.WriteJsonToFile(updated_device_list)
            else:

                print("DEVICE NOT FOUND", destination_mac)

        elif mac == None:
            # UNREACHABLE IP ADDRESS
            # MAKE FULL ARP REQUEST TO FIND MAC
            # IF FOUND SEND MESSAGE TO CORRECT IP
            # IF NOT FOUND INFORM USER
            network_devices = self.arp()
            device_found = self.lookup_mac_in_arp(network_devices, data) # True IP if MAC FOUND , Flase if Not
            if device_found:
                data['device'] = [device_found, destination_mac]
                self.send_message(data)

                device_list = self.LoadJsonFromFile()
                new_device = {'mac': destination_mac, 'dhcp_hostname': 'ARP', 'host_ip': [device_found]}
                updated_device_list = self.check_if_new_device(new_device, device_list)
                self.WriteJsonToFile(updated_device_list)
            else:
                print("DEVICE NOT FOUND" , destination_mac)

    def lookup_mac_in_arp(self,network_devices,data):
        logger.info('discovered devices %s' % network_devices)

        #print(" discovered devices" , network_devices)
        #    ('network devices', {0: {'ip': '192.168.1.1', 'mac': 'e8:de:27:f6:f8:26'}, 1: {'ip': '192.168.1.101', 'mac': 'd0:50:99:3b:49:00'}, 2: {'ip': '192.168.1.105', 'mac': '00:17:88:27:fd:01'}, 3: {'ip': '192.168.1.100', 'mac': '24:a1:60:54:2b:bc'}, 4: {'ip': '192.168.1.106', 'mac': '78:0f:77:63:66:96'}, 5: {'ip': '192.168.1.107', 'mac': '50:c7:bf:b6:ef:30'}, 6: {'ip': '192.168.1.108', 'mac': 'fc:a6:67:72:c9:83'}, 7: {'ip': '192.168.1.112', 'mac': 'b8:27:eb:e8:90:b9'}, 8: {'ip': '192.168.1.116', 'mac': '24:a1:60:45:e3:20'}, 9: {'ip': '192.168.1.118', 'mac': '24:a1:60:54:31:28'}, 10: {'ip': '192.168.1.115', 'mac': '50:02:91:9f:3e:30'}, 11: {'ip': '192.168.1.113', 'mac': '50:02:91:92:3d:d4'}})
        for x in network_devices.values():
            #print(x, data['device'])
            #print(x['mac'], data['device'])
            # x =    (0, [u'192.168.1.109', u'84:cc:a8:60:76:d4'])
            if x['mac'] == data['device'][1]:
                return x['ip']
        return False

    # SEND A MESSAGE , use THREAD to not block main
    def send_message(self,data):
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = (data['device'][0], 7300)
        logger.info('connecting to %s port %s' % (server_address[0],server_address[1]))
        #print('connecting to %s port %s' % server_address)
        sock.connect(server_address)

        logger.info('DATA %s' % str(data))
        try:

            #print("radio", data['event'])
            # translate choice into string for readability
            event = ''
            if 'event' in data:
                if data['event'] == 0: event = 'default';
                if data['event'] == 1: event = 'finished';
                if data['event'] == 2: event = 'failure';

                data['event'] = event

            message = json.dumps(data, sort_keys=True)

            logger.info('Sending to %s' % data['device'][0])
            logger.info('DATA %s' % str(message))
            #print('Sending to {}'.format(data['device'][0]))

            # Send data
            sock.sendall(message.encode('utf-8'))

        except Exception as e:
            print(e)
            print traceback.print_exc()
            print('#!! SEND FAILURE !!#' , data['device'][0])

        finally:
            logger.info('closing socket')
            #print('closing socket')
            sock.close()

    def JSONFormatter(self,json_string):
        try:
            string_remover = json_string.replace("\"", "")
            json_acceptable_string = string_remover.replace("'", "\"")
            logger.info('json_acceptable_string %s' % json_acceptable_string)
            #print("json_acceptable_string",json_acceptable_string)
            json_data = json.loads(json_acceptable_string)
            logger.info('json_data %s' % json_data)
            #print("json_data", json_data)
            return json_data
        except:
            print("ERROR - BAD JSON FORMAT ;)", json_acceptable_string)

    def check_if_new_device(self, new_device, device_list):


        #print("device_list" , device_list)
        #print("new_device", new_device)
        # 1 FULL MATCH

        if device_list == None:
            return new_device # NEW DEVICE LIST

        if new_device in device_list:
            print ("<FULL MATCH> --> " + str(new_device))
            return device_list
            #pass

        if new_device not in device_list:
            # Falls mac adresse bekannt ist dann wird alter eintrag  geupdatet
            # um duplicate zu verhindern
            return self.update_devce_list(new_device, device_list)


    def update_devce_list(self, new_device , device_list):

        if device_list:
            for x in device_list:
                #('device_list', [u"{'mac': '24:6f:28:8f:43:6c', 'dhcp_hostname': 'espressif', 'host_ip': ('192.168.1.111', '255.255.255.0', '192.168.1.1', '192.168.1.1')}", u"{'mac': '84:cc:a8:60:76:d4', 'dhcp_hostname': 'espressif', 'host_ip': ('192.168.1.109', '255.255.255.0', '192.168.1.1', '192.168.1.1')}", u"{'mac': '84:cc:a8:60:76:d4', 'dhcp_hostname': 'espressif', 'host_ip': ('192.168.1.109', '255.255.255.0', '192.168.1.1', '192.168.1.1')}"])
                # 4 SAME MAC , NEW HOSTNAME
                if (x['mac'] == new_device['mac']) and (x['dhcp_hostname'] != new_device['dhcp_hostname'] and  new_device['dhcp_hostname'] != "ARP"): # added this last one because we use this function again during arp requests and we use placeholder arp to prevent renaming to arp  as hostname

                    print("CHANGE: " + x['dhcp_hostname'] + " TO: " + new_device['dhcp_hostname'])
                    x['dhcp_hostname'] = new_device['dhcp_hostname']  # UPDATE HOSTNAME

                # 2 NEW IP , SAME MAC
                if x['host_ip'] != new_device['host_ip'] and x['mac'] == new_device['mac']:
                    # print("Updated IP_ADRESS : " + x['host'] +  " TO : " +  new_device['host'])

                    logger.info('IP UPDATE -->  %s TO %s' % (str(x['dhcp_hostname']),str(new_device['host_ip'])))
                    #print(' IP UPDATE --> ' + str(x['dhcp_hostname']) + " TO " + str(new_device['host_ip']))
                    x['host_ip'] = new_device['host_ip']  # UPDATE IP
            if new_device not in device_list and  new_device['dhcp_hostname'] != "ARP":
                device_list.append(new_device)
                return device_list
            return device_list
        else:
            # ('new_device', {u'mac': u'84:cc:a8:60:76:d4', u'host_ip': [u'192.168.1.109', u'255.255.255.0', u'192.168.1.1', u'192.168.1.1'], u'dhcp_hostname': u'espressif'})
            return [new_device] # FIRST  LIST CREATED


    def LoadJsonFromFile(self):
        # {"mac": "84:cc:a8:60:76:d4", "host_ip": ["192.168.1.109", "255.255.255.0", "192.168.1.1", "192.168.1.1"],
        # "dhcp_hostname": "espressif"}

        try:
            # OPEN from path
            path = eg.configDir + '\plugins\M5Stack'
            # Load json
            json_data = open(
                path + '/' +
                'esp32_devices' + '.json', 'r'
            )

            loadedText = json_data.read()
            JSONARRAY = json.loads(loadedText)

            return JSONARRAY

        except:
            return  # None



    def WriteJsonToFile(self, json_list):
        path = eg.configDir + '\plugins\M5Stack'
        # 1. Create Dir if doesnt exists

        if (not os.path.exists(path) and not os.path.isdir(path)):
            print('Created new Directory' + str(os.path.exists(path)))
            os.makedirs(path)
        else:
            logger.info('Directory Exists: %s' % str(os.path.exists(path)))
            logger.info('Path: %s' % str(os.path.exists(path)))
            #print('Directory Exists: ' + str(path))
            #print('Path:' + str(path))

        # CREATE NEW FILE

        f = open(
            path + '/' +
            "esp32_devices" + '.json', 'w'
        )

        data = json.dumps(json_list)
        f.write(data)
        f.close()

        logger.info('Config Updated')
        #print('Config Updated')

    def get_stored_device_list(self):
        stored_devices = self.LoadJsonFromFile()

        device_list = []
        for x in stored_devices:
            device_list.append([x['host_ip'][0],x['mac']])

        return device_list

# -------------------------------
# # # # # # DEFAULT FOLDER LOADER
# -------------------------------

    def default_loader(self):
        default_choices = []
        default_png = glob.glob(self.info.path + "\\MAIN\\SERVER\\TEMPLATES\\DEFAULT\\*.png")

        for x in default_png:
            default_choices.append(os.path.basename(x))
        logger.info(default_choices)
        #print default_choices
        return default_choices

# --------------------------------
# # # # # # SPECIFIC FOLDER LOADER
# --------------------------------

    def specific_loader(self,TEMPLATE):
        specific_choices = []
        specific_png = glob.glob(self.info.path + "\\MAIN\\SERVER\\TEMPLATES\\{}\\*.png".format(TEMPLATE))


        for x in specific_png:
            specific_choices.append(os.path.basename(x))

        #print self.info.path
        logger.info(specific_choices)
        #print specific_choices
        return specific_choices

# -------------------------------------------------------
# SETTINGS SECTION
# -------------------------------------------------------

class Setup(eg.ActionBase):

    def __call__(self):
        broadcast_adress = '255.255.255.255'

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name)

        mac = get_mac()
        mac = ':'.join(("%012X" % mac)[i:i + 2] for i in range(0, 12, 2))
        print(mac)

        print("Hostname :  ", host_name)
        print("IP : ", host_ip)

        host_info = {"host_name": str(host_name), "host_ip": host_ip, "host_mac": str(mac), "host_port": 7300,
                     "broadcast_adress": str(broadcast_adress)}

        print("sending :", host_info)
        s.sendto(str(host_info), (broadcast_adress, 7200))


class ARP(eg.ActionBase):

    def __call__(self):
        #from scapy.all import *
        import os
        ans, unans = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst="192.168.1.0/24"), timeout=2, verbose=False)
        arp_list = {}
        for x in range(0, len(ans)):
            arp_list_item = {x: {"mac": ans[x][1][ARP].hwsrc, "ip": ans[x][1][ARP].psrc}}
            arp_list.update(arp_list_item)

        print(arp_list)

class Firewall_Open_Port(eg.ActionBase):

    def __call__(self):
        pass

# -------------------------------------------------------
# NOTIFICATION SECTION
# -------------------------------------------------------

class EventCard(eg.ActionBase):

    def __call__(self , value1=0, value2='', value3='', value4=0, value6=0, value7=0):
        ip_mac_pair_list = self.plugin.get_stored_device_list()
        chosen_device = ip_mac_pair_list[value1]

        # data['image'] = 0 ( m_default.png)
        # MAKE SURE that in  data['image']  are all images
        # the esp32 device will look into the list and use the image / images
        # ['default.png']  or possibly multiple for other templates

        # data['mode'] = EVENT_CARD for example ...named after folder in program data
        image_list = self.plugin.default_loader() + self.plugin.specific_loader("EVENT_CARD")
        selected_image = image_list[value7]

        value2 = eg.ParseString(value2)
        value3 = eg.ParseString(value3)


        data = \
            {
                'mode': "EVENT_CARD", # named exactly after Eventghost folder important !
                'device': chosen_device , # ip & mac [192.168 , ff:ff:ff:]
                'title': value2,
                'message': value3,
                'event': value4,
                'event_duration': value6,
                'image': selected_image,
            }

        self.plugin.confirm_ip(data)

    def Configure(self, value1=0, value2='', value3='', value4=0, value6=3, value7=0):


        panel = eg.ConfigPanel(self)
        ip_mac_pair_tuple = self.plugin.get_stored_device_list()

        mac_list = []
        for x in ip_mac_pair_tuple:
            mac_list.append(x[1]) # mac


        device = panel.Choice(value1, choices=mac_list)
        title = panel.TextCtrl(value2)
        message = panel.TextCtrl(value3) # style = wx.TE_MULTILINE
        eventlist = ['Event', 'Finished', 'Running']

        #event = panel.RadioBox(value4, label = 'RadioBox', pos = (80,10),
         #majorDimension = 1, style = wx.RA_SPECIFY_ROWS, choices=eventlist)

        event = wx.RadioBox(panel, pos=(10, 10), choices=eventlist,
                                majorDimension=1, style=wx.RA_SPECIFY_ROWS)
        # label='pick event mode'
        event.SetSelection(value4)



        #checkbox = panel.CheckBox(value5)
        #print("value6", value6)
        event_duration = panel.SpinIntCtrl(value6, min=0, max=60)

        image_list = self.plugin.default_loader() + self.plugin.specific_loader("EVENT_CARD")
        image = panel.Choice(value7, choices=image_list)



        panel.AddLine("Device:", device)
        panel.AddLine("Title:", title)
        panel.AddLine("Message:", message)
        panel.AddLine("Mode:", event)
        #panel.AddLine("Event:", checkbox)
        panel.AddLine("Event_duration:", event_duration)
        panel.AddLine("Image:", image)


        while panel.Affirmed():
            # richtige reihenfolge anscheinend wichtig / so wie auch in UI angeordnet
            panel.SetResult(
                device.GetValue(),
                title.GetValue(),
                message.GetValue(),
                event.GetSelection(), #Returns the index of the selected item
                #checkbox.GetValue(), # returns true or false depending on if the checkbox is checked or not.
                event_duration.GetValue(),
                image.GetValue()
            )

class List(eg.ActionBase):

    def __call__(self , value1=0, value2='' , value3='' , value4='', value5='', value6=0 , value7=0):
        ip_mac_pair_list = self.plugin.get_stored_device_list()
        chosen_device = ip_mac_pair_list[value1]

        # data['mode'] = EVENT_CARD for example ...named after folder in program data
        image_list = self.plugin.default_loader() + self.plugin.specific_loader("LIST")
        selected_image = image_list[value7]

        # SUPPORT FOR VARIABLES / Execute Code IN EVENTGHOST input field {eg.result}
        value2 = eg.ParseString(value2)
        value3 = eg.ParseString(value3)
        value4 = eg.ParseString(value4)
        value5 = eg.ParseString(value5)

        data = \
            {
                'mode': "LIST", # named exactly after Eventghost folder important !
                'device': chosen_device , # ip & mac [192.168 , ff:ff:ff:]
                'title': value2,
                'message': [value3, value4, value5],
                'event': value6,
                'image': selected_image,
            }

        self.plugin.confirm_ip(data)
        pass

    def Configure(self, value1=0, value2='', value3='', value4='', value5='', value6=0, value7=0):
        panel = eg.ConfigPanel(self)

        ip_mac_pair_tuple = self.plugin.get_stored_device_list()

        mac_list = []
        for x in ip_mac_pair_tuple:
            mac_list.append(x[1]) # mac

        device = panel.Choice(value1, choices=mac_list)
        title = panel.TextCtrl(value2)

        item1 = panel.TextCtrl(value3)
        item2 = panel.TextCtrl(value4)
        item3 = panel.TextCtrl(value5)

        eventlist = ['Normal', 'Complete', 'Failure']
        event = wx.RadioBox(panel, pos=(10, 10), choices=eventlist,
                            majorDimension=1, style=wx.RA_SPECIFY_ROWS)
        # label='pick event mode'
        event.SetSelection(value6)

        image_list = self.plugin.default_loader() + self.plugin.specific_loader("LIST")
        image = panel.Choice(value7, choices=image_list)

        panel.AddLine("Device:", device)
        panel.AddLine("Title:", title)
        panel.AddLine("Item 1:", item1)
        panel.AddLine("Item 2:", item2)
        panel.AddLine("Item 3:", item3)
        panel.AddLine("Mode:", event)
        panel.AddLine("Image:", image)

        while panel.Affirmed():
            panel.SetResult(
                device.GetValue(),
                title.GetValue(),

                item1.GetValue(),
                item2.GetValue(),
                item3.GetValue(),

                event.GetSelection(),
                image.GetValue(),
            )


class KeyValue(eg.ActionBase):

    def __call__(self , value1=0, value2='' , value3='' , value4=0, value5='', value6='' , value7=0 ):
        ip_mac_pair_list = self.plugin.get_stored_device_list()
        chosen_device = ip_mac_pair_list[value1]

        # data['mode'] = EVENT_CARD for example ...named after folder in program data
        image_list = self.plugin.default_loader() + self.plugin.specific_loader("KEY_VALUE")
        selected_image_one = image_list[value4]
        selected_image_two = image_list[value7]

        # SUPPORT FOR VARIABLES / Execute Code IN EVENTGHOST input field {eg.result}
        value2 = eg.ParseString(value2) # title
        value3 = eg.ParseString(value3) # text

        value5 = eg.ParseString(value5) # title
        value6 = eg.ParseString(value6) # text

        data = \
            {
                'mode': "KEY_VALUE", # named exactly after Eventghost folder important !
                'device': chosen_device , # ip & mac [192.168 , ff:ff:ff:]
                'title': [value2 , value5],
                'message': [value3, value6],
                'image': [selected_image_one, selected_image_two],
            }

        self.plugin.confirm_ip(data)

    def Configure(self, value1=0, value2='', value3='', value4=0, value5='', value6='', value7=0):
        panel = eg.ConfigPanel(self)

        ip_mac_pair_tuple = self.plugin.get_stored_device_list()
        mac_list = []
        for x in ip_mac_pair_tuple:
            mac_list.append(x[1]) # mac

        device = panel.Choice(value1, choices=mac_list)

        title1 = panel.TextCtrl(value2)
        data1 = panel.TextCtrl(value3)
        image_list = self.plugin.default_loader() + self.plugin.specific_loader("LIST")
        image1 = panel.Choice(value4, choices=image_list)

        title2 = panel.TextCtrl(value5)
        data2 = panel.TextCtrl(value6)
        image2 = panel.Choice(value7, choices=image_list)

        panel.AddLine("Device:", device)
        panel.AddLine("Title 1:", title1)
        panel.AddLine("Data 1:", data1)
        panel.AddLine("Icon 1:", image1)

        panel.AddLine("Title 2:", title2)
        panel.AddLine("Data 2:", data2)
        panel.AddLine("Icon 2:", image2)

        while panel.Affirmed():
            panel.SetResult(
                device.GetValue(),
                title1.GetValue(),
                data1.GetValue(),
                image1.GetValue(),

                title2.GetValue(),
                data2.GetValue(),
                image2.GetValue()
            )

class Single(eg.ActionBase):

    def __call__(self , value1=0, value2='', value3=0, value4=0, value5=0):
        ip_mac_pair_list = self.plugin.get_stored_device_list()
        chosen_device = ip_mac_pair_list[value1]

        # SUPPORT FOR VARIABLES / Execute Code IN EVENTGHOST input field {eg.result}
        value2 = eg.ParseString(value2) # text
        if value3 == 0: value3 = 'normal'; # font size
        if value3 == 1: value3 = 'medium';
        if value3 == 2: value3 = 'big';

        if value4 == 0: value4 = 'normal'; # color
        if value4 == 1: value4 = 'finished';
        if value4 == 2: value4 = 'failure';

        if value5 == 0: value5 = 'normal'; # capitalisation
        if value5 == 1: value5 = 'capital';


        data = \
            {
                'mode': "SINGLE", # named exactly after Eventghost folder important !
                'device': chosen_device, # ip & mac [192.168 , ff:ff:ff:]
                'message': value2,

                'font_size': value3,
                'color': value4,
                'capital': value5,
            }

        self.plugin.confirm_ip(data)

    def Configure(self, value1=0, value2='', value3=0, value4=0, value5=0):
        panel = eg.ConfigPanel(self)

        ip_mac_pair_tuple = self.plugin.get_stored_device_list()
        mac_list = []
        for x in ip_mac_pair_tuple:
            mac_list.append(x[1]) # mac

        device = panel.Choice(value1, choices=mac_list)

        text = panel.TextCtrl(value2)

        size_list = ['small', 'medium', 'big']
        font_size = wx.RadioBox(panel, pos=(10, 10), choices=size_list,
                            majorDimension=1, style=wx.RA_SPECIFY_ROWS)
        font_size.SetSelection(value3)

        color_list = ['normal', 'finished', 'failure']
        color = wx.RadioBox(panel, pos=(10, 10), choices=color_list,
                                majorDimension=1, style=wx.RA_SPECIFY_ROWS)
        color.SetSelection(value4)

        capitalized_list = ['normal', 'capital']
        capitalized = wx.RadioBox(panel, pos=(10, 10), choices=capitalized_list,
                            majorDimension=1, style=wx.RA_SPECIFY_ROWS)
        capitalized.SetSelection(value5)



        panel.AddLine("Device:", device)
        panel.AddLine("Text:", text)
        panel.AddLine("Font Size:", font_size)
        panel.AddLine("Color:", color)
        panel.AddLine("Capitalization:", capitalized)



        while panel.Affirmed():
            panel.SetResult(
                device.GetValue(),
                text.GetValue(),

                font_size.GetSelection(),
                color.GetSelection(),
                capitalized.GetSelection(),

            )