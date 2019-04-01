#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
#  Copyright 2017 <AUTHOR>                                        <EMAIL>
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


from io import BytesIO
import pycurl
from subprocess import Popen, PIPE
import json
import sys
import os
import re





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

##############################################################################

class alexarc4shng(SmartPlugin):
    PLUGIN_VERSION = '1.0.0'
    ALLOW_MULTIINSTANCE = False
    """
    Main class of the Plugin. Does all plugin specific stuff and provides
    the update functions for the items
    """

    PLUGIN_VERSION = '1.0.0'

    def __init__(self, sh, cookiefile = '', host =''):
        
        self.logger = logging.getLogger(__name__)
        self.sh = sh
        self.header = ''
        self.cookiefile = cookiefile
        self.csrf = 'N/A'
        self.a2s_csrf = 'N/A'
        self.postfields=''
        self.host = host
        self.shngObjects = shngObjects()
        
        self.csrf = self.parseCookieFile(self.cookiefile)
        # Collect all devices
        self.Echos = self.getDevicesbyCurl()

        if not self.init_webinterface():
            self._init_complete = False
        
        return

    def run(self):
        """
        Run method for the plugin
        """
        self.logger.info("Plugin '{}': start method called".format(self.get_fullname()))
        self.alive = True
        while self.alive == True:
            sleep(2)
        # if you want to create child threads, do not make them daemon = True!
        # They will not shutdown properly. (It's a python bug)

    def stop(self):
        """
        Stop method for the plugin
        """
        self.logger.debug("Plugin '{}': stop method called".format(self.get_fullname()))
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

            self.logger.debug("Plugin '{}': parse item: {}".format(self.get_fullname(), item))
            
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
        newValue=str(item())
        oldValue=str(item.prev_value())
        if(item.prev_value()==item()):
            return 
        
        CmdItem_ID = item._name
        
    
        if self.shngObjects.exists(CmdItem_ID):
            self.logger.debug(
                "Plugin '{}': update_item ws called with item '{}' from caller '{}', source '{}' and dest '{}'".format(
                    self.get_fullname(), item, caller, source, dest))
            
            
            actValue = str(item())
            
            actDevice = self.shngObjects.get(CmdItem_ID)
            
            for myCommand in actDevice.Commands:
                
                if (actValue == str(myCommand.ItemValue) and myCommand):
                    self.SendCmdByCurl(myCommand.EndPoint,myCommand.Action,myCommand.Value)


        # PLEASE CHECK CODE HERE. The following was in the old skeleton.py and seems not to be 
        # valid any more 
        # # todo here: change 'plugin' to the plugin name
        # if caller != 'plugiSmartPluginn':
        #    logger.info("update item: {0}".format(item.id()))
    
    ##############################################
    # Help -Start Functions by pycurl
    ##############################################
    
    def SendCmdByCurl(self,dvName, cmdName,mValue,path=None):
        buffer = BytesIO()
        actEcho = self.Echos.get(dvName)
        myUrl='https://'+self.host
        myDescriptions = ''
        myDict = {}
        
        
        myDescription,myUrl,myDict = self.LoadCommandlet(cmdName,path)
        # complete the URL
        myUrl='https://'+self.host+myUrl
        # replace the placeholders in URL
        myUrl=self.ParseUrl(myUrl,
                            mValue,
                            actEcho.serialNumber,
                            actEcho.family,
                            actEcho.deviceType,
                            actEcho.deviceOwnerCustomerId)
        
        # replace the placeholders in Payload
        myheaders=self.CreateCurlHeader() 
        postfields = self.ParseJson2Curl(myDict,
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
        myCurl.setopt(pycurl.WRITEDATA , buffer)
        myCurl.setopt(pycurl.POST,1)
        if len(postfields) > 20:
         myCurl.setopt(pycurl.POSTFIELDS,postfields)
        myCurl.perform()
        self.logger.info('Status of SendCmdByCurl: %d' % myCurl.getinfo(myCurl.RESPONSE_CODE))
        
        return myCurl.getinfo(myCurl.RESPONSE_CODE)
        

    
    def getDevicesbyCurl(self):
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
            self.logger.info('Status of getDevicesbyCurl: %d' % myCurl.getinfo(myCurl.RESPONSE_CODE))
            body=buffer.getvalue()
            mybody = body.decode()
            myDict=json.loads(mybody)
            myDevices = EchoDevices()
        except Exception as err:
            self.logger.debug('Error while getting Devices',err)
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
                self.logger.debug('Error while getting Devices',err)
                myDevices = None
                
        return myDevices
    
    def parseCookieFile(self,cookiefile):
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

        except Exception as err:
            self.logger.debug('Cookiefile could not be opened %s' % cookiefile)
        
        return csrf
    
    
    def ParseUrl(self,myDummy,mValue,serialNumber,familiy,deviceType,deviceOwnerCustomerId):
        
        myDummy = myDummy.strip()
        myDummy=myDummy.replace(' ','')
        myDummy=myDummy.replace('<mValue>',mValue)
        
        # Inject the Device informations
        myDummy=myDummy.replace('<serialNumber>',serialNumber)
        myDummy=myDummy.replace('<familiy>',familiy)
        myDummy=myDummy.replace('<deviceType>',deviceType)
        myDummy=myDummy.replace('<deviceOwnerCustomerId>',deviceOwnerCustomerId)
        
        return myDummy

    def ParseJson2Curl(self,myDict,mValue,serialNumber,familiy,deviceType,deviceOwnerCustomerId):

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
        myDummy=myDummy.replace('<mValue>',mValue)
        
        # Inject the Device informations
        myDummy=myDummy.replace('<serialNumber>',serialNumber)
        myDummy=myDummy.replace('<familiy>',familiy)
        myDummy=myDummy.replace('<deviceType>',deviceType)
        myDummy=myDummy.replace('<deviceOwnerCustomerId>',deviceOwnerCustomerId)
        
        return myDummy
    
    def CreateCurlHeader(self):
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
    
    def LoadCommandlet(self,cmdName,path=None):
        myDescription   = ''
        myUrl           = ''
        myJson          = ''
        retJson         = {}
        
        if path==None:
            path="/usr/local/smarthome/plugins/alexarc4shng/cmd/"
            
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
    

    
    def LoadCmdList(self):
        retValue=[]
        files = os. listdir('/usr/local/smarthome/plugins/alexarc4shng/cmd/')
        for line in files:
            line=line.split(".")
            newCmd = {'Name':line[0]}
            retValue.append(newCmd)
        
        return json.dumps(retValue)

    def CheckJson(self,payload):
        try:
            myDump = json.loads(payload)
            return 'Json OK'
        except Exception as err:
            return 'Json - Not OK - '+ err.args[0]
        
    def DeleteCmdLet(self,name):
        result = ""
        try:
            os.remove("/usr/local/smarthome/plugins/alexarc4shng/cmd/"+name+'.cmd')
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
    
    def TestCmdLet(self,selectedDevice,txtValue,txtDescription,txt_payload,txtApiUrl):
        result = ""
        if (txtApiUrl[0:1] != "/"):
            txtApiUrl = "/"+txtApiUrl
            
        JsonResult = self.CheckJson(txt_payload)
        if (JsonResult != 'Json OK'):
            result =  "Status:failure\n"
            result += "value1:"+JsonResult+"\n"
        else:
            try:
                self.SaveCmdLet("test", txtDescription, txt_payload, txtApiUrl, "/tmp/")
                retVal = self.SendCmdByCurl(selectedDevice,"test",txtValue,"/tmp/")
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

    def LoadCmd2WebIf(self,txtCmdName):
        try:
            myDescription,myUrl,myDict = self.LoadCommandlet(txtCmdName,None)
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
        
        
    def SaveCmdLet(self,name,description,payload,ApiURL,path=None):
        if path==None:
            path="/usr/local/smarthome/plugins/alexarc4shng/cmd/"
        
        result = ""
        mydummy = ApiURL[0:1]
        if (ApiURL[0:1] != "/"):
            ApiURL = "/"+ApiURL
            
        JsonResult = self.CheckJson(payload)
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


    @cherrypy.expose
    def index(self, reload=None):
        """
        Build index.html for cherrypy

        Render the template and return the html file to be delivered to the browser

        :return: contents of the template after beeing rendered
        """
        
        myDevices = self.GetDeviceList()
        alexa_device_count = len(myDevices)
        return self.render_template('index.html',device_list=myDevices,csrf_cookie=self.plugin.csrf,alexa_device_count=alexa_device_count)
        '''
        tmpl = self.tplenv.get_template('index.html')
        return tmpl.render(plugin_shortname=self.plugin.get_shortname(), plugin_version=self.plugin.get_version(),
                           plugin_info=self.plugin.get_info(), p=self.plugin,
                           device_list=myDevices)
        '''
    @cherrypy.expose
    def handleButtons_html(self,txtValue=None, selectedDevice=None,txtButton=None,txt_payload=None,txtCmdName=None,txtApiUrl=None,txtDescription=None):
        if txtButton=="BtnSave":
            result = self.plugin.SaveCmdLet(txtCmdName,txtDescription,txt_payload,txtApiUrl)
        elif txtButton =="BtnCheck":
            pass
        elif txtButton =="BtnLoad":
            result = self.plugin.LoadCmd2WebIf(txtCmdName)
            pass
        elif txtButton =="BtnTest":
            result = self.plugin.TestCmdLet(selectedDevice,txtValue,txtDescription,txt_payload,txtApiUrl)
        elif txtButton =="BtnDelete":
            result = self.plugin.DeleteCmdLet(txtCmdName)
        else:
            pass
        
        #return self.render_template("index.html",txtresult=result)
        return result
                
    
    @cherrypy.expose
    def BuildCmdList_html(self,reload=None):
        myCommands = self.plugin.LoadCmdList()
        return myCommands
    
    
    def GetDeviceList(self):
        self.plugin.Echos = self.plugin.getDevicesbyCurl()
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
        value1 = self.plugin.parseCookieFile("/tmp/cookie.txt")
        if (value1 == "N/A") :
            # Cookies not found give back an error
            tmpl = self.tplenv.get_template('index.html')
            return tmpl.render(plugin_shortname=self.plugin.get_shortname(), plugin_version=self.plugin.get_version(),
                           plugin_info=self.plugin.get_info(), p=self.plugin,
                           txt_Result='<font color="red"><i class="fas fa-exclamation-triangle"></i> Cookies are not saved missing csrf or a2s_csrf',
                           cookie_txt=cookie_txt,
                           csrf_cookie=value1)

        file=open(self.plugin.cookiefile,"w")
        for line in myLines:
            file.write(line+"\r\n")
        file.close()
        
        self.plugin.csrf = value1
        myDevices = self.GetDeviceList()
        alexa_device_count = len(myDevices)
        
        
        tmpl = self.tplenv.get_template('index.html')
        return tmpl.render(plugin_shortname=self.plugin.get_shortname(), plugin_version=self.plugin.get_version(),
                           plugin_info=self.plugin.get_info(), p=self.plugin,
                           txt_Result='<font color="green"> <strong><i class="far fa-check-circle"></i> Cookies were saved - everything OK<strong>',
                           cookie_txt=cookie_txt,
                           csrf_cookie=value1,
                           device_list=myDevices,
                           alexa_device_count=alexa_device_count)
                           

        

