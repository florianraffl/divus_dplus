import aiohttp
import logging
import xml.etree.ElementTree as ET
from urllib.parse import urlencode

from custom_components.divus_dplus.dtos import DeviceDto, DeviceStateDto

class DivusDplusApi:
    def __init__(self, host: str, username: str, password: str, logger: logging.Logger):
        self._base = f"http://{host}/"
        self._username = username
        self._password = password
        self._session = aiohttp.ClientSession()
        self._sessionId = None
        self._logger = logger

        # Constants for D+ systems
        self._topSurroundingId = '187'
        self._environmentSurroundingName = '_DPAD_PRODUCT_K3_MENU_ENVIRONMENTS'
        self._systemOwner = 'SYSTEM'

    async def get_devices(self) -> list[DeviceDto]:
        topJson = await self._get_surroundings(self._topSurroundingId)

        self._logger.info("Retrieved top surroundings")
        environmentSurroundingId = next(x['ID'] for x in topJson['getObjsFromId']['data'].values() if x['NAME'] == self._environmentSurroundingName)
        environmentXml = await self._get_surroundings(environmentSurroundingId)
        devices = list[DeviceDto]()
        for room in filter(lambda x: x['OWNED_BY'] != self._systemOwner, environmentXml['getObjsFromId']['data'].values()):
            roomId = room['ID']
            deviceJson = await self._get_surroundings(roomId)
            for deviceJson in filter(lambda x: x['OWNED_BY'] != self._systemOwner and x['ID'] != roomId, deviceJson['getObjsFromId']['data'].values()):
                deviceSubElementsJson = await self._get_surroundings(deviceJson['ID'])
                deviceSubElements = list(filter(lambda x: x['OWNED_BY'] != self._systemOwner and x['ID'] != deviceJson['ID'], deviceSubElementsJson['getObjsFromId']['data'].values()))
                device = DeviceDto(
                    id=deviceJson['ID'],
                    parentId=roomId,
                    parentName=room['NAME'],
                    json=deviceJson,
                    subElements=deviceSubElements
                )
                devices.append(device)
        self._logger.info(f"Retrieved {len(devices)} devices")
        return devices

    async def get_states(self, device_id: list[str]) -> list[DeviceStateDto]:

        formData = {
            "args": "ID, CURRENT_VALUE",
            "src": "DPADD_OBJECT",
            "filter": "ID IN (" + ", ".join(device_id) + ")",
            "type": "SELECT",
            "context": "runtime",
            "sessionid": await self._getSessionId()
        }

        async with self._session.post(self._base + "www/modules/system/api.php", data=urlencode(formData), headers={"Content-Type": "application/x-www-form-urlencoded"}) as r:
            response = await r.text()

            xml = ET.fromstring(response)
            payload = xml.find(".//payload")
            data = payload.text if payload is not None else None
            if data:
                rows = data.splitlines()
                rows = list(filter(lambda x: x.strip() != "" and x.startswith("Row"), rows))[1:]
                states = []
                for row in rows:
                    row = row.strip()
                    row = row[row.index(":") + 1:].strip()
                    parts = row.split(",")
                    if len(parts) >= 2:
                        states.append(DeviceStateDto(id=parts[0].strip("'"), current_value=parts[1].strip("'")))
                self._logger.info(f"Retrieved {len(states)} device states")
                return states

            return None

    async def set_value(self, device_id: str, value: str):

        xml_value = f'''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <service-runonelement xmlns="urn:xmethods-dpadws">
      <payload>{value}</payload>
      <hashcode>NO-HASHCODE</hashcode>
      <optionals>NO-OPTIONALS</optionals>
      <callsource>WEB-DOMUSPAD_SOAP</callsource>
      <sessionid>{await self._getSessionId()}</sessionid>
      <waittime>10</waittime>
      <idobject>{device_id}</idobject>
      <operation>SETVALUE</operation>
    </service-runonelement>
  </soapenv:Body>
</soapenv:Envelope>'''

        async with self._session.post(self._base + f"/cgi-bin/dpadws", data=xml_value, headers={"Content-Type": "text/xml"}) as r:
            self._logger.info(f"Set value for device {device_id} to {value}")
            return await r.text()
        
    async def _get_surroundings(self, surrounding_id):
        formData = {
            "ids": surrounding_id,
            "filter": "",
            "order": "ORDER_NUM,ID",
            "limit": "",
            "context": "runtime",
            "sessionId": await self._getSessionId()
        }
        
        async with self._session.post(self._base + "www/modules/system/surrounding.php", data=urlencode(formData), headers={"Content-Type": "application/x-www-form-urlencoded"}) as r:
            return await r.json()
    
    async def _getSessionId(self):

        if(self._sessionId):
            return self._sessionId

        formData = {
            "username": self._username,
            "password": self._password,
            "context": "runtime",
            "op": "login"
        }

        #text = urlencode(formData)
        #self._logger.debug(f"Logging in with data: {text}")
        async with self._session.post(self._base + "www/modules/system/user_login.php", data=formData, headers={"Content-Type": "application/x-www-form-urlencoded"}) as resp:
            text = await resp.text()
            xml = ET.fromstring(text)
            sessionId = xml.find("./sessionid")
            if sessionId is not None:
                self._sessionId = sessionId.text
                self._logger.debug(f"Login successful")
                return self._sessionId
            else:
                self._logger.error("Login failed")
                raise Exception("Login failed")
