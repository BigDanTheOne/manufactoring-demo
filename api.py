import json

from datetime import datetime
from pprint import pprint
from pydantic import ValidationError

from app.models import Plan_


class API:
    def __init__(self) -> None:
        self._json_file = open("fixtures/response.example.json", "r")

    def get_plan(self) -> Plan_:
        response = '{"orders": ' + self._json_file.read() + "}"
        try:
            result = Plan_.model_validate_json(response)
        except ValidationError as e:
            pprint(json.loads(e.json()))
        else:
            return result
