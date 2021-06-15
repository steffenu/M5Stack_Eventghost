from m5stack import *
from m5ui import *
from uiflow import *

setScreenColor(0x222222)







import network
import wifiCfg
import socket
import json
import sys

#add folder to current path so you cna import it
# normally you can only import from same direcoty

sys.path.insert(1, '/flash/eventghost')
sys.path.insert(1, '/flash/apps')
from Core import NOTIFICATION_MODE_READY_SCREEN

import templates
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








# enable station interface and connect to WiFi access point
nic = network.WLAN(network.STA_IF)
nic.active(True)
model = GET_M5_MODEL()
dhcp_hostname = nic.config(dhcp_hostname=model) # changing default hostname to detected model
SSID, PASS = wifiCfg.deviceCfg.wifi_read_from_flash()
nic.connect(SSID, PASS)
while not nic.isconnected(): pass



def NOTIFICATION_SERVER():

    # device's IP address
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 7300  # TCP   = 7300 UDP = 7200
    # receive 4096 bytes each time
    BUFFER_SIZE = 4096
    SEPARATOR = "<SEPARATOR>"

    # create the server socket
    s = socket.socket()

    # bind the socket to our local address
    s.bind((SERVER_HOST, SERVER_PORT))


    s.listen(1) # only connection - handle conn overflow in Eventghost
    print(" Listening as", SERVER_HOST , SERVER_PORT)



    while True:
        # Wait for a connection
        print('waiting for a connection')
        connection, client_address = s.accept()
        #label4 = M5TextBox(0, 0, str("CONNECTED"), lcd.FONT_Default, 0xFFFFFF)


        try:

            while True:
                data = connection.recv(BUFFER_SIZE).decode('utf-8')



                if data:
                    # NOTIFICATION_EVENT_CARD(title, message, icon, event, event_duration)

                    """
                    mode                event_card,multiline_message, image_mode....
                    msg                 main text message
                    title               ...
                    event               True / False
                    event_duration      Dauer Wechsel image_red zu image green 0-60s
                    screen_color
                    sd_card_images      ["image1", "image2"] - if default icons are swapped
                    """

                    # BILDSCHIRM CLEAREN
                    templates.TEXT_CLEAR_SCREEN()

                    data = json.loads(data)
                    #label4 = M5TextBox(0, 0, str(data), lcd.FONT_Default, 0xFFFFFF)

                    # ======== EVENT_CARD  ======== #
                    # NOTIFICATION_EVENT_CARD(title, message, icon, event, event_duration)
                    """
                        mode': "event_card",
                        'device': chosen_device , # ip & mac [192.168 , ff:ff:ff:]
                        'title': value2,
                        'message': value3,
                        'event': value4,   # default , finshed , runniing
                        'event_duration': 3,
                        'image': [image1 , image 2],
                    """
                    if data['mode'] == "EVENT_CARD":
                        #templates.EVENT_CARD(data['title'], data['message'], data['image'], data['event'], data['event_duration'])
                        templates.EVENT_CARD(data)

                    # ======== LIST  ======== #
                    if data['mode'] == "LIST":
                        templates.LIST(data)

                    # ======== MULTILINE_MESSAGE  ======== #
                    if data['mode'] == "MULTILINE":
                        pass

                    # ======== KEY_VALUE ======== #
                    if data['mode'] == "KEY_VALUE":
                        templates.KEY_VALUE(data)

                    # ======== IMAGE  ======== #
                    if data['mode'] == "IMAGE":
                        pass
                    # ======== SINGLE  ======== #
                    if data['mode'] == "SINGLE":
                        templates.SINGLE(data)

                    # --------------------------
                    #           UTILITY
                    # --------------------------

                    # ======== STANDBY ======== #
                    if data['mode'] == "STANDBY":

                        pass

                else:
                    break
        except Exception as e:

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
            label13 = M5TextBox(0, 100, str(data), lcd.FONT_Default, 0xFFFFFF, rotate=0)

        finally:
            connection.close() # Always clean up the connection
NOTIFICATION_SERVER()




