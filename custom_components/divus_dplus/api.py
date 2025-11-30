import aiohttp

class DivusDplusApi:
    def __init__(self, host, username, password):
        self._base = f"http://{host}//www/modules/system/"
        self._username = username
        self._password = password
        self._session = aiohttp.ClientSession()
        self._sessionId = None

        # Constants for D+ systems
        self._topSurroundingId = 187
        self._environmentSurroundingName = "_DPAD_PRODUCT_K3_MENU_ENVIRONMENTS"
        self._systemOwner = "SYSTEM"

    async def get_devices(self):
        async with self._get_surroundings(self._topSurroundingId) as topXml:

            environmentSurroundingId = topXml['getObjsFromId']['data'].filter(lambda x: x['NAME'] == self._environmentSurroundingName)['ID']
            async with self._get_surroundings(environmentSurroundingId) as environmentXml:
                devices = []
                for room in environmentXml['getObjsFromId']['data'].filter(lambda x: x['OWNED_BY'] == self._systemOwner):
                    roomId = room['ID']
                    async with self._get_surroundings(roomId) as deviceXml:
                        for device in deviceXml['getObjsFromId']['data']:
                            devices.append(device)
                return devices

    # async def get_state(self, device_id):
    #     async with self._session.get(self._base + f"device/{device_id}/state") as r:
    #         return await r.json()

    # async def set_state(self, device_id, value):
    #     async with self._session.post(self._base + f"device/{device_id}/set", json=value) as r:
    #         return await r.json()
        
    async def _get_surroundings(self, surrounding_id):
        formData = {
            "ids": surrounding_id,
            "filter": "",
            "order": "ORDER_NUM%2CID+",
            "limit": "",
            "context": "runtime",
            "sessionId": await self._getSessionId()
        }
        
        async with self._session.post(self._base + "surrounding.php", data=formData, headers={"Content-Type": "application/x-www-form-urlencoded"}) as r:
            return await r.xml()
    
    async def _getSessionId(self):

        if(self._sessionId):
            return self._sessionId

        formData = {
            "username": self._username,
            "password": self._password,
            "context": "runtime",
            "op": "login"
        }
        async with self._session.post(self._base + "login.php", data=formData) as r:
            xml = await r.xml()
            if "sessionId" in xml:
                self._sessionId = xml["sessionId"]
                return self._sessionId
            else:
                raise Exception("Login failed")
