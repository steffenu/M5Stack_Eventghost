
from m5stack import *
from m5ui import *
from uiflow import *

from m5stack import lcd

import time
import _thread

tft = lcd

# GLOBAL VARIABLE
lock = _thread.allocate_lock()


def EVENT_CARD(data):
    """

    :param title:
    :param message:
    :param icon:
    :param event:                   0 , 1 , 2 = event , finsehed , running
    :param event_duration:          time it takes to change from red to green image

    :param available_width:         207 width of text box
    :param message_start_position   start x , y coordinates ,  [107, 74, XX, XX]
    :param row_limit:
    :param line_height:
    :param padding:                 207 - padding
    :return:
    """

    #

    # 320 - 107
    # 107, 114, 320, 160
    # = 213

    try:
        print(data)
        global lock
        with lock:
            #lock.acquire()
            TEXT_CLEAR_SCREEN()

            # title, message, icon, event, event_duration
            # image0 = M5Img(147, 203, "res/event_red.png", True)

            # available_width = box_dimensions[2] - box_dimensions[0]
            available_width = 280  # Widht of text box
            message_start_position = [17, 118]
            line_height = 30
            padding = 0

            # ==== CARD BACKGROUND ==== #
            #rectangle0 = M5Rect(0, 40, 320, 160, 0x000000, 0x000000)
            rectangle0 = M5Rect(0, 20, 320, 200, 0x000000, 0x000000)

            # ==== TITLE ==== #
            truncated_title = TRUNCATE(data['title'], 180, 20) # 180 = available with set manually
            title_label = M5TextBox(17, 54, truncated_title, lcd.FONT_DejaVu24, 0xffb300, rotate=0)

            # ==== URHZEIT ==== #
            #label1 = M5TextBox(141, 185, "3:31 pm", lcd.FONT_Default, 0xffb300, rotate=0)

            # ==== IMAGE ==== #
            print("image loaded",data['image'])
            tft.image(258, 38, "res/" + data['image']) # incoming data is a list


            # ==== TEXT OUTPUT ==== #
            tft.font(lcd.FONT_DejaVu18, rotate=0, color=0xffb300) # set active font
            newline_list = TEXT_LINE_CREATOR(data['message'], available_width, 2, padding)
            #label4 = M5TextBox(0, 0, str(newline_list), lcd.FONT_Default, 0xFFFFFF)
            TEXT_NEWLINE_OUTPUT(newline_list, message_start_position, line_height)
            print("event mode",data['event'])
            if data['event'] == "default":
                _thread.start_new_thread(EVENT_DURATION, (data['event_duration'],title_label))

                for x in range(data['event_duration']):
                    time.sleep(1)
                #EVENT_DURATION(event_duration , title_label)
            else:
                pass

    except Exception as e:
        ERROR_MESSAGE(e,"Event Card")


# ======================================================================== #

def LIST(data):
    """
    :param data['message']:
    [
    text1 ,
    text2 ,
    text3
    ]

    :param data['title']:
    title


    :param colors:
    [
    0x3f3f3f , 0x333333 , 0xababab
    0x000000 ,
    0xffd52b ,  0x3f3f3f ,
    0x3f3f3f , 0x9f9f9f
    ]

    [
    main_rectangle , , main_text ,  main_circle
    li_rectangle ,
    li_label_selected ,  li_circle_selected ,
    li_label ,li_circle
    ]

    """

    """ 3 THEMES AVAILABLE IN EVENTGHOST TO SELECT

    """

    default = \
        [
            0x3f3f3f ,  0xababab ,0x333333 ,
            0x000000 ,
            0xffd52b ,  0x3f3f3f ,
            0x333333 , 0xababab
        ]

    red = \
        [
            0x960000 ,  0xd4d4d4, 0xab2424 ,
            0x000000 ,
            0xffd52b ,  0x3f3f3f ,
            0xab2424 , 0x9f9f9f
        ]

    green = \
        [
            0x01560e ,  0xd4d4d4, 0x007211 ,
            0x000000 ,
            0xffd52b ,  0x01560e ,
            0x007211, 0x9f9f9f
        ]

    colors = []
    if data['event'] == 'default': colors = default;
    if data['event'] == 'finished': colors = green;
    if data['event'] == 'failure': colors = red;
    print(data)
    try:

        global lock
        with lock:
            TEXT_CLEAR_SCREEN()

            setScreenColor(0x1111111)

            # ==== TITLE ==== #
            truncated_main_text = TRUNCATE(data['title'], 237, 20) # 180 = available with set manually

            main_rectangle = M5Rect(0, 10, 270, 50, colors[0], colors[0])
            main_text = M5TextBox(10, 30, truncated_main_text, lcd.FONT_DejaVu18, colors[1], rotate=0)
            main_circle = M5Circle(280, 35, 30, colors[2], colors[2])
            image = M5Img(256, 10, "res/" + str(data['image']), True)

            if data['message'][0] != "":
                # ==== TEXT ITEM 1 ==== #
                truncated_item_one = TRUNCATE(data['message'][0], 270, 20)

                li_rectangle_one = M5Rect(10, 86, 290, 35, colors[3], colors[3])
                li_circle_selected = M5Circle(299, 103, 15, colors[5], colors[5])
                li_label_selected = M5TextBox(20, 97, truncated_item_one, lcd.FONT_DejaVu18, colors[4], rotate=0)

            if data['message'][1] != "":
                # ==== TEXT ITEM 2 ==== #
                truncated_item_two = TRUNCATE(data['message'][1], 270, 20)

                li_rectangle_two = M5Rect(10, 136, 290, 35, colors[3], colors[3])
                li_circle_two = M5Circle(299, 153, 15, colors[7], colors[7])
                li_label_two = M5TextBox(20, 147, truncated_item_two, lcd.FONT_DejaVu18, colors[6], rotate=0)

            if data['message'][2] != "":
                # ==== TEXT ITEM 3 ==== #
                truncated_item_three = TRUNCATE(data['message'][2], 270, 20)

                li_rectangle_three = M5Rect(10, 186, 290, 35, colors[3], colors[3])
                li_circle_three = M5Circle(299, 203, 15, colors[7], colors[7])
                li_label_three = M5TextBox(20, 197, truncated_item_three, lcd.FONT_DejaVu18, colors[6], rotate=0)

    except Exception as e:
        ERROR_MESSAGE(e, "LIST")

def KEY_VALUE(data):
    """
    :param
    data = \
            {
                'mode': "KEY_VALUE", # named exactly after Eventghost folder important !
                'device': chosen_device , # ip & mac [192.168 , ff:ff:ff:]
                'title': [value2 , value5],
                'message': [value3, value6],
                'image': [value4, value7],
            }
    """

    try:
        print(data)
        global lock
        with lock:

            rectangle0 = M5Rect(0, 120, 320, 120, 0x000000, 0x000000)
            label0 = M5TextBox(25, 31, data['title'][0], lcd.FONT_DejaVu18, 0xffd801, rotate=0)
            label2 = M5TextBox(25, 62, data['message'][0], lcd.FONT_DejaVu40, 0xFFFFFF, rotate=0)
            image0 = M5Img(242, 31, "res/" + data['image'][0], True)

            label0 = M5TextBox(25, 146, data['title'][1], lcd.FONT_DejaVu18, 0xffd801, rotate=0)
            label2 = M5TextBox(25, 177, data['message'][1], lcd.FONT_DejaVu40, 0xFFFFFF, rotate=0)
            image0 = M5Img(242, 146, "res/" + data['image'][1], True)

    except Exception as e:
        ERROR_MESSAGE(e, "KEY_VALUE")

def SINGLE(data):
    setScreenColor(0x1111111)

    """
    :param
        data = \
            {
                'mode': "SINGLE", # named exactly after Eventghost folder important !
                'device': chosen_device, # ip & mac [192.168 , ff:ff:ff:]
                'message': value2,

                'font_size': value3,
                'color': value4,
                'capital': value5,
            }
    """
    print(data)
    try:

        global lock
        with lock:

            # SET COLOR
            color = None
            if data['color'] == 'normal': color = 0xababab; # white/grey
            if data['color'] == 'finished': color = 0x007211; # green
            if data['color'] == 'failure': color = 0xab2424; # red

            font = None
            # SET FONT SIZE
            if data['font_size'] == 'normal':
                tft.font(lcd.FONT_Default, rotate=0, color=color) # set active font
                font = lcd.FONT_Default

            if data['font_size'] == 'medium':
                tft.font(lcd.FONT_DejaVu18, rotate=0, color=color) # set active font
                font = lcd.FONT_DejaVu18

            if data['font_size'] == 'big':
                tft.font(lcd.FONT_DejaVu24, rotate=0, color=color) # set active font
                font = lcd.FONT_DejaVu24


            # SCREEN SIZE
            SCREEN_WIDTH  = lcd.screensize()

            message = data['message']
            if data['capital'] == 'capital': message = data['message'].upper() # uppercased capital

            # width of the string
            string_width = lcd.textWidth(message)

            center_horizontal = int(SCREEN_WIDTH[0]  / 2 -  string_width /2)

            font_height = tft.fontSize()

            center_vertical =  int(SCREEN_WIDTH[1]  / 2 -  font_height [1] /2)




            centered_text = M5TextBox(center_horizontal , center_vertical , message , font,color, rotate=0)

    except Exception as e:
        ERROR_MESSAGE(e, "SINGLE")

# CREATES list OF LINES .. correctly formatted for avaialbe space of a line
def TEXT_LINE_CREATOR(string, width_setting, row_limit, padding):
    """
    :param string:              "A LONG OR SHORT MESSAGE"
    :param width_setting:       213 - the available amount of pixel for a line
    :param row_limit:           2 - max row output
    :param padding:             20 - gets subtracted from width setting
    """
    string_list = string.split()
    #M5TextBox(0, 30, str(string_list), lcd.FONT_DejaVu18, 0xffb300, rotate=0)
    # label0 = M5TextBox(0, 0, str(string_list), lcd.FONT_DejaVu18, 0xffb300, rotate=0)
    # label0 = M5TextBox(0, 200, str(lcd.textWidth("This is a short messag")), lcd.FONT_Ubuntu, 0xffb300, rotate=0)
    # label0 = M5TextBox(107, 174, str("This is a short messag"), lcd.FONT_Ubuntu, 0xffb300, rotate=0)
    newline_list = []
    newline = ""
    list_lenght = len(string_list)

    # 1 Erstelle newlines bis row limit erreicht ist
    # 2 sofern row limit nicht erreicht ist gebe newlines aus
    # 3 sofern noch wörter übrig sind im newline string .. schaue ob noch platz ist
    for string in string_list:
        string_width = lcd.textWidth(string)
        newline_width = lcd.textWidth(newline)

        if len(newline_list) == row_limit: break;

        if (newline_width + string_width)  < width_setting - padding:
            # APPEND STRING
            newline +=  string + " "

        elif (newline_width + string_width) > width_setting - padding:
            # ADD NEWLINE TO LIST IF width_setting is overflow
            # RESET NEWLINE
            #
            newline_list.append(newline.rstrip())
            newline = ""
            newline += string + " " # NEUE ZEILE mit string der zuviel war

    if newline:
        #TEXT_LONG_STRING_SPLITTER(long_string, available_width)
        newline = TRUNCATE(newline , width_setting , 0)
        newline_list.append(newline.rstrip())


    while ("" in newline_list):
        newline_list.remove("")
    return newline_list


# uses formatted list of TEXT_LINE_CREATOR() to output list items  to screen at position
# with line height and right padding
def TEXT_NEWLINE_OUTPUT(newline_list, message_start_position, line_height):
    """
    :param newline_list:                ["Sample Text Line 1" , "Sample Text Line 2]
    :param message_start_position:      box_dimensions = [0, 40, 320, 160]
    :param line_height:                 30
    """

    start_x, start_y = message_start_position[0], message_start_position[1]
    # label0 = M5TextBox(0, 0, str(newline_list), lcd.FONT_DejaVu18, 0xffb300, rotate=0)
    for x in newline_list:
        label0 = M5TextBox(start_x, start_y, str(x), lcd.FONT_DejaVu18, 0xFFFFFF, rotate=0)
        start_y = start_y + line_height  # vertical space between rows

        # TRUNCATE(string)  # truncate last line  of row_limit if required ...


def TEXT_LONG_STRING_SPLITTER(long_string, available_width):
    tft.font(lcd.FONT_DejaVu18, rotate=0, color=0xffb300)  # setting the ACTIVE font for lcd.textWidth -.-

    splitted = long_string.split()

    mod_string = ""
    long_string_list = []

    for y in splitted:
        for x in range(len(y)):
            if lcd.textWidth(mod_string) <= available_width:
                mod_string = mod_string + y[x]
            else:
                long_string_list.append(mod_string)
                mod_string = ""

    #label0 = M5TextBox(0, 200, str(lcd.textWidth(long_string_list[0])), lcd.FONT_Ubuntu, 0xffb300, rotate=0)
    # label0 = M5TextBox(0, 0, str(long_string_list), lcd.FONT_Ubuntu, 0xffb300, rotate=0)
    return long_string_list


def TRUNCATE(string, available_width, padding):
    # WIERD FIX TO HAVE LCD.texwidht work correctly ....
    # setting the active font for lcd texwidth to work correctly

    tft.font(lcd.FONT_DejaVu18, rotate=0, color=0xffb300)
    title = ""

    for x in string:
        if lcd.textWidth(x + title) < available_width - padding:
            title = title + x
        elif lcd.textWidth(x + title) > available_width - padding:
            title = title + ".."
            return title
    return title


def CALCULATE_BOX_WIDTH(box_dimensions):
    # [107, 74, 320, 160] EXAMPLE box_width = 320 - 107
    box_width = box_dimensions[2] - box_dimensions[0]
    return box_width


def CALCULATE_AVAILABLE_WIDTH(newline_width, width_setting):
    available_width = width_setting - newline_width
    return available_width


def TEXT_GET_STRING_WIDTH(string):
    string_width = lcd.textWidth(string)
    return string_width


def TEXT_CLEAR_SCREEN():
    # Clear the screen with default background color or specific color if given.
    tft.clear()





def EVENT_DURATION(event_duration , title_text):
    """

    :param event:           True , False
    :param event_duration:  0-60secs
    :return:
    """


    # ==  UI SET TO RED COLOR == #
    title_text.setColor(0xff0101) # RED
    indicator = M5Circle(160, 219, 15, 0xff0101, 0xff0101)  # RED
    image_circle = M5Circle(280, 65, 27, 0xff0101, 0xff0101)  # RED
    image0 = M5Img(258, 38, "res/m_eg.png", True)
    toggle = True

    for x in range(event_duration):

        time.sleep(1)
        # BLINKING INDICATIOR Circle
        if toggle:
            indicator.hide()
        else:
            indicator.show()
        toggle = not toggle


        if event_duration - 1 == x:
            # ==  UI SET TO GREEN COLOR == #
            title_text.setColor(0x07ba00) # GREEN TITLE
            image_circle.setBgColor(0x07ba00) # GREEN
            image_circle.setBorderColor(0x07ba00) # GREEN

            indicator.setBgColor(0x07ba00) # GREEN
            indicator.setBorderColor(0x07ba00) # GREEN
            indicator.show()

            image0.show()


def ERROR_MESSAGE(e , func_name):

    label0 = M5TextBox(20, 10, str("Error in ") + str(func_name), lcd.FONT_Default, 0xFFFFFF, rotate=0)
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




"""
message_string = "This is a short mess which probably needs 1 or 2 newlines ... and truncation if its too long"
# list_string = {{"name":"John", "age": 18} , {"name":"Tim", "age": 26} , {"name":"Jack", "age": 33}}
no_spaces_string = "yikes xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx yikes xxxxxxxxxx"
brother_string = "today is a good day my brother have a free beer on the house brother"

EVENT_CARD("garage door opened again", brother_string, "logo.png", True, 7)

EVENT_CARD("BRUDI MUSS LOSS", no_spaces_string, "logo.png", True, 7)
"""




