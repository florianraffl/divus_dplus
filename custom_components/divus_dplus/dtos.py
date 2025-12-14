class DeviceDto:
    def __init__(
        self,
        device_id: str,
        parent_id: str,
        parent_name: str,
        json: dict,
        sub_elements: list,
    ) -> None:
        self.id = device_id
        self.parentId = parent_id
        self.parentName = parent_name
        self.json = json
        self.sub_elements = sub_elements


class DeviceStateDto:
    def __init__(self, device_id: str, current_value: str) -> None:
        self.id = device_id
        self.current_value = current_value
