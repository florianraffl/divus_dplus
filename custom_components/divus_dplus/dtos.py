class DeviceDto:
    def __init__(self, id: str, parentId: str, parentName: str, json: dict, subElements: list):
        self.id = id
        self.parentId = parentId
        self.parentName = parentName
        self.json = json
        self.subElements = subElements

class DeviceStateDto:
    def __init__(self, id: str, current_value: str):
        self.id = id
        self.current_value = current_value