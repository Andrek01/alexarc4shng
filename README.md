# AlexaRc4shNG

#### Version 1.0.0

The plugin gives the possibilty to control an Alexa-Echo-Device remote.
So its possible to switch on an TuneIn-Radio Channel, send some messages via Text2Speech when an event happens on the knx-bus or on the Visu. On the Web-Interface you can define your own commandlets. The follwing functions are available on the Web-Interface :

- Store a cookie-file to get access to the Alexa-WebInterface
- See all available devices, select one to send Test-Functions
- define Commandlets - you can load,store,delete, check and test Commandlets
- the Commandlets can be loaded to the webinterface by clicking on the list
- the Json-Structure can be checked on the WebInterface

In the API-URL and in the json-payload you have to replace the real values from the Alexa-Webinterface with the following placeholders. For testing functions its not really neccessary to use the placeholders.

###Placeholders :

```
<mValue>				= Value to send
<serialNumber>			= SerialNo. of the device where the command should go to
<familiy>				= device family
<deviceType>			= deviceType
<deviceOwnerCustomerId>	= OwnerID of the device
```
####<strong>!! Please keep in mind to use the "<" and the ">" the qualify the placeholders !!</strong>

## Change Log



### Changes Since version 1.x.x

- no changes, first Release



## Requirements

List the requirements of your plugin. Does it need special software or hardware?

### Needed software

* the plugin need pycurl (pip install pycurl)
* smarthomeNg 1.4.2 and above for the web-interface


### Supported Hardware

* all that supports smartHomeNG


## Configuration

### plugin.yaml

The plugin needs to be defined in the plugin.yaml in this way. The attributes are : <br> class_name -> fix <br> class_path -> fix (depending on you configuration) <br> cookiefile -> the path to the cookie-file. Here it will stored from the Web-Interfache<br>host -> the adress of you Alexa-WebInterface


```yaml
alexarc4shng:
    class_name: alexarc4shng
    class_path: plugins.alexarc4shng
    cookiefile: '/usr/local/smarthome/plugins/alexarc4shng/cookies.txt'
    host:       'alexa.amazon.de'
```



### items.yaml

The configuration of the item are done in the following way :
<strong><br><br>
alexa_cmd_01: Value:EchoDevice:Commandlet:Value_to_Send

Sampe to switch on a Radiostation by using TuneIN<br><br>
Value = True means the item() becomes "ON"<br>
EchodotKueche = Devicename where the Command should be send to<br>
StartTuneInStaion = Name of the Commandlet<br>
S96141 = Value of the Radiostation (here S96141 = baden.fm)

example:
alexa_cmd_01: True:EchoDotKueche:StartTuneInStation:s96141
</strong>

#### alexa_cmd_XX

You can specify up to 99 Commands per shng-item. The plugin scanns the item.conf/item.yaml during initialization for commands starting with 01 up to 99.

<strong>Please start all the time with 01, the command-numbers must be serial, dont forget one the scann of commands is stopped when there is no command found with the next number</strong>

#### Example

Example for settings in an item.yaml file :

```yaml
# items/my.yaml
%YAML 1.1
---

OG:

    Buero:
        name: Buero
        Licht:
            type: bool
            alexa_name: Licht Büro
            alexa_description: Licht Büro
            alexa_actions: TurnOn TurnOff
            alexa_icon: LIGHT
            alexa_cmd_01: True:EchoDotKueche:StartTuneInStation:s96141
            alexa_cmd_02: True:EchoDotKueche:Text2Speech:Hallo das Licht im Buero ist eingeschalten
            alexa_cmd_03: False:EchoDotKueche:Text2Speech:Hallo das Licht im Buero ist aus
            alexa_cmd_04: 'False:EchoDotKueche:Pause: '
            visu_acl: rw
            knx_dpt: 1
            knx_listen: 1/1/105
            knx_send: 1/1/105
            enforce_updates: 'true'

```
Example for settings in an item.conf file :

```yaml
# items/my.conf

[OG]
    [[Buero]]
        name = Buero
        [[[Licht]]]
        type = bool
        alexa_name = "Licht Büro"
        alexa_description = "Licht Büro"
	alexa_actions = "TurnOn TurnOff"
        alexa_icon = "LIGHT"
        alexa_cmd_01 = "True:EchoDotKueche:StartTuneInStation:s96141"
        alexa_cmd_02 = "True:EchoDotKueche:Text2Speech:Hallo das Licht im Buero ist eingeschalten"
	alexa_cmd_03 = "False:EchoDotKueche:Text2Speech:Hallo das Licht im Buero ist aus"
	alexa_cmd_04 = "False:EchoDotKueche:Pause: "		
        visu_acl = rw
        knx_dpt = 1
        knx_listen = 1/1/105
        knx_send = 1/1/105
        enforce_updates = truey_attr: setting
```

### logic.yaml
Right now no logics are implemented. But you can trigger the items by your own logic


## Methods
No methods are implemented

