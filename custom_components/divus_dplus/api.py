import logging
from urllib.parse import urlencode

import aiohttp
from defusedxml import ElementTree

from custom_components.divus_dplus.dtos import DeviceDto, DeviceStateDto

_LOGGER = logging.getLogger(__name__)


class DivusDplusApi:
    def __init__(self, host: str, username: str, password: str) -> None:
        self._base = f"http://{host}/"
        self._username = username
        self._password = password
        self._session = aiohttp.ClientSession()
        self._session_id = None

        # Constants for D+ systems
        self._top_surrounding_id = "187"
        self._environment_surrounding_name = "_DPAD_PRODUCT_K3_MENU_ENVIRONMENTS"
        self._system_owner = "SYSTEM"
        self._minDevice_state_parts = 2

    async def get_devices(self) -> list[DeviceDto]:
        top_json = await self._get_surroundings(self._top_surrounding_id)

        _LOGGER.info("Retrieved top surroundings")
        environment_surrounding_id = next(
            x["ID"]
            for x in top_json["getObjsFromId"]["data"].values()
            if x["NAME"] == self._environment_surrounding_name
        )
        environment_xml = await self._get_surroundings(environment_surrounding_id)
        devices = list[DeviceDto]()
        for room in filter(
            lambda x: x["OWNED_BY"] != self._system_owner,
            environment_xml["getObjsFromId"]["data"].values(),
        ):
            room_id = room["ID"]
            devices_json = await self._get_surroundings(room_id)
            for device_json in filter(
                lambda x: x["OWNED_BY"] != self._system_owner and x["ID"] != room_id,
                devices_json["getObjsFromId"]["data"].values(),
            ):
                device_sub_elements_json = await self._get_surroundings(
                    device_json["ID"]
                )
                device_sub_elements = list(
                    filter(
                        lambda x: x["OWNED_BY"] != self._system_owner
                        and x["ID"] != device_json["ID"],
                        device_sub_elements_json["getObjsFromId"]["data"].values(),
                    )
                )
                device = DeviceDto(
                    device_id=device_json["ID"],
                    parent_id=room_id,
                    parent_name=room["NAME"],
                    json=device_json,
                    sub_elements=device_sub_elements,
                )
                devices.append(device)
        _LOGGER.info("Retrieved %d devices", len(devices))
        return devices

    async def get_states(self, device_id: list[str]) -> list[DeviceStateDto]:
        form_data = {
            "args": "ID, CURRENT_VALUE",
            "src": "DPADD_OBJECT",
            "filter": "ID IN (" + ", ".join(device_id) + ")",
            "type": "SELECT",
            "context": "runtime",
            "sessionid": await self._get_session_id(),
        }

        async with self._session.post(
            self._base + "www/modules/system/api.php",
            data=urlencode(form_data),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as r:
            response = await r.text()

            xml = ElementTree.fromstring(response)
            payload = xml.find(".//payload")
            data = payload.text if payload is not None else None
            if data:
                rows = data.splitlines()
                rows = list(
                    filter(lambda x: x.strip() != "" and x.startswith("Row"), rows)
                )[1:]
                states = []
                for full_row in rows:
                    row = full_row.strip()
                    row = row[row.index(":") + 1 :].strip()
                    parts = row.split(",")
                    if len(parts) >= self._minDevice_state_parts:
                        states.append(
                            DeviceStateDto(
                                device_id=parts[0].strip("'"),
                                current_value=parts[1].strip("'"),
                            )
                        )

                _LOGGER.info("Retrieved %d device states", len(states))
                return states

            return []

    async def set_value(self, device_id: str, value: str) -> str:
        xml_value = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <service-runonelement xmlns="urn:xmethods-dpadws">
      <payload>{value}</payload>
      <hashcode>NO-HASHCODE</hashcode>
      <optionals>NO-OPTIONALS</optionals>
      <callsource>WEB-DOMUSPAD_SOAP</callsource>
      <sessionid>{await self._get_session_id()}</sessionid>
      <waittime>10</waittime>
      <idobject>{device_id}</idobject>
      <operation>SETVALUE</operation>
    </service-runonelement>
  </soapenv:Body>
</soapenv:Envelope>"""

        async with self._session.post(
            self._base + "/cgi-bin/dpadws",
            data=xml_value,
            headers={"Content-Type": "text/xml"},
        ) as r:
            _LOGGER.info("Set value for device %s to %s", device_id, value)
            return await r.text()

    async def _get_surroundings(self, surrounding_id: str) -> dict:
        form_data = {
            "ids": surrounding_id,
            "filter": "",
            "order": "ORDER_NUM,ID",
            "limit": "",
            "context": "runtime",
            "sessionId": await self._get_session_id(),
        }

        async with self._session.post(
            self._base + "www/modules/system/surrounding.php",
            data=urlencode(form_data),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as r:
            return await r.json()

    async def _get_session_id(self) -> str:
        if self._session_id:
            return self._session_id

        form_data = {
            "username": self._username,
            "password": self._password,
            "context": "runtime",
            "op": "login",
        }

        async with self._session.post(
            self._base + "www/modules/system/user_login.php",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as resp:
            text = await resp.text()
            xml = ElementTree.fromstring(text)
            session_id_node = xml.find("./sessionid")
            if session_id_node is not None and session_id_node.text:
                self._session_id = session_id_node.text
                _LOGGER.debug("Login successful")
                return self._session_id
            _LOGGER.error("Login failed")
            msg = "Login failed"
            raise Exception(msg)  # noqa: TRY002
