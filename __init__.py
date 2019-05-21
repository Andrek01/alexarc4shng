#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
#  Copyright 2019 AndreK                    andre.kohler01@googlemail.com
#########################################################################
#  This file is part of SmartHomeNG.   
#
#  Sample plugin for new plugins to run with SmartHomeNG version 1.4 and
#  upwards.
#
#  SmartHomeNG is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SmartHomeNG is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHomeNG. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from lib.module import Modules
from lib.model.smartplugin import *
from lib.item import Items
from datetime import datetime


from io import BytesIO
import pycurl
from subprocess import Popen, PIPE
import json
import sys
import os
import re
import urllib3
import time
import base64







class shngObjects(object):
    def __init__(self):
        self.Devices = {}

    def exists(self, id):
        return id in self.Devices

    def get(self, id):
        return self.Devices[id]

    def put(self, newID):
        self.Devices[newID] = Device()

    def all(self):
        return list( self.Devices.values() )

class Device(object):
    def __init__(self):
        self.Commands=[]

class Cmd(object):
    def __init__(self, id):
        self.id = id
        self.command = ''
        self.ItemValue = ''
        self.EndPoint = ''
        self.Action = ''
        self.Value = ''


##############################################################################
class EchoDevices(object):
    def __init__(self):
        self.devices = {}

    def exists(self, id):
        return id in self.devices

    def get(self, id):
        return self.devices[id]

    def put(self, device):
        self.devices[device.id] = device

    def all(self):
        return list( self.devices.values() )

class Echo(object):
    def __init__(self, id):
        self.id = id
        self.name = ""
        self.serialNumber = ""
        self.family = ""
        self.deviceType = ""
        self.deviceOwnerCustomerId = ""
        self.playerinfo = {}
        self.queueinfo = {}

##############################################################################

class alexarc4shng(SmartPlugin):
    PLUGIN_VERSION = '1.0.0'
    ALLOW_MULTIINSTANCE = False
    """
    Main class of the Plugin. Does all plugin specific stuff and provides
    the update functions for the items
    """

    PLUGIN_VERSION = '1.0.1'

    def __init__(self, sh, *args, **kwargs):
        # get Instances
        self.logger = logging.getLogger(__name__)
        self.sh = self.get_sh()
        self.items = Items.get_instance()
        self.shngObjects = shngObjects()
        
        # Init values
        self.header = ''
        self.csrf = 'N/A'
        self.postfields=''
        self.login_state = False
        self.last_update_time = ''
        self.next_update_time = ''
        # get parameters
        self.cookiefile = self.get_parameter_value('cookiefile')
        self.host = self.get_parameter_value('host')
        self.AlexaEnableItem = self.get_parameter_value('item_2_enable_alexa_rc')
        self.credentials = self.get_parameter_value('alexa_credentials').encode('utf-8')
        self.credentials = base64.decodebytes(self.credentials).decode('utf-8')
        self.LoginUpdateCycle = self.get_parameter_value('login_update_cycle')
        self.update_file=self.sh.get_basedir()+"/plugins/alexarc4shng/lastlogin.txt"
        

        if not self.init_webinterface():
            self._init_complete = False
        
        return

    def run(self):
        """
        Run method for the plugin
        """
        self.logger.info("Plugin '{}': start method called".format(self.get_fullname()))
        # get additional parameters from files
        self.csrf = self.parse_cookie_file(self.cookiefile)
        
        # Check login-state - if logged off and credentials are availabel login in
        if os.path.isfile(self.cookiefile):
            self.login_state=self.check_login_state()
            self.check_refresh_login()
        
        if (self.login_state == False and self.credentials != ''):
            try:
                os.remove(self.update_file)
            except:
                pass
            self.check_refresh_login()
            self.login_state=self.check_login_state()
        
        # Collect all devices    
        if (self.login_state):
            self.Echos = self.get_devices_by_curl()
        else:
            self.Echos = None
        # enable scheduler if Login should be updated automatically
        
        if self.credentials != '':
            self.scheduler_add('check_login', self.check_refresh_login,cycle=300)
            #self.scheduler.add('plugins.alexarc4shng.check_login', self.check_refresh_login,cycle=300,from_smartplugin=True)
        self.alive = True
        
        # if you want to create child threads, do not make them daemon = True!
        # They will not shutdown properly. (It's a python bug)

    def stop(self):
        """
        Stop method for the plugin
        """
        self.logger.debug("Plugin '{}': stop method called".format(self.get_fullname()))
        self.scheduler_remove('alexarc4shng.check_login')
        self.alive = False

    def parse_item(self, item):
        """
        Default plugin parse_item method. Is called when the plugin is initialized.
        The plugin can, corresponding to its attribute keywords, decide what to do with
        the item in future, like adding it to an internal array for future reference
        :param item:    The item to process.
        :return:        If the plugin needs to be informed of an items change you should return a call back function
                        like the function update_item down below. An example when this is needed is the knx plugin
                        where parse_item returns the update_item function when the attribute knx_send is found.
                        This means that when the items value is about to be updated, the call back function is called
                        with the item, caller, source and dest as arguments and in case of the knx plugin the value
                        can be sent to the knx with a knx write function within the knx plugin.
        """
        
        itemFound=False
        i=1
        
        myValue = 'alexa_cmd_{}'.format( '%0.2d' %(i))
        while myValue in item.conf:
            

            self.logger.debug("Plugin '{}': parse item: {} Command {}".format(self.get_fullname(), item,myValue))
            
            CmdItem_ID = item._name
            try:
                myCommand = item.conf[myValue].split(":")
                 
                
                if not self.shngObjects.exists(CmdItem_ID):
                    self.shngObjects.put(CmdItem_ID)
                
                actDevice = self.shngObjects.get(CmdItem_ID)
                actDevice.Commands.append(Cmd(myValue))
                
                actCommand = len(actDevice.Commands)-1
                
                actDevice.Commands[actCommand].command = item.conf[myValue]
                myCommand = actDevice.Commands[actCommand].command.split(":")
                self.logger.info("Plugin '{}': parse item: {}".format(self.get_fullname(), item.conf[myValue]))
                
                actDevice.Commands[actCommand].ItemValue = myCommand[0]
                actDevice.Commands[actCommand].EndPoint = myCommand[1]
                actDevice.Commands[actCommand].Action = myCommand[2]
                actDevice.Commands[actCommand].Value = myCommand[3]
                itemFound=True
                
            except Exception as err:
                print("Error:" ,err)
            i += 1
            myValue = 'alexa_cmd_{}'.format( '%0.2d' %(i))
            
        # todo
        # if interesting item for sending values:
        #   return update_item
        if itemFound == True:
            return self.update_item
        else:
            return None
    
    def parse_logic(self, logic):
        """
        Default plugin parse_logic method
        """
        if 'xxx' in logic.conf:
            # self.function(logic['name'])
            pass

    def update_item(self, item, caller=None, source=None, dest=None):
        """
        Write items values
        :param item: item to be updated towards the plugin
        :param caller: if given it represents the callers name
        :param source: if given it represents the source
        :param dest: if given it represents the dest
        """
        # todo 
        # change 'foo_itemtag' into your attribute name
        
        # Item was not changed but double triggered the Upate_Item-Function
        if (self.AlexaEnableItem != ""):
            AlexaEnabledItem = self.items.return_item(self.AlexaEnableItem) 
            if AlexaEnabledItem() != True:
                return
        
        if item._type == "str":
            newValue=str(item())
            oldValue=str(item.prev_value())
        elif item._type =="num":
            newValue=float(item())
            oldValue=float(item.prev_value())
        else:
            newValue=str(item())
            oldValue=str(item.prev_value())
        
        # Nur bei Wertänderung, sonst nix wie raus hier
        if(oldValue == newValue):
            return         
        
        
        try:
            myEchos = self.sh.alexarc4shng.Echos.all()
            
        except Exception as err:
            self.logger.debug("Error while getting Echos :",err)
        # End Test
        

        
        CmdItem_ID = item._name
        
    
        if self.shngObjects.exists(CmdItem_ID):
            self.logger.debug("Plugin '{}': update_item ws called with item '{}' from caller '{}', source '{}' and dest '{}'".format(self.get_fullname(), item, caller, source, dest))
            
            actDevice = self.shngObjects.get(CmdItem_ID)
            
            for myCommand in actDevice.Commands:
                
                newValue2Set = myCommand.Value
                myItemBuffer = myCommand.ItemValue
                # Spezialfall auf bigger / smaller
                if myCommand.ItemValue.find("<=") >=0:
                    actValue = "<="
                    myCompValue = myCommand.ItemValue.replace("<="," ")
                    myCompValue = myCompValue.replace(".",",")
                    myCompValue = float(myCompValue)
                    myCommand.ItemValue = actValue                    
                    if  newValue > myCompValue:
                        return
                elif myCommand.ItemValue.find(">=") >=0:
                    actValue = ">="
                    myCompValue = myCommand.ItemValue.replace(">="," ")
                    myCompValue = myCompValue.replace(".",",")
                    myCompValue = float(myCompValue)
                    myCommand.ItemValue = actValue        
                    if newValue < myCompValue:
                        return
                elif myCommand.ItemValue.find("=") >=0 :
                    actValue = "="
                    myCompValue = myCommand.ItemValue.replace("="," ")
                    myCompValue = myCompValue.replace(".",",")
                    myCompValue = float(myCompValue)
                    myCommand.ItemValue = actValue                    
                    if newValue != myCompValue:
                        return
                elif myCommand.ItemValue.find("<") >=0:
                    actValue = "<"
                    myCompValue = myCommand.ItemValue.replace("<"," ")
                    myCompValue = myCompValue.replace(".",",")
                    myCompValue = float(myCompValue)
                    myCommand.ItemValue = actValue
                    if newValue >= myCompValue :
                        return
                elif myCommand.ItemValue.find(">") >=0:
                    actValue = ">"
                    myCompValue = myCommand.ItemValue.replace(">"," ")
                    myCompValue = myCompValue.replace(".",",")
                    myCompValue = float(myCompValue)
                    myCommand.ItemValue = actValue
                    if  newValue <= myCompValue:
                        return
                else:
                    actValue = str(item())
                    
                if ("volume" in myCommand.Action.lower()):
                    httpStatus, myPlayerInfo = self.receive_info_by_curl(myCommand.EndPoint,"LoadPlayerInfo","")
                    # Store Player-Infos to Device
                    if httpStatus == 200:
                        try:
                            myActEcho = self.Echos.get(myCommand.EndPoint)
                            myActEcho.playerinfo = myPlayerInfo['playerInfo']
                            actVolume = self.search(myPlayerInfo, "volume")
                            actVolume = self.search(actVolume, "volume")
                        except:
                            actVolume = 50
                    else:
                        try:
                            actVolume = int(item())
                        except:
                            actVolume = 50
                        
                if ("volumeadj" in myCommand.Action.lower()):
                    myDelta = int(myCommand.Value)
                    if actVolume+myDelta < 0:
                        newValue2Set = 0
                    elif actVolume+myDelta > 100:
                        newValue2Set = 100
                    else:
                        newValue2Set =actVolume+myDelta
                
                # neuen Wert speichern in item
                if ("volume" in myCommand.Action.lower()):
                    item._value = newValue2Set
                    

                if (actValue == str(myCommand.ItemValue) and myCommand):
                    myCommand.ItemValue = myItemBuffer
                    self.send_cmd_by_curl(myCommand.EndPoint,myCommand.Action,newValue2Set)

    
    
    # find Value for Key in Json-structure
    # needed for Alexa Payload V3
    
    def search(self,p, strsearch):
        if type(p) is dict:  
            if strsearch in p:
                tokenvalue = p[strsearch]
                if not tokenvalue is None:
                 return tokenvalue
            else:
                for i in p:
                    tokenvalue = self.search(p[i], strsearch)  
                    if not tokenvalue is None:
                        return tokenvalue
    
    # Check if update of login is needed
    def check_refresh_login(self):
        my_file= self.update_file
        try:
            with open (my_file, 'r') as fp:
                for line in fp:
                    last_update_time = float(line)
            fp.close()
        except:
            last_update_time = 0
        
        mytime = time.time()
        if (last_update_time + self.LoginUpdateCycle < mytime):
            self.log_off()
            self.auto_login()
            
            if not self.login_state:
                mytime = 0
            
            file=open(my_file,"w")
            file.write(str(mytime)+"\r\n")
            file.close()
            
            # set actual values for web-interface
            self.last_update_time = datetime.fromtimestamp(mytime).strftime('%Y-%m-%d %H:%M:%S')
            self.next_update_time = datetime.fromtimestamp(mytime+self.LoginUpdateCycle).strftime('%Y-%m-%d %H:%M:%S')
            self.logger.info('refreshed Login/Cookie: %s' % self.last_update_time)
        else:
            self.last_update_time = datetime.fromtimestamp(last_update_time).strftime('%Y-%m-%d %H:%M:%S')
            self.next_update_time = datetime.fromtimestamp(last_update_time+self.LoginUpdateCycle).strftime('%Y-%m-%d %H:%M:%S')
        
        
    
    
    def replace_mutated_vowel(self,mValue):
        # prüfen auf Sonderzeichen
        search =  ["ä" , "ö" , "ü" , "ß" , "Ä" , "Ö", "Ü",  "&"  , "é", "á", "ó"]
        replace = ["ae", "oe", "ue", "ss", "Ae", "Oe","Ue", "und", "e", "a", "o"]

        counter = 0
        myNewValue = mValue
        try:
            for Replacement in search:
                myNewValue = myNewValue.replace(search[counter],replace[counter])
                counter +=1
        except:
            pass
            
        return myNewValue
        # Ende der Prüfung

    
        # PLEASE CHECK CODE HERE. The following was in the old skeleton.py and seems not to be 
        # valid any more 
        # # todo here: change 'plugin' to the plugin name
        # if caller != 'plugiSmartPluginn':
        #    logger.info("update item: {0}".format(item.id()))
    
    ##############################################
    # Help -Start Functions by pycurl
    ##############################################
    
    
    def check_login_state(self):
        myUrl='https://'+self.host+'/api/bootstrap?version=0'
        myHeader = ['DNT: 1',
                    'Connection :keep-alive',
                    'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0'
                   ]
        try:
            buffer = BytesIO()
            myCurl = pycurl.Curl()
            myCurl.setopt(myCurl.URL,myUrl)
            myCurl.setopt(pycurl.FOLLOWLOCATION, 1)
            myCurl.setopt(pycurl.COOKIEJAR ,self.cookiefile)
            myCurl.setopt(pycurl.COOKIEFILE ,self.cookiefile)
            myCurl.setopt(pycurl.ENCODING, "gzip, deflate");
            myCurl.setopt(pycurl.USERAGENT , "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0" )
            myCurl.setopt(pycurl.HEADER,1)
            myCurl.setopt(pycurl.WRITEDATA , buffer)
            myCurl.setopt(pycurl.HTTPGET,1)
            myCurl.perform()
            
            self.logger.info('Status of check_login_state: %d' % myCurl.getinfo(myCurl.RESPONSE_CODE))
            
            header_size = myCurl.getinfo(pycurl.HEADER_SIZE)
            
            myCurl.close()
            
            body=buffer.getvalue()
            headers=body[0:header_size]
            content = body[header_size:len(body)]
            
            mybody = content.decode()
            headers = headers.decode()
            myDict=json.loads(mybody)
            myAuth =myDict['authentication']['authenticated']
            if (myAuth == True):
                self.logger.info('Login-State checked - Result: Logged ON' )
                return True
            else:
                self.logger.info('Login-State checked - Result: Logged OFF' )
                return False
            
            
          
            
        except Exception as err:
            self.logger.error('Error while checking login state: %s' %err)
            return False
    
    def receive_info_by_curl(self,dvName,cmdName,mValue):
        buffer = BytesIO()
        actEcho = self.Echos.get(dvName)
        myUrl='https://'+self.host
        myDescriptions = ''
        myDict = {}
        
        
        myDescription,myUrl,myDict = self.load_command_let(cmdName,None)
        # complete the URL
        myUrl='https://'+self.host+myUrl
        # replace the placeholders in URL
        myUrl=self.parse_url(myUrl,
                            mValue,
                            actEcho.serialNumber,
                            actEcho.family,
                            actEcho.deviceType,
                            actEcho.deviceOwnerCustomerId)
        
        # replace the placeholders in Payload
        #myheaders=self.create_curl_header()
        myheaders=["Host: alexa.amazon.de",
                   "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0",
                   "Connection: keep-alive",
                   "Content-Type: application/json; charset=UTF-8",
                   "Accept-Language: en-US,en;q=0.5",
                   "Referer: https://alexa.amazon.de/spa/index.html",
                   "Origin: https://alexa.amazon.de",
                   "DNT: 1"
                  ] 
    
        myCurl = pycurl.Curl()
        myCurl.setopt(myCurl.URL,myUrl)
        myCurl.setopt(pycurl.HTTPHEADER, myheaders)
        myCurl.setopt(pycurl.FOLLOWLOCATION, 1)
        myCurl.setopt(pycurl.COOKIEJAR ,self.cookiefile)
        myCurl.setopt(pycurl.COOKIEFILE ,self.cookiefile)
        myCurl.setopt(pycurl.WRITEDATA , buffer)
        myCurl.setopt(pycurl.HTTPGET,1)
        myCurl.perform()
        myResult = myCurl.getinfo(myCurl.RESPONSE_CODE)
        myCurl.close()
        try:
            body=buffer.getvalue()
            mybody = body.decode()
            myDict=json.loads(mybody)
        except Exception as err:
            self.logger.debug("Error while getting Player-Infos",err)
        
        self.logger.info('Status of receive_info_by_curl: %d' % myResult)
        
        return myResult,myDict
    
    def send_cmd_by_curl(self,dvName, cmdName,mValue,path=None):
        # Parse the value field for dynamic content
        if (str(mValue).find("#") >= 0 and str(mValue).find("/#") >0):
            FirstPos = str(mValue).find("#")
            LastPos = str(mValue).find("/#",FirstPos)
            myItemName = str(mValue)[FirstPos+1:LastPos]
            myItem=self.items.return_item(myItemName)
            #myItem=self.sh.return_item(myItemName)
            
            if myItem._type == "num":
                myValue = str(myItem())
                myValue = myValue.replace(".", ",")
            elif myitem._type == "bool":
                myValue = str(myItem())
            else:
                myValue = str(myItem())
            mValue = mValue[0:FirstPos]+myValue+mValue[LastPos:LastPos-2]+mValue[LastPos+2:len(mValue)]

        mValue = self.replace_mutated_vowel(mValue)
                
        
        buffer = BytesIO()
        actEcho = self.Echos.get(dvName)
        myUrl='https://'+self.host
        myDescriptions = ''
        myDict = {}
        
        
        myDescription,myUrl,myDict = self.load_command_let(cmdName,path)
        # complete the URL
        myUrl='https://'+self.host+myUrl
        # replace the placeholders in URL
        myUrl=self.parse_url(myUrl,
                            mValue,
                            actEcho.serialNumber,
                            actEcho.family,
                            actEcho.deviceType,
                            actEcho.deviceOwnerCustomerId)
        
        # replace the placeholders in Payload
        myheaders=self.create_curl_header() 
        postfields = self.parse_json_2_curl(myDict,
                                         mValue,
                                         actEcho.serialNumber,
                                         actEcho.family,
                                         actEcho.deviceType,
                                         actEcho.deviceOwnerCustomerId)
        
        
        
        myCurl = pycurl.Curl()
        myCurl.setopt(myCurl.URL,myUrl)
        myCurl.setopt(pycurl.HTTPHEADER, myheaders)
        myCurl.setopt(pycurl.FOLLOWLOCATION, 1)
        myCurl.setopt(pycurl.COOKIEJAR ,self.cookiefile)
        myCurl.setopt(pycurl.COOKIEFILE ,self.cookiefile)
        myCurl.setopt(pycurl.POST,1)
        try:
            if len(postfields) > 20:
                myCurl.setopt(pycurl.POSTFIELDS,postfields)
        except Exception as err:
            self.logger.info('Got Error by adding PostFields',err)
        myCurl.perform()
        self.logger.info('Status of send_cmd_by_curl: %d' % myCurl.getinfo(myCurl.RESPONSE_CODE))
        myResult = myCurl.getinfo(myCurl.RESPONSE_CODE)
        myCurl.close()
        
        return myResult 
        

    
    def get_devices_by_curl(self):
        try:
            buffer = BytesIO()
            myCurl = pycurl.Curl()
            myCurl.setopt(myCurl.URL,'https://alexa.amazon.de/api/devices-v2/device?cached=false')
            myCurl.setopt(pycurl.FOLLOWLOCATION, 1)
            myCurl.setopt(pycurl.COOKIEJAR ,self.cookiefile)
            myCurl.setopt(pycurl.COOKIEFILE ,self.cookiefile)
            myCurl.setopt(pycurl.WRITEDATA , buffer)
            myCurl.setopt(pycurl.HTTPGET,1)
            myCurl.perform()
            self.logger.info('Status of get_devices_by_curl: %d' % myCurl.getinfo(myCurl.RESPONSE_CODE))
            myCurl.close()
            
            body=buffer.getvalue()
            mybody = body.decode()
            myDict=json.loads(mybody)
            myDevices = EchoDevices()
            
            
        except Exception as err:
            self.logger.error('Error while getting Devices: %s' %err)
            return None
        
        for device in myDict['devices']:
            deviceFamily=device['deviceFamily']
            if deviceFamily == 'WHA' or deviceFamily == 'VOX' or deviceFamily == 'FIRE_TV' or deviceFamily == 'TABLET':
                continue
            try:
                actName = device['accountName']
                myDevices.put(Echo(actName))
        
                actDevice = myDevices.get(actName)
                actDevice.serialNumber=device['serialNumber']
                actDevice.deviceType=device['deviceType']
                actDevice.family=device['deviceFamily']
                actDevice.name=device['accountName']
                actDevice.deviceOwnerCustomerId=device['deviceOwnerCustomerId']
            except Exception as err:
                self.logger.debug('Error while getting Devices: %s' %err)
                myDevices = None
                
        return myDevices
    
    def parse_cookie_file(self,cookiefile):
        csrf = 'N/A'
        try:
            with open (cookiefile, 'r') as fp:
                for line in fp:
                    if line.find('amazon.de')<0:
                            continue
                    if not re.match(r'^\#', line):
                        lineFields = line.strip().split('\t')
                        if len(lineFields) >= 7:
                            if lineFields[5] == 'csrf' and lineFields[0].find("amazon") >= 0:
                                csrf = lineFields[6]
            fp.close()
        except Exception as err:
            self.logger.debug('Cookiefile could not be opened %s' % cookiefile)
        
        return csrf
    
    
    def parse_url(self,myDummy,mValue,serialNumber,familiy,deviceType,deviceOwnerCustomerId):
        
        myDummy = myDummy.strip()
        myDummy=myDummy.replace(' ','')
        # for String
        try:
            myDummy=myDummy.replace('<mValue>',mValue)
        except Exception as err:
            print("no String")
        # for Numbers
        try:    
            myDummy=myDummy.replace('"<nValue>"',mValue)
        except Exception as err:
            print("no Integer")
            
        # Inject the Device informations
        myDummy=myDummy.replace('<serialNumber>',serialNumber)
        myDummy=myDummy.replace('<familiy>',familiy)
        myDummy=myDummy.replace('<deviceType>',deviceType)
        myDummy=myDummy.replace('<deviceOwnerCustomerId>',deviceOwnerCustomerId)
        
        return myDummy

    def parse_json_2_curl(self,myDict,mValue,serialNumber,familiy,deviceType,deviceOwnerCustomerId):

        myDummy = json.dumps(myDict, sort_keys=True)
       
        count = 0
        for char in myDummy:
          if char == '{':
            count = count + 1
         
        
        if count > 1:
            # Find First Pos for inner Object
            FirstPos = myDummy.find("{",1)
             
            # Find last Pos for inner Object
            LastPos = 0
            pos1 = 1
            while pos1 > 0:
                pos1 = myDummy.find("}",LastPos+1)
                if (pos1 >= 0):
                    correctPos = LastPos
                    LastPos = pos1
            LastPos = correctPos
        
        
            innerJson = myDummy[FirstPos+1:LastPos]
            innerJson = innerJson.replace('"','\\"')
    
            myDummy = myDummy[0:FirstPos]+'"{'+innerJson+'}"'+myDummy[LastPos+1:myDummy.__len__()]
        
            
        myDummy = myDummy.strip()
        myDummy=myDummy.replace(' ','')
        # for String
        try:
            myDummy=myDummy.replace('<mValue>',mValue)
        except Exception as err:
            print("no String")
        # for Numbers
        try:    
            myDummy=myDummy.replace('"<nValue>"',str(mValue))
        except Exception as err:
            print("no Integer")
        
        # Inject the Device informations
        myDummy=myDummy.replace('<serialNumber>',serialNumber)
        myDummy=myDummy.replace('<familiy>',familiy)
        myDummy=myDummy.replace('<deviceType>',deviceType)
        myDummy=myDummy.replace('<deviceOwnerCustomerId>',deviceOwnerCustomerId)
        
        return myDummy
    
    def create_curl_header(self):
        myheaders=["Host: alexa.amazon.de",
                    "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:60.0) Gecko/20100101 Firefox/60.0",
                    "Accept: */*",
                    "Accept-Encoding: deflate, gzip",
                    "DNT: 1",
                    "Connection: keep-alive",
                    "Content-Type: application/json; charset=UTF-8",
                    "Accept-Language: de,nl-BE;q=0.8,en-US;q=0.5,en;q=0.3",
                    "Referer: https://alexa.amazon.de/spa/index.html",
                    "Origin: https://alexa.amazon.de",
                    "csrf: "+ self.csrf,
                    "Cache-Control: no-cache"
                  ]
        return myheaders
    
    def load_command_let(self,cmdName,path=None):
        myDescription   = ''
        myUrl           = ''
        myJson          = ''
        retJson         = {}
        
        if path==None:
            path=self.sh.get_basedir()+"/plugins/alexarc4shng/cmd/"
            
        try:
            file=open(path+cmdName+'.cmd','r')
            for line in file:
                line=line.replace("\r\n","")
                line=line.replace("\n","")
                myFields=line.split("|")
                if (myFields[0]=="apiurl"):
                    myUrl=myFields[1]
                    pass
                if (myFields[0]=="description"):
                    myDescription=myFields[1]
                    pass
                if (myFields[0]=="json"):
                    myJson=myFields[1]
                    retJson=json.loads(myJson)
                    pass
            file.close()
        except:
            self.logger.error("Error while loading Commandlet : {}".format(cmdName))
        return myDescription,myUrl,retJson
    

    
    def load_cmd_list(self):
        retValue=[]
        
        files = os.listdir(self.sh.get_basedir()+'/plugins/alexarc4shng/cmd/')
        for line in files:
            try:
                line=line.split(".")
                if line[1] == "cmd":
                    newCmd = {'Name':line[0]}
                    retValue.append(newCmd)
            except:
                pass
        
        return json.dumps(retValue)

    def check_json(self,payload):
        try:
            myDump = json.loads(payload)
            return 'Json OK'
        except Exception as err:
            return 'Json - Not OK - '+ err.args[0]
        
    def delete_cmd_let(self,name):
        result = ""
        try:
            os.remove(self.sh.get_basedir()+"/plugins/alexarc4shng/cmd/"+name+'.cmd')
            result =  "Status:OK\n"
            result += "value1:File deleted\n"
        except Exception as err:
            result =  "Status:failure\n"
            result += "value1:Error - "+err.args[1]+"\n"
        
        ##################
        # prepare Response
        ##################
        myResult = result.splitlines()
        myResponse=[]
        newEntry=dict()
        for line in myResult:
            myFields=line.split(":")
            newEntry[myFields[0]] = myFields[1]

        myResponse.append(newEntry)        
        ##################
        return json.dumps(myResponse,sort_keys=True)
    
    def test_cmd_let(self,selectedDevice,txtValue,txtDescription,txt_payload,txtApiUrl):
        result = ""
        if (txtApiUrl[0:1] != "/"):
            txtApiUrl = "/"+txtApiUrl
            
        JsonResult = self.check_json(txt_payload)
        if (JsonResult != 'Json OK'):
            result =  "Status:failure\n"
            result += "value1:"+JsonResult+"\n"
        else:
            try:
                self.save_cmd_let("test", txtDescription, txt_payload, txtApiUrl, "/tmp/")
                retVal = self.send_cmd_by_curl(selectedDevice,"test",txtValue,"/tmp/")
                result =  "Status:OK\n"
                result += "value1: HTTP "+str(retVal)+"\n"
            except Exception as err:
                result =  "Status:failure\n"
                result += "value1:"+err.args[0]+"\n"
                
        ##################
        # prepare Response
        ##################
        myResult = result.splitlines()
        myResponse=[]
        newEntry=dict()
        for line in myResult:
            myFields=line.split(":")
            newEntry[myFields[0]] = myFields[1]

        myResponse.append(newEntry)        
        ##################
        return json.dumps(myResponse,sort_keys=True)

    def load_cmd_2_webIf(self,txtCmdName):
        try:
            myDescription,myUrl,myDict = self.load_command_let(txtCmdName,None)
            result =  "Status|OK\n"
            result += "Description|"+myDescription+"\n"
            result += "myUrl|"+myUrl+"\n"
            result += "payload|"+str(myDict)+"\n"
        except Exception as err:
            result =  "Status|failure\n"
            result += "value1|"+err.args[0]+"\n"
        ##################
        # prepare Response
        ##################
        myResult = result.splitlines()
        myResponse=[]
        newEntry=dict()
        for line in myResult:
            myFields=line.split("|")
            newEntry[myFields[0]] = myFields[1]

        myResponse.append(newEntry)        
        ##################
        return json.dumps(myResponse,sort_keys=True)
        
        
    def save_cmd_let(self,name,description,payload,ApiURL,path=None):
        if path==None:
            path=self.sh.get_basedir()+"/plugins/alexarc4shng/cmd/"
        
        result = ""
        mydummy = ApiURL[0:1]
        if (ApiURL[0:1] != "/"):
            ApiURL = "/"+ApiURL
            
        JsonResult = self.check_json(payload)
        if (JsonResult != 'Json OK'):
            result =  "Status:failure\n"
            result += "value1:"+JsonResult+"\n"
            
        else:
            try:
                myDict = json.loads(payload)
                myDump = json.dumps(myDict)
                description=description.replace("\r"," ")
                description=description.replace("\n"," ")
                file=open(path+name+".cmd","w")
                file.write("apiurl|"+ApiURL+"\r\n")
                file.write("description|"+description+"\r\n")
                file.write("json|"+myDump+"\r\n")
                file.close
    
                result =  "Status:OK\n"
                result += "value1:"+JsonResult + "\n"
                result += "value2:Saved Commandlet\n"
            except Exception as err:
                print (err)
        
        ##################
        # prepare Response
        ##################
        myResult = result.splitlines()
        myResponse=[]
        newEntry=dict()
        for line in myResult:
            myFields=line.split(":")
            newEntry[myFields[0]] = myFields[1]

        myResponse.append(newEntry)        
        ##################
        return json.dumps(myResponse,sort_keys=True)
    
    def auto_login(self):
        if self.credentials == '':
            return False
        # First delete tmp-Cookie
        try:
            os.remove(self.cookiefile+"_tmp")
        except:
            pass
        ####################################################
        # Start Step 1 - get Page without Post-Fields
        ####################################################
        if self.credentials != '':
            dummy = self.credentials.split(":")
            user = dummy[0]
            pwd = dummy[1]
        myResults= []
        ## start - First Step - generate Session-ID
        buffer = BytesIO()
        
        myUrl='https://'+self.host
        FirstHeader=["Accept-Language: de,en-US;q=0.7,en;q=0.3",
                     "DNT: 1",
                     "Upgrade-Insecure-Requests: 1",
                     "Connection: keep-alive",
                     "Content-Type: text/plain;charset=UTF-8",
                    ] 
    
        myCurl = pycurl.Curl()
        myCurl.setopt(pycurl.URL,myUrl)
        myCurl.setopt(pycurl.USERAGENT , "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0" )
        myCurl.setopt(pycurl.HTTPHEADER, FirstHeader)
        myCurl.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_1)
        myCurl.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_1)
        
        myCurl.setopt(pycurl.ENCODING,  "gzip, deflate") # , br entfernt
        myCurl.setopt(pycurl.HEADER,1)
        myCurl.setopt(pycurl.FOLLOWLOCATION, 1)
        
        myCurl.setopt(pycurl.COOKIEJAR ,self.cookiefile+"_tmp")
        myCurl.setopt(pycurl.COOKIEFILE ,self.cookiefile+"_tmp")
        myCurl.setopt(pycurl.WRITEDATA , buffer)
        myCurl.perform()
        header_size = myCurl.getinfo(pycurl.HEADER_SIZE)
        self.logger.info('Status of Auto-Login First Step: %d' % myCurl.getinfo(myCurl.RESPONSE_CODE))
        myResults.append('HTTP : ' + str(myCurl.getinfo(myCurl.RESPONSE_CODE))+'- Step 1 - get Session-ID')
        myCurl.close()        
        
        content=buffer.getvalue()
        content = content.decode()
        
        ## Get the hidden values
        content = str(content.replace('hidden', '\r\nhidden'))
        postdata = {}
        myFile = content.splitlines()
        for myLine in myFile:
            if 'hidden' in myLine:
                data = re.findall(r'hidden.*name="([^"]+).*value="([^"]+).*/',myLine)
                if len(data) >0:
                    postdata[data[0][0]]= data[0][1]
 
        
        postdata['showPasswordChecked'] = 'false'

        headers=content[0:header_size]
        content = content[header_size:len(content)]
        
        # Get Session-ID from Cookie-File
        actSessionID = ""
        try:
            with open (self.cookiefile+"_tmp", 'r') as fp:
                for line in fp:
                    if line.find('session-id')<0:
                            continue
                    if line.find('session-id-time')>0:
                            continue
                    if not re.match(r'^\#', line):
                        lineFields = line.strip().split('\t')
                        if len(lineFields) >= 7:
                            actSessionID = lineFields[6]
            fp.close()
        except:
            pass
        
        ####################################################
        ## done - First Step - generate Session-ID
        ####################################################
        
        ####################################################
        # Start Step 2 - login with form
        ####################################################
        # Get the Location-Referer
        for myLine in headers.splitlines():
            if 'Location' in myLine:
                data = re.findall('Location:(.*)/',myLine)
                myLocation = data[0].strip()
                myLocation = myLine.split(":")[1].strip()+':'+myLine.split(":")[2].strip()
 
 
        SecondHeader=["Accept-Language: de,en-US;q=0.7,en;q=0.3",
                      "DNT: 1",
                      "Upgrade-Insecure-Requests: 1",
                      "Connection: keep-alive",
                      "Referer: "+ myLocation
                     ]
        
        
        
        newUrl = "https://www.amazon.de"+"/ap/signin/"+actSessionID
        

        postfields = urllib3.request.urlencode(postdata)
        
        

        buffer = BytesIO()

        myCurl = pycurl.Curl()
        myCurl.setopt(pycurl.URL,newUrl)
        myCurl.setopt(pycurl.USERAGENT , "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0" )
        myCurl.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_1)
        myCurl.setopt(pycurl.ENCODING,  "gzip, deflate") # ,br entfernt
        myCurl.setopt(pycurl.POST,1)
        myCurl.setopt(pycurl.HEADER,1)
        myCurl.setopt(pycurl.FOLLOWLOCATION, 1)
        myCurl.setopt(pycurl.HTTPHEADER, SecondHeader)
        
        myCurl.setopt(pycurl.POSTFIELDS,postfields)
        
        myCurl.setopt(pycurl.COOKIEJAR ,self.cookiefile+"_tmp")
        myCurl.setopt(pycurl.COOKIEFILE ,self.cookiefile+"_tmp")
        
        myCurl.setopt(pycurl.WRITEDATA , buffer)
        myCurl.perform()
        content=buffer.getvalue()
        content = content.decode()
        header_size = myCurl.getinfo(pycurl.HEADER_SIZE)
        myResults.append('HTTP : ' + str(myCurl.getinfo(myCurl.RESPONSE_CODE))+'- Step 2 - login blank to get referer')
        self.logger.info('Status of Auto-Login Second Step: %d' % myCurl.getinfo(myCurl.RESPONSE_CODE))
        myCurl.close()
        
        
        headers=content[0:header_size]
        content = content[header_size:len(content)]
        
        
        ## Get the hidden values
        content = str(content.replace('hidden', '\r\nhidden'))
        postdata2 = {}
        myFile = content.splitlines()
        for myLine in myFile:
            if 'hidden' in myLine:
                if 'showPassword' in myLine:
                    print ("fdssadf")
                data = re.findall(r'hidden.*name="([^"]+).*value="([^"]+).*/',myLine)
                if len(data) >0:
                    postdata2[data[0][0]]= data[0][1]
 
        postdata2['showPasswordChecked'] = 'false'        
        
        
        
        # Get Session-ID from Cookie-File
        actSessionID = ""
        try:
            with open (self.cookiefile+"_tmp", 'r') as fp:
                for line in fp:
                    if line.find('session-id')<0:
                            continue
                    if line.find('session-id-time')>0:
                            continue
                    if not re.match(r'^\#', line):
                        lineFields = line.strip().split('\t')
                        if len(lineFields) >= 7:
                            actSessionID = lineFields[6]
            fp.close()
        except Exception as err:
            self.logger.debug('Cookiefile could not be opened %s' % self.cookiefile+"_tmp")

        ####################################################
        ## done - Second Step - generate Session-ID
        ####################################################
        
        ####################################################
        # Start Step 3 - login with form
        ####################################################
        ThirdHeader =["Accept-Language: de,en-US;q=0.7,en;q=0.3",
                      "DNT: 1",
                      "Connection: keep-alive",
                      "Upgrade-Insecure-Requests: 1",
                      "Content-Type: application/x-www-form-urlencoded",
                      "Referer: https://www.amazon.de/ap/signin/" + actSessionID
                     ]

        newUrl = "https://www.amazon.de/ap/signin"
        

        postdata2['email'] =user
        postdata2['password'] = pwd
        
        postfields = urllib3.request.urlencode(postdata2)
        buffer = BytesIO()
        myCurl = pycurl.Curl()
        myCurl.setopt(pycurl.URL,newUrl)
        myCurl.setopt(pycurl.USERAGENT , "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0" )
        myCurl.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_1)
        myCurl.setopt(pycurl.ENCODING,  "gzip, deflate")
        myCurl.setopt(pycurl.HEADER,1)
        myCurl.setopt(pycurl.FOLLOWLOCATION, 1)
        myCurl.setopt(pycurl.HTTPHEADER, ThirdHeader)
        myCurl.setopt(pycurl.POSTFIELDS,postfields)
        myCurl.setopt(pycurl.POST,1)
        
        myCurl.setopt(pycurl.COOKIEJAR ,self.cookiefile+"_tmp")
        myCurl.setopt(pycurl.COOKIEFILE ,self.cookiefile+"_tmp")
        
        myCurl.setopt(pycurl.WRITEDATA , buffer)
        myCurl.perform()
        
        content=buffer.getvalue()
        content = content.decode()
        header_size = myCurl.getinfo(pycurl.HEADER_SIZE)
        myResults.append('HTTP : ' + str(myCurl.getinfo(myCurl.RESPONSE_CODE))+'- Step 3 - login with credentials')
        self.logger.info('Status of Auto-Login Third Step: %d' % myCurl.getinfo(myCurl.RESPONSE_CODE))
        myCurl.close()
        
      
        
        headers=content[0:header_size]
        content = content[header_size:len(content)]
        
        
        
        #################################################################
        ## done - third Step - logged in now go an get the goal (csrf)
        #################################################################
        FourthHeader =["Accept-Language: de,en-US;q=0.7,en;q=0.3",
              "DNT: 1",
              "Connection: keep-alive",
              'Referer: https://'+self.host+ '/spa/index.html',
              'Origin: https://'+self.host
             ]

        newUrl = 'https://'+self.host+'/api/language'
        myCurl = pycurl.Curl()
        myCurl.setopt(pycurl.URL,newUrl)
        myCurl.setopt(pycurl.USERAGENT , "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0" )
        myCurl.setopt(pycurl.HTTPHEADER, FourthHeader)
        myCurl.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_1)
        myCurl.setopt(pycurl.ENCODING,  "gzip, deflate") # , br entfernt
        myCurl.setopt(pycurl.HEADER,1)
        myCurl.setopt(pycurl.FOLLOWLOCATION, 1)
        
        myCurl.setopt(pycurl.COOKIEJAR ,self.cookiefile+"_tmp")
        myCurl.setopt(pycurl.COOKIEFILE ,self.cookiefile+"_tmp")
        myCurl.setopt(pycurl.WRITEDATA , buffer)
        myCurl.perform()
        
        
        content=buffer.getvalue()
        content = content.decode()
        
        myResults.append('HTTP : ' + str(myCurl.getinfo(myCurl.RESPONSE_CODE))+'- Step 4 - get csrf')
        self.logger.info('Status of Auto-Login fourth Step: %d' % myCurl.getinfo(myCurl.RESPONSE_CODE))
        myCurl.close()
        # Hopefully we got an new csrf - so check it
        my_csrf = self.parse_cookie_file(self.cookiefile+'_tmp')
        if (my_csrf != 'N/A'):
            self.csrf = my_csrf
            myResults.append('check CSRF- Step 5 - got good csrf')
            ############################################################
            # now move the TMP-Cookie to the real cookie
            try:
                if os.path.isfile(self.cookiefile+'_tmp'):
                    try:
                        os.remove(self.cookiefile)
                    except:
                        pass
                    os.popen('mv '+self.cookiefile+'_tmp' + ' ' + self.cookiefile)
                    time.sleep(1)
                myResults.append('created new cookie-File - Step 6 - done')
                self.login_state= self.check_login_state()
                myResults.append('login state : %s' % self.login_state)
            except:
                myResults.append('created new cookie-File - Step 6 - finished with error')
        else:
            myResults.append('check CSRF- Step 5 - error -got no CSRF')
        
                
        return myResults
        
        
    
    
    def log_off(self):
        buffer = BytesIO()
        myUrl='https://'+self.host+"/logout"
        FirstHeader=["DNT: 1",
                     "Connection: keep-alive"
                     "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0",
                    ] 
        try:
            myCurl = pycurl.Curl()
            myCurl.setopt(pycurl.URL,myUrl)
            myCurl.setopt(pycurl.USERAGENT , "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) Gecko/20100101 Firefox/65.0" )
            myCurl.setopt(pycurl.HTTPHEADER, FirstHeader)
            myCurl.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_1)
            myCurl.setopt(pycurl.ENCODING,  "gzip, deflate")
            myCurl.setopt(pycurl.HEADER,1)
            
            #myCurl.setopt(pycurl.RETURNTRANSFER,1)
            myCurl.setopt(pycurl.FOLLOWLOCATION, 1)
            
            myCurl.setopt(pycurl.COOKIEFILE ,self.cookiefile)
            myCurl.setopt(pycurl.WRITEDATA , buffer)
            myCurl.perform()
            myResult = myCurl.getinfo(myCurl.RESPONSE_CODE)
            myCurl.close()
        except Exception as err:
            print(err)
            
            
        
        self.logger.info('Status of log_off: %d' % myResult)
        
        if myResult == 200:
            return "HTTP - " + str(myResult)+" successfully logged off"
        else:
            return "HTTP - " + str(myResult)+" Erro while logging off"
        
    
    ##############################################
    # Help - End Functions by pycurl
    ##############################################
    
    def init_webinterface(self):
        """"
        Initialize the web interface for this plugin

        This method is only needed if the plugin is implementing a web interface
        """
        try:
            self.mod_http = Modules.get_instance().get_module(
                'http')  # try/except to handle running in a core version that does not support modules
        except:
            self.mod_http = None
        if self.mod_http == None:
            self.logger.error("Plugin '{}': Not initializing the web interface".format(self.get_shortname()))
            return False

        # set application configuration for cherrypy
        webif_dir = self.path_join(self.get_plugin_dir(), 'webif')
        config = {
            '/': {
                'tools.staticdir.root': webif_dir,
            },
            '/static': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': 'static'
            }
        }

        # Register the web interface as a cherrypy app
        self.mod_http.register_webif(WebInterface(webif_dir, self),
                                     self.get_shortname(),
                                     config,
                                     self.get_classname(), self.get_instance_name(),
                                     description='')

        return True


    
 

# ------------------------------------------
#    Webinterface of the plugin
# ------------------------------------------

import cherrypy
from jinja2 import Environment, FileSystemLoader

class WebInterface(SmartPluginWebIf):


    def __init__(self, webif_dir, plugin):
        """
        Initialization of instance of class WebInterface

        :param webif_dir: directory where the webinterface of the plugin resides
        :param plugin: instance of the plugin
        :type webif_dir: str
        :type plugin: object
        """
        self.logger = logging.getLogger(__name__)
        self.webif_dir = webif_dir
        self.plugin = plugin
        self.tplenv = self.init_template_environment()


    def render_template(self, tmpl_name, **kwargs):
        """

        Render a template and add vars needed gobally (for navigation, etc.)
    
        :param tmpl_name: Name of the template file to be rendered
        :param **kwargs: keyworded arguments to use while rendering
        
        :return: contents of the template after beeing rendered 

        """
        tmpl = self.tplenv.get_template(tmpl_name)
        return tmpl.render(plugin_shortname=self.plugin.get_shortname(), plugin_version=self.plugin.get_version(),
                   plugin_info=self.plugin.get_info(), p=self.plugin,
                   **kwargs)

    def set_cookie_pic(self,CookieOK=False):
        dstFile = self.plugin.sh.get_basedir()+'/plugins/alexarc4shng/webif/static/img/plugin_logo.png'
        srcGood = self.plugin.sh.get_basedir()+'/plugins/alexarc4shng/webif/static/img/alexa_cookie_good.png'
        srcBad = self.plugin.sh.get_basedir()+'/plugins/alexarc4shng/webif/static/img/alexa_cookie_bad.png'
        if os.path.isfile(dstFile):
                os.remove(dstFile)
        if CookieOK==True:
            if os.path.isfile(srcGood):
                os.popen('cp '+srcGood + ' ' + dstFile)
        else:
            if os.path.isfile(srcBad):
                os.popen('cp '+srcBad + ' ' + dstFile)            

    @cherrypy.expose
    def index(self, reload=None):
        """
        Build index.html for cherrypy

        Render the template and return the html file to be delivered to the browser

        :return: contents of the template after beeing rendered
        """
        
        if (self.plugin.login_state != 'N/A'):
            self.set_cookie_pic(True)
        else:
            self.set_cookie_pic(False)
        
        myDevices = self.get_device_list()
        alexa_device_count = len(myDevices)
        
        login_info = self.plugin.last_update_time + '<font color="green"><strong>('+ self.plugin.next_update_time + ')</strong>' 
        return self.render_template('index.html',device_list=myDevices,csrf_cookie=self.plugin.csrf,alexa_device_count=alexa_device_count,time_auto_login=login_info)
        '''
        tmpl = self.tplenv.get_template('index.html')
        return tmpl.render(plugin_shortname=self.plugin.get_shortname(), plugin_version=self.plugin.get_version(),
                           plugin_info=self.plugin.get_info(), p=self.plugin,
                           device_list=myDevices)
        '''
   
   
    @cherrypy.expose
    def log_off_html(self,txt_Result=None):
        txt_Result=self.plugin.log_off()
        return json.dumps(txt_Result)
    
    @cherrypy.expose
    def log_in_html(self,txt_Result=None):
        txt_Result=self.plugin.auto_login()
        return json.dumps(txt_Result)
        
                           
    @cherrypy.expose
    def handle_buttons_html(self,txtValue=None, selectedDevice=None,txtButton=None,txt_payload=None,txtCmdName=None,txtApiUrl=None,txtDescription=None):
        if txtButton=="BtnSave":
            result = self.plugin.save_cmd_let(txtCmdName,txtDescription,txt_payload,txtApiUrl)
        elif txtButton =="BtnCheck":
            pass
        elif txtButton =="BtnLoad":
            result = self.plugin.load_cmd_2_webIf(txtCmdName)
            pass
        elif txtButton =="BtnTest":
            result = self.plugin.test_cmd_let(selectedDevice,txtValue,txtDescription,txt_payload,txtApiUrl)
        elif txtButton =="BtnDelete":
            result = self.plugin.delete_cmd_let(txtCmdName)
        else:
            pass
        
        #return self.render_template("index.html",txtresult=result)
        return result
                
    
    @cherrypy.expose
    def build_cmd_list_html(self,reload=None):
        myCommands = self.plugin.load_cmd_list()
        return myCommands
    
    
    def get_device_list(self):
        if (self.plugin.login_state == True):
            self.plugin.Echos = self.plugin.get_devices_by_curl()
        
        Device_items = []
        try:
            myDevices = self.plugin.Echos.devices
            for actDevice in myDevices:
                newEntry=dict()
                Echo2Add=self.plugin.Echos.devices.get(actDevice)
                newEntry['name'] = Echo2Add.id
                newEntry['serialNumber'] = Echo2Add.serialNumber
                newEntry['family'] = Echo2Add.family
                newEntry['deviceType'] = Echo2Add.deviceType
                newEntry['deviceOwnerCustomerId'] = Echo2Add.deviceOwnerCustomerId
                Device_items.append(newEntry)
            
        except Exception as err:
            self.logger.debug('No devices found',err)
        
        return Device_items
        
        
    @cherrypy.expose
    def storecookie_html(self, save=None, cookie_txt=None, txt_Result=None):
        myLines = cookie_txt.splitlines()
        #
        # Problem - different Handling of Cookies by Browser

        file=open("/tmp/cookie.txt","w")
        for line in myLines:
            file.write(line+"\r\n")
        file.close()
        value1 = self.plugin.parse_cookie_file("/tmp/cookie.txt")
        self.plugin.login_state = self.plugin.check_login_state()
        
        if (self.plugin.login_state == True):
            self.set_cookie_pic(True)
        else:
            self.set_cookie_pic(False)
        
        
        if (self.plugin.login_state == False) :
            # Cookies not found give back an error
            tmpl = self.tplenv.get_template('index.html')
            return tmpl.render(plugin_shortname=self.plugin.get_shortname(), plugin_version=self.plugin.get_version(),
                           plugin_info=self.plugin.get_info(), p=self.plugin,
                           txt_Result='<font color="red"><i class="fas fa-exclamation-triangle"></i> Cookies are not saved missing csrf',
                           cookie_txt=cookie_txt,
                           csrf_cookie=value1)
        
        # Store the Cookie-file for permanent use
        file=open(self.plugin.cookiefile,"w")
        for line in myLines:
            file.write(line+"\r\n")
        file.close()
        
        self.plugin.csrf = value1
        
        
        myDevices = self.get_device_list()
        alexa_device_count = len(myDevices)
        
        
        tmpl = self.tplenv.get_template('index.html')
        return tmpl.render(plugin_shortname=self.plugin.get_shortname(), plugin_version=self.plugin.get_version(),
                           plugin_info=self.plugin.get_info(), p=self.plugin,
                           txt_Result='<font color="green"> <strong><i class="far fa-check-circle"></i> Cookies were saved - everything OK<strong>',
                           cookie_txt=cookie_txt,
                           csrf_cookie=value1,
                           device_list=myDevices,
                           alexa_device_count=alexa_device_count)
                           

        

