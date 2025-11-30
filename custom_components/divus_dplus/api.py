import aiohttp

class DivusDplusApi:
    def __init__(self, host, username, password):
        self._base = f"http://{host}/api/"
        self._username = username
        self._password = password
        self._session = aiohttp.ClientSession()

    async def get_devices(self):
        async with self._session.get(self._base + "devices") as r:
            return await r.json()

    async def get_state(self, device_id):
        async with self._session.get(self._base + f"device/{device_id}/state") as r:
            return await r.json()

    async def set_state(self, device_id, value):
        async with self._session.post(self._base + f"device/{device_id}/set", json=value) as r:
            return await r.json()
