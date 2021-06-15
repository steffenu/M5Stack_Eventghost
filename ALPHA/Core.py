import network
import socket
import ubinascii
import _thread
import os
import json
import time
import wifiCfg

from m5stack import lcd
tft = lcd

m5_device_list = \
    {
        "Core": {"width": 320, "height": 240},
        "Core2": {"width": 320, "height": 240},
        "StickC": {"width": 80, "height": 160},
        "StickCPlus": {"width": 135, "height": 240},
        "E-ink": {"width": 200, "height": 200},
        "Paper": {"width": 540, "height": 960},
    }

m5_device_list_noscreen = \
    {
        "Atom Lite": {"imu": False, },
        "Atom Matrix": {"imu": True, },
    }

# IDENTIFYING THE MODEL , BY SCREEN , or other unique characteristics
def GET_M5_MODEL():

    width, height = tft.screensize()

    for x in m5_device_list.items():
        if {"width": width, "height": height} in x:

            # since core/core2 have same screen ... we differntiate by import availabaility
            if x[1]['width'] == 320:
                try:
                    import m5stack_ui
                    return "Core 2"
                except:
                    try:
                        import base
                        return "Atom" # Atom Lite or matrix
                    except:
                        return "Core"
            return x[0]
    return "Unknown ESP32 Model"

#alive = True # GLOBAL VARIABLE to STOP PAIRING THread
#LOADING = True # GLOBAL VARIABLE to stop loading animations threads

# enable station interface and connect to WiFi access point
nic = network.WLAN(network.STA_IF)
nic.active(True)
model = GET_M5_MODEL()
dhcp_hostname = nic.config(dhcp_hostname=model) # changing default hostname to detected model
SSID, PASS = wifiCfg.deviceCfg.wifi_read_from_flash()
nic.connect(SSID, PASS)
while not nic.isconnected(): pass


mac = nic.config('mac')
host_ip = list(nic.ifconfig()) # return a tuple json doesnt allow tuple

mac_decoded = ubinascii.hexlify(mac, ':').decode()


# SEND PAIRING REQUEST EVERY 30 Secs
def UDP_PAIRING_REQUEST(dhcp_hostname,mac_decoded,host_ip):
    broadcast_adress = ('192.168.1.255', 7200)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    m5_info = str({'dhcp_hostname': dhcp_hostname, 'mac': mac_decoded, 'host_ip': host_ip})

    global alive

    while alive == True :
        s.sendto(m5_info.encode('utf-8'), broadcast_adress)
        should_i_stop , addr2 = s.recv(1024) # recv = (bytes)
        time.sleep(30)

# SEND !!FILE!! REQUEST EVERY 30 Secs
def UDP_FILE_REQUEST():
    dhcp_hostname = nic.config('dhcp_hostname')
    host_ip = list(nic.ifconfig())  # return a tuple json doesnt allow tuple
    mac_decoded = ubinascii.hexlify(mac, ':').decode()

    broadcast_adress = ('192.168.1.255', 7200)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    m5_info = str({'file_request': str(True), 'dhcp_hostname': dhcp_hostname, 'mac': mac_decoded, 'host_ip': host_ip})

    global FILE_REQUEST

    while FILE_REQUEST == True :
        s.sendto(m5_info.encode('utf-8'), broadcast_adress)
        #s.sendto('its a cool', broadcast_adress)
        time.sleep(30)

def UDP_SERVER(dhcp_hostname,mac_decoded,host_ip):
    port = 7300

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((host_ip[0], port))  # make sure to change to device IP


    while True:
        data, addr = s.recvfrom(1024)
        decoded_data = data.decode()

        #if "NICE SETUP BRO" in decoded_data:


        if data:

            global LOADING
            global alive
            alive = False  # STOPPING PAIRING THREAD
            LOADING = False  # STOP ANIMATION THREAD
            #label0 = M5TextBox(20, 10, str(decoded_data), lcd.FONT_Default, 0xFFFFFF, rotate=0)

            try:
                """
                {'host_port': 7300, 'broadcast_adress': '192.168.1.255', 'host_name': 'NewSilver',
                               'host_mac': 'D0:50:99:3B:49:00', 'host_ip': '192.168.1.101'}
                """

                # TCP_DEVICE_INFO_RESPONSE(status, mac, host)
                WriteJsonToFile(decoded_data)  # device info
                # After recveving config . recieve files and show rdy screen
                NOTIFICATION_MODE_UPDATE_SCREEN()
                _thread.start_new_thread(FILE_UPDATE_SERVER, ()) # BLOCKING at accept
                _thread.start_new_thread(UDP_FILE_REQUEST, ()) # CAN RUN

            except Exception as e:
                #rectangle0.hide()
                #label1.hide()
                #label2.hide()
                #label3.hide()
                #label4.hide()
                #image0.hide()
                label0 = M5TextBox(20, 10, str("Error in UDP_SERVER"), lcd.FONT_Default, 0xFFFFFF, rotate=0)
                label9 = M5TextBox(0, 30, str(e), lcd.FONT_Default, 0xFFFFFF, rotate=0)

                import sys;
                from uio import StringIO
                s = StringIO();
                sys.print_exception(e, s)
                s = s.getvalue();
                s = s.split('\n')
                line = s[1].split(',');
                line = line[1];
                error = s[2];
                err = error + line;
                label12 = M5TextBox(0, 60, str(err), lcd.FONT_Default, 0xFFFFFF, rotate=0)

def FILE_UPDATE_SERVER():
    try:
        # device's IP address
        SERVER_HOST = "0.0.0.0"
        SERVER_PORT = 7300
        # receive 4096 bytes each time
        BUFFER_SIZE = 4096
        SEPARATOR = "<SEPARATOR>"

        # create the server socket
        # TCP socket
        s = socket.socket()

        # bind the socket to our local address
        s.bind((SERVER_HOST, SERVER_PORT))

        # enabling our server to accept connections
        # 5 here is the number of unaccepted connections that
        # the system will allow before refusing new connections
        s.listen(10)
        print(" Listening as", SERVER_HOST, SERVER_PORT)

        l = True
        while l:
            # accept connection if there is any
            client_socket, address = s.accept()
            # if below code is executed, that means the sender is connected
            print(address, "is connected.")

            # receive the file infos
            # receive using client socket, not server socket
            received = client_socket.recv(BUFFER_SIZE).decode()  # decode add
            print(received)

            if received == "ALL FILES SEND":

                #print("## UPDATE COMPLETE - SHUTTING DOWN  ##")

                s.close()
                #import machine
                #machine.reset() # RESTARTING
                #NOTIFICATION_MODE_READY_SCREEN()
                break

            client_socket.send("OK")
            #label9 = M5TextBox(0, 150, str(received), lcd.FONT_Default, 0xFFFFFF, rotate=0)

            filename, filesize = received.split(SEPARATOR)
            print(filename)
            print(filesize)
            # remove absolute path if there is
            #filename = os.path.basename(filename) NOT AVAILABLE IN MICROPYTHON :D
            filename = filename.replace("SETUP\\", "")
            # convert to integer
            filesize = int(filesize)

            # start receiving the file from the socket
            # and writing to the file stream


            if '.png' in filename:
                path = '/flash/res/' + filename

            else:
                path = '/flash/eventghost/' + filename

            """
            /flash/eventghost
            templates.py
            server.py
            
            /res
            image_1
            image_2 
            """

            f = open(path, "wb")

            while True:
                # read 1024 bytes from the socket (receive)
                bytes_read = client_socket.recv(BUFFER_SIZE)
                if not bytes_read:
                    # nothing is received
                    # file transmitting is done
                    print("recieve done")
                    break
                # write to the file the bytes we just received
                f.write(bytes_read)
                # update the progress bar

            # close the client socket
            f.close()
            client_socket.close()
    except Exception as e:
        label0 = M5TextBox(0, 10, str("Error in FILE_SERVER"), lcd.FONT_Default, 0xFFFFFF, rotate=0)
        label9 = M5TextBox(0, 30, str(e), lcd.FONT_Default, 0xFFFFFF, rotate=0)

        import sys;
        from uio import StringIO
        s = StringIO();
        sys.print_exception(e, s)
        s = s.getvalue();
        s = s.split('\n')
        line = s[1].split(',');
        line = line[1];
        error = s[2];
        err = error + line;
        label12 = M5TextBox(0, 60, str(err), lcd.FONT_Default, 0xFFFFFF, rotate=0)

# # TCP
# def FILE_UPDATE_SERVER():
#     try:
#         # device's IP address
#         SERVER_HOST = "0.0.0.0"
#         SERVER_PORT = 7300
#         # receive 4096 bytes each time
#         BUFFER_SIZE = 4096
#         SEPARATOR = "<SEPARATOR>"
#
#         # create the server socket
#         # TCP socket
#         s = socket.socket()
#
#         # bind the socket to our local address
#         s.bind((SERVER_HOST, SERVER_PORT))
#
#         # enabling our server to accept connections
#         # 5 here is the number of unaccepted connections that
#         # the system will allow before refusing new connections
#         s.listen(10)
#         print(" Listening as", SERVER_HOST, SERVER_PORT)
#
#         l = True
#         while l:
#             # accept connection if there is any
#             client_socket, address = s.accept()
#             # if below code is executed, that means the sender is connected
#             print(address, "is connected.")
#
#             # receive the file infos
#             # receive using client socket, not server socket
#             received = client_socket.recv(BUFFER_SIZE).decode()  # decode add
#             if received == "ALL FILES SEND":
#
#                 #print("## UPDATE COMPLETE - SHUTTING DOWN  ##")
#
#                 s.close()
#                 import machine
#                 machine.reset() # RESTARTING
#                 #NOTIFICATION_MODE_READY_SCREEN()
#                 break
#
#             client_socket.send("OK")
#             #label9 = M5TextBox(0, 150, str(received), lcd.FONT_Default, 0xFFFFFF, rotate=0)
#
#             filename, filesize = received.split(SEPARATOR)
#             # remove absolute path if there is
#             #filename = os.path.basename(filename) NOT AVAILABLE IN MICROPYTHON :D
#             filename = filename.replace("SETUP\\", "")
#             # convert to integer
#             filesize = int(filesize)
#
#             # start receiving the file from the socket
#             # and writing to the file stream
#             path = '/flash/res/' + filename
#             f = open(path, "wb")
#             while True:
#                 # read 1024 bytes from the socket (receive)
#                 bytes_read = client_socket.recv(BUFFER_SIZE)
#                 if not bytes_read:
#                     # nothing is received
#                     # file transmitting is done
#                     print("recieve done")
#                     break
#                 # write to the file the bytes we just received
#                 f.write(bytes_read)
#                 # update the progress bar
#
#             # close the client socket
#             f.close()
#             client_socket.close()
#     except Exception as e:
#         label0 = M5TextBox(0, 10, str("Error in FILE_SERVER"), lcd.FONT_Default, 0xFFFFFF, rotate=0)
#         label9 = M5TextBox(0, 30, str(e), lcd.FONT_Default, 0xFFFFFF, rotate=0)
#
#         import sys;
#         from uio import StringIO
#         s = StringIO();
#         sys.print_exception(e, s)
#         s = s.getvalue();
#         s = s.split('\n')
#         line = s[1].split(',');
#         line = line[1];
#         error = s[2];
#         err = error + line;
#         label12 = M5TextBox(0, 60, str(err), lcd.FONT_Default, 0xFFFFFF, rotate=0)



#1 Erstelle Directory
# Erstelle File mit device info

def WriteJsonToFile(eg_config):
    path = 'eventghost'
    #os.remove('dir2')
    # 1. Create Dir if doesnt exists

    path = '/flash/eventghost'

    try:
        # es gibt kein is directory modul ... deswegen nutzen wir ich einfach die fehlermeldung
        # für den fall das er den angegeben pfad nicht findet
        os.listdir(path)
        #circle0 = M5Circle(220, 22, 6, 0x00ff5d, 0x00ff5d) # Directoty vorhanden



    except:
        os.mkdir('eventghost')

    # 2. Create File (if it doesnt exists) /  add Json data to Array
    try:
        os.stat(path + '/' + "eg_config" + '.json')


    except:
        f = open(
            path + '/' +
            "eg_config" + '.json', 'w')


        data = json.dumps(eg_config)
        f.write(data)
        f.close()


def LoadJsonFromFile():
    path = 'eventghost'
    #os.remove('dir2')
    # 1. Create Dir if doesnt exists

    path = '/flash/eventghost'

    try:
        #os.stat(path + '/' + "eg_config" + '.json')
        f = open(
            path + '/' +
            "eg_config" + '.json', 'r'
        )

        loadedText = f.read()

        string_remover = loadedText.replace("\"", "")
        json_acceptable_string = string_remover.replace("'", "\"")
        json_data = json.loads(json_acceptable_string)  # https://stackoverflow.com/a/19391807/11678858



        f.close()
        return json_data

    except Exception as e:
        #printError(e)
        # if no valid json is loadable ... will show Config error on screen in tcp function
        # Shouldnt happen normally
        return






def TCP_DEVICE_INFO_RESPONSE(status,mac_decoded,host):

    rectangle0.hide()
    label1.hide()
    label2.hide()
    label3.hide()
    label4.hide()
    image0.hide()

    try :
        device_config = LoadJsonFromFile()
        #label0 = M5TextBox(10, 20, str(status), lcd.FONT_Default, 0xFFFFFF, rotate=0)

    except Exception as e:
        printError(e)
        return



    if device_config != None:

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Connect the socket to the port where the server is listening
            eventghost_adress = ("192.168.1.101", 7300)
            sock.connect(eventghost_adress)

            message = str({'status': status, 'mac': mac_decoded, 'host': host})
            sock.sendall(message.encode('utf-8'))

            amount_received = 0
            amount_expected = len(message)

            while amount_received < amount_expected:
                data = sock.recv(1024)
                amount_received += len(data)

            sock.close()

        except Exception as e:
            printError(e)

    if device_config == None:
        label0 = M5TextBox(10, 70, str('## NO DEVICE CONFIG ##'), lcd.FONT_Default, 0xFFFFFF, rotate=0)
        label1 = M5TextBox(0, 90, str(device_config), lcd.FONT_Default, 0xFFFFFF, rotate=0)
def printError(e):
    import sys;
    from uio import StringIO
    s = StringIO();
    sys.print_exception(e, s)
    s = s.getvalue();
    s = s.split('\n')
    line = s[1].split(',');
    line = line[1];
    error = s[2];
    err = error + line;
    label12 = M5TextBox(0, 60, str(err), lcd.FONT_Default, 0xFFFFFF, rotate=0)



### ANIMATIONS

def ANIMATION_PAIRING():
    # Set activce font
    tft.font(lcd.FONT_Default, rotate=0, color=0xffb300)

    # (320,240)
    SCREENSIZE = lcd.screensize()
    first_rectangle_X = SCREENSIZE[0] / 2 - 15

    rectangle1 = M5Rect(int(first_rectangle_X), 108, 30, 30, 0x7a7a7a, 0x7a7a7a) # mitte
    rectangle2 = M5Rect(int(first_rectangle_X) + 50, 108, 30, 30, 0x7a7a7a, 0x7a7a7a)#rechts
    rectangle0 = M5Rect(int(first_rectangle_X) - 50, 108, 30, 30,0x7a7a7a, 0x7a7a7a) # links

    # width of the string
    string = "PAIRING"
    string_width = lcd.textWidth(string)

    center_horizontal = (SCREENSIZE[0] / 2) - (string_width / 2)

    font_height = lcd.fontSize()
    center_vertical = SCREENSIZE[1] / 2 - font_height[1] / 2

    label0 = M5TextBox(int(center_horizontal), int(center_vertical) + 30, string, lcd.FONT_Default, 0xFFFFFF, rotate=0)

    global LOADING
    while LOADING == True:

        # STEP 1 FIRST ITEM WHITE
        rectangle0.setBgColor(0xFFFFFF)
        rectangle0.setBorderColor(0xFFFFFF)

        rectangle1.setBgColor(0x7a7a7a)
        rectangle1.setBorderColor(0x7a7a7a)

        rectangle2.setBgColor(0x7a7a7a)
        rectangle2.setBorderColor(0x7a7a7a)

        time.sleep(1)

        # STEP 2 FIRST, SECOND ITEM WHITE
        rectangle0.setBgColor(0xFFFFFF)
        rectangle0.setBorderColor(0xFFFFFF)

        rectangle1.setBgColor(0xFFFFFF)
        rectangle1.setBorderColor(0xFFFFFF)

        rectangle2.setBgColor(0x7a7a7a)
        rectangle2.setBorderColor(0x7a7a7a)

        time.sleep(1)

        # STEP 3 ALL RECTANGLE WHITE
        rectangle0.setBgColor(0xFFFFFF)
        rectangle0.setBorderColor(0xFFFFFF)

        rectangle1.setBgColor(0xFFFFFF)
        rectangle1.setBorderColor(0xFFFFFF)

        rectangle2.setBgColor(0xFFFFFF)
        rectangle2.setBorderColor(0xFFFFFF)

        time.sleep(1)

        # STEP 4 ALL RECTANGLE GREY
        rectangle0.setBgColor(0x7a7a7a)
        rectangle0.setBorderColor(0x7a7a7a)

        rectangle1.setBgColor(0x7a7a7a)
        rectangle1.setBorderColor(0x7a7a7a)

        rectangle2.setBgColor(0x7a7a7a)
        rectangle2.setBorderColor(0x7a7a7a)

        time.sleep(1)

        if LOADING == False:
            rectangle0.hide()
            rectangle1.hide()
            rectangle2.hide()
            label0.hide()

### NOTIFCATION MODES

def NOTIFICATION_MODE_READY_SCREEN():
    lcd.clear()
    config_data = LoadJsonFromFile()
    host_ip = list(nic.ifconfig())  # return a tuple json doesnt allow tuple
    # READY SCREEN

    rectangle0 = M5Rect(71, 12, 260, 100, 0x000000, 0x000000)
    image3 = M5Img(14, 11, "res/eg.png", True)
    label0 = M5TextBox(135, 52, config_data['host_name'], lcd.FONT_DejaVu24, 0xffc100, rotate=0)

    rectangle0 = M5Rect(71, 130, 260, 100, 0x000000, 0x000000)
    image0 = M5Img(14, 127, "res/m5.png", True)
    label0 = M5TextBox(130, 172, host_ip[0], lcd.FONT_UNICODE, 0xFFFFFF, rotate=0)


def NOTIFICATION_MODE_UPDATE_SCREEN():
    host_ip = list(nic.ifconfig())  # return a tuple json doesnt allow tuple
    # CONFIG SCREEN

    # SCREEN SIZE
    SCREEN_WIDTH = lcd.screensize()

    # width of the string
    string_width = lcd.textWidth(str(host_ip[0]))

    center_horizontal = int(SCREEN_WIDTH[0] / 2 - string_width / 2)

    font_height = tft.fontSize()
    tft.font(lcd.FONT_Default)  # set active font

    center_vertical = int(SCREEN_WIDTH[1] / 2 - font_height[1] / 2)
    label0 = M5TextBox(center_horizontal, 0, str(host_ip[0]), lcd.FONT_Default, 0xFFFFFF, rotate=0)

    #image0 = M5Img(95, 58, "res/config.png", True)
    #label0 = M5TextBox(125, 210, "LOADING...", lcd.FONT_Default, 0xFFFFFF, rotate=0)


# Keine Config , dann Pairing ;)

config_exists = LoadJsonFromFile()
if not config_exists:
    global LOADING
    global alive
    global FILE_REQUEST
    FILE_REQUEST = True  # STOPPING FILE_REQQUEST THREAD
    alive = True  # STOPPING PAIRING THREAD
    LOADING = True  # STOP ANIMATION THREAD

    pairing_animatiom = _thread.start_new_thread(ANIMATION_PAIRING, ())
    pairing = _thread.start_new_thread(UDP_PAIRING_REQUEST, (dhcp_hostname,mac_decoded,host_ip,))
    udp_server = _thread.start_new_thread(UDP_SERVER, (dhcp_hostname,mac_decoded,host_ip,))
else:
    sys.path.insert(1, '/flash/eventghost')
    import server
    # TCP SERVER START HERE