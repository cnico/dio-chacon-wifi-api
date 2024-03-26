# Protocol for DIO devices
Here is a description of the wifi protocol to be used through the chacon's cloud in order to connect and handle DIO devices (REV-SHUTTER or REV-LIGHT).

# Connection :
To connect to the cloud service, use this type of REST request :
Server Url : https://l4hfront-prod.chacon.cloud/api/session/login
Content :

    {"email":"USER","password":"PASSWORD","installationId":"top"}

USER is to be replaced by your user's mail.
PASSWORD is to be replaced by your password.
installationId should have the value of your installation instance but we send it an arbitrary content here.

Typical answer :

    {"status":200,"data":{"sessionToken":"r:9deb0bfeb982314029166810e940f3ab"}}

Then switch to WebSockets since devices actions and states are handled via a websocket connection.
Url for websockets switching :
l4hfront-prod.chacon.cloud/ws?sessionToken=r:9deb0bfeb982314029166810e940f3ab

At connection, it responds with a content like :

    {"name":"connection","action":"success","data":""}

# User info retrieval :
Send this content to the web socket :

    {"method":"GET","path":"/user","parameters":{},"id":1}

Note : the id attribute for each request has to be incremented since the response always contains an id that corresponds to the question.

The response will be of the following type (I replaced some content with dots) :

    {
        "id": 2,
        "status": 200,
        "data": {
            "id": "...",
            "name": "... ",
            "email": "...",
            "isNewsletter": true,
            "isPromoNotification": true,
            "isAIImageObjectDetection": true,
            "bleKey": "..."
        }
    }

# Devices retrieval :
Send this content to the web socket :

    {"method":"GET","path":"/device","parameters":{},"id":1}

The response will be of the following type (I replaced some content with dots) :

    {
    "id": 1,
    "status": 200,
    "data": [
        {
            "id": "L4HActuator_...",
            "createdAt": "...",
            "provider": "L4HActuator",
            "name": "...",
            "defaultName": "CERSwd-3B",
            "modelName": "CERSwd-3B",
            "vendor": "Chacon",
            "hardwareVersion": "1.0",
            "softwareVersion": "1.0.6",
            "macAddress": "...",
            "type": ".dio1.wifi.shutter.mvt_linear.",
            "roomId": "...",
            "image": null
        },
        {
            ...
        }
    ]
    }

For a switch, type will be : .dio1.wifi.genericSwitch.switch.


# Devices position retrieval :

    {"method":"POST","path":"/device/states","parameters":{"devices":["L4HActuator_...", ... ]},"id":22}

Will return the status of every given device via such an answer :

    {
    "id": 22,
    "status": 200,
    "data": {
        "L4HActuator_...": {
            "rt": "oic.d.blind",
            "href": "/v1/devices/L4HActuator_...",
            "provider": "L4HActuator",
            "rc": 0,
            "t": 0,
            "di": "L4HActuator_...",
            "n": "CERSwd-3B_...",
            "links": [
                {
                    "rt": "oic.wk.p",
                    ...
                },
                {
                    "rt": "oic.r.movement.linear",
                    "href": "mvtlinear",
                    "movement": "stop",
                    "movementSettings": [
                        "stop",
                        "up",
                        "down"
                    ]
                },
                {
                    "rt": "oic.r.openlevel",
                    "href": "openlevel",
                    "openLevel": 0
                },
                {
                    "rt": "gw.r.shutter.calibration",
                    "href": "shuttercalibration",
                    "up_ms": 10683,
                    "down_ms": 10370,
                    "direction": 0,
                    "reset": false,
                    "door": false
                },
                {
                    "rt": "gw.r.schedule",
                    "href": "schedule",
                    ...
                    ]
                },
                {
                    "rt": "gw.r.dio1.switch",
                    "href": "dio1_switch",
                    "value": 0
                },
                {
                    "rt": "gw.r.dio1.paired",
                    "href": "dio1paired",
                    ...
                }
            ]
        },
        {...}
    }
    }

Relevant informations are the movement attribute describing if the shutter is moving up, down or stopped ; the openlevel and the shutter calibration.
To know if a device is connected or disconnected from the wifi, in the 'rt'='oic.d.blind' section, the attribute 'rc' to 1 means the device is connected and to 0 is that it is disconnected.

# Shutter device action :

"stop", "up" or "down" action :

    {"method":"POST","path":"/device/L4HActuator_.../action/mvtlinear","parameters":{"movement":"down"},"id":8}

The Response sends lots of data including the configuration and the current position of the shutter.

    {
    "name": "deviceState",
    "action": "update",
    "data": {...
    }
    }

At the end of movment, another response is sent from the server that is similar to the previous answer but with a "stop" event.
An attribute named openlevel with a value between 0 and 100 gives the current high of the shutter.


Action to set a given position, for exemple 75% opened :

    {"method":"POST","path":"/device/L4HActuator_.../action/openlevel","parameters":{"openLevel":75},"id":24}


NOTE : For group actions or multiple shutter, simply send as many json request as shutters to act on.

# Device light retrieval :

    {"method":"POST","path":"/device/states","parameters":{"devices":["L4HActuator_...", ... ]},"id":22}

Will return the status of every given device via such an answer :

    {
    "id": 6,
    "status": 200,
    "data": {
        "L4HActuator_...": {
            "rt": "oic.d.switch",
            "href": "/v1/devices/L4HActuator_...",
            "provider": "L4HActuator",
            "rc": 1,
            "t": 0,
            "di": "L4HActuator_...",
            "n": "CWMSwd-2B_...",
            "links": [
                {
                    "rt": "oic.wk.p",
                    "href": "platform",
                    ...
                },
                {
                    "rt": "oic.r.switch.binary",
                    "href": "switch",
                    "value": 0
                },
                {
                    "rt": "gw.r.quietmode",
                    "href": "quietmode",
                    "value": 0
                },
                {
                    "rt": "gw.r.schedule",
                    "href": "schedule",
                    "maxSchedules": 8,
                    "sun": 1,
                    "schedules": [
                        ...
                    ]
                },
                {
                    "rt": "gw.r.dio1.paired",
                    "href": "dio1paired",
                    ...
                }
            ]
        }
    }
    }

The oic.r.switch.binary gives the information if the light is on or off.

# Switching a light on or off :

    {"method":"POST","path":"/device/L4HActuator_.../action/switch","parameters":{"value":0},"id":12}

Possible values are 0 or 1 to switch on or off.

# Disconnecting :

    {"method":"POST","path":"/session/logout","parameters":{},"id":13}

# Other API verbs not implemented by this lib :
Via the Web socket, send either one of this request :

For rooms definitions retrieval :

    {"method":"GET","path":"/room","parameters":{},"id":3}

For groups definitions retrieval :

    {"method":"GET","path":"/group","parameters":{},"id":4}

For static content in the mobile app :
    {"method":"GET","path":"/static/all","parameters":{},"id":5}
