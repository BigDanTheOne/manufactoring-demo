import json
import logging
import time
from typing import Any

import requests

import config

logger = logging.getLogger(__name__)


def send_data(name: str, values: list[Any], timestamps: list[int] | None = None) -> None:
    if timestamps is None:
        if len(values) > 1:
            logger.error(f"Error sending {len(values)} without timestamps")
            return
        else:
            timestamps = [int(time.time() * 1000)]
    if len(values) != len(timestamps):
        logger.error(
            f"The number of values ({len(values)}) must be equal "
            f"to the number of timestamps ({len(timestamps)})"
        )
        return

    def _payload(name: str, values: list[Any], timestamps: list[int]) -> str:
        data = {"metric": {"__name__": name}, "values": values, "timestamps": timestamps}
        return json.dumps(data)

    payload = _payload(name, values, timestamps)
    logger.debug(f"Sending data: {payload}")
    if config.SEND_METRICS:
        response = requests.post(
            url=config.POST_URL, headers=config.POST_HEADERS, data=payload, timeout=20
        )
        logger.debug(f"Response status code: {response.status_code}, text: {response.text}")


def get_data(metric: str) -> Any:
    # params = {"match": f'__name__=~"{metric}"'}
    params = f'match={{__name__=~"{metric}"}}'
    try:
        response = requests.get(
            url=config.GET_URL, params=params, headers=config.GET_HEADERS, timeout=20
        )
        obj = json.loads(response.text)
    except Exception as err:
        logger.error("Error by getting metric '%s': %s", metric, str(err))
        logger.debug("Response status code: %s", response.status_code)
        logger.debug("Response text: %s", response.text)
        return
    else:
        return obj
