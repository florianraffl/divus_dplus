import aiohttp
import xml.etree.ElementTree as ET
from urllib.parse import urlencode, quote

class DivusDplusApi:
    def __init__(self, host, username, password):
        self._base = f"http://{host}//www/modules/system/"
        self._username = username
        self._password = password
        self._session = aiohttp.ClientSession()
        self._sessionId = None

        # Constants for D+ systems
        self._topSurroundingId = "187"
        self._environmentSurroundingName = "_DPAD_PRODUCT_K3_MENU_ENVIRONMENTS"
        self._systemOwner = "SYSTEM"

    async def get_devices(self):
        topXml = await self._get_surroundings(self._topSurroundingId)

        environmentSurroundingId = topXml['getObjsFromId']['data'].filter(lambda x: x['NAME'] == self._environmentSurroundingName)['ID']
        environmentXml = await self._get_surroundings(environmentSurroundingId)
        devices = []
        for room in environmentXml['getObjsFromId']['data'].filter(lambda x: x['OWNED_BY'] == self._systemOwner):
            roomId = room['ID']
            deviceXml = await self._get_surroundings(roomId)
            for device in deviceXml['getObjsFromId']['data']:
                devices.append(device)
        return devices

    async def get_state(self, device_id):
        async with self._session.get(self._base + f"device/{device_id}/state") as r:
            return await r.json()

    async def set_state(self, device_id, value):
        async with self._session.post(self._base + f"device/{device_id}/set", json=value) as r:
            return await r.json()
        
    async def _get_surroundings(self, surrounding_id):
        formData = {
            "ids": surrounding_id,
            "filter": "",
            "order": "ORDER_NUM%2CID+",
            "limit": "",
            "context": "runtime",
            "sessionId": await self._getSessionId()
        }
        
        async with self._session.post(self._base + "surrounding.php", data=urlencode(formData), headers={"Content-Type": "application/x-www-form-urlencoded"}) as r:
            text = await r.text()
            return ET.fromstring(text)
    
    async def _getSessionId(self):

        if(self._sessionId):
            return self._sessionId

        formData = {
            "username": self._username,
            "password": self._password,
            "context": "runtime",
            "op": "login"
        }
        async with self._session.post(self._base + "login.php", data=urlencode(formData), headers={"Content-Type": "application/x-www-form-urlencoded"}) as resp:
            text = await resp.text()
            xml = ET.fromstring(text)
            sessionId = xml.find(".//sessionId")
            if sessionId is not None:
                self._sessionId = sessionId.text
                return self._sessionId
            else:
                raise Exception("Login failed")
