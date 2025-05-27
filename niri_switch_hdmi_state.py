import socket
from os import getenv
import json
from functools import wraps, partial
import subprocess
import logging
from typing import Any


# constants
HDMI_NAME = "HDMI-A-1"
HDMI_ACTION_ON = json.dumps({"Output":{"output":HDMI_NAME,"action":"On"}}).encode()
HDMI_ACTION_OFF = json.dumps({"Output":{"output":HDMI_NAME,"action":"Off"}}).encode()
OUTPUTS = json.dumps("Outputs").encode()
NIRI_SOCKET = getenv("NIRI_SOCKET")

# logger
logger = logging.getLogger("niri_hdmi_state_switcher")


if not NIRI_SOCKET:
    logger.error("NIRI_SOCKET was not found.")
    exit(1)

# helper functions
def send_desktop_notification_and_log(title: str, text: str):
    """This function will send text to desktop notification area and log it to console like error message."""
    subprocess.run(
        ["notify-send",
         "-u",
         "normal",
         "-t",
         "3000",
         title,
         text,
        ],
        check = True,
    )
    logger.error(f"{title}: {text}")

hdmi_switch_error = partial(send_desktop_notification_and_log, "HDMI SWITCH ERROR")


def check_action_return_values(func):
    @wraps(func)
    def wrapper(*args, **kwargs) -> tuple:
        result_info, result_content = func(*args, **kwargs)

        if "ERROR" in result_info:
            hdmi_switch_error(str(result_content))
            return result_info, result_content
        
        # check, if anything went OK
        if isinstance(result_content, dict):
            try:
                output_config_msg = result_content["OutputConfigChanged"]
                if output_config_msg == "Applied":
                    # no need to do anything, monitor will turn on
                    pass
                elif output_config_msg == "OutputWasMissing":
                    hdmi_switch_error(output_config_msg)
            except KeyError:
                # we will check only results with OutputConfigChanged output
                pass
        return result_info, result_content
        
    return wrapper


@check_action_return_values
def connect_to_niri_socket(cmd: bytes) -> tuple[str, Any]:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as socket_client:
        assert NIRI_SOCKET is not None
        socket_client.connect(NIRI_SOCKET)
        socket_client.send(cmd)
        socket_client.send("\n".encode()) # send new line is demanded
        result_bytes = b""
        while part_bytes := socket_client.recv(1024): # receive 1024 bytes
            result_bytes += part_bytes

    try:
        result: dict = json.loads(result_bytes)
    except json.JSONDecodeError as ex:
        hdmi_switch_error(f"We weren't able to decode data from NIRI socket:\n{ex}")
        exit(1)
    
    if "Ok" in result:
        result_content = result.get("Ok")
        result_info = "OK"
    elif "Err" in result:
        result_content = result.get("Err")
        result_info = "ERROR"
    else:
        result_content = result
        result_info = "UNKNOWN ERROR"
    return result_info, result_content


def get_hdmi_monitor_state() -> bool | None:
    result_info, result_content = connect_to_niri_socket(OUTPUTS)
    if result_info != "OK":
        return None
    else:
        try:
            current_mode = result_content.get("Outputs").get(HDMI_NAME).get("current_mode")
            if current_mode is not None:
                return True
            else:
                return False
        except AttributeError:
            return None


def main()->None:
    hdmi_turned_on: bool | None = get_hdmi_monitor_state()
    if hdmi_turned_on is True:
        result_info, result_content = connect_to_niri_socket(HDMI_ACTION_OFF)
    elif hdmi_turned_on is False:
        result_info, result_content = connect_to_niri_socket(HDMI_ACTION_ON)
    

if __name__ == "__main__":
    main()
