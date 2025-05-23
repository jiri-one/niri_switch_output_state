import socket
from os import getenv
import json

# constants
HDMI_NAME = "HDMI-A-1"
HDMI_ACTION_ON = json.dumps({"Output":{"output":HDMI_NAME,"action":"On"}}).encode()
HDMI_ACTION_OFF = json.dumps({"Output":{"output":HDMI_NAME,"action":"Off"}}).encode()
OUTPUTS = json.dumps("Outputs").encode()
NIRI_SOCKET = getenv("NIRI_SOCKET")

if not NIRI_SOCKET:
    # TODO: show user some info (use niri msg)
    exit()

def connect_to_niri_socket(action: str):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as socket_client:
        socket_client.connect(NIRI_SOCKET)
        socket_client.send(action)
        socket_client.send("\n".encode()) # send new line is demanded
        result_bytes = b""
        while part_bytes := socket_client.recv(1024): # receive 1024 bytes
            result_bytes += part_bytes

    try:
        result: dict = json.loads(result_bytes)
    except json.JSONDecodeError as e:
        # TODO: show user some info (use niri msg)
        ...
    if "Ok" in result:
        result_content = result.get("Ok")
        result_info = "OK"
    elif "Err" in result:
        result_content = result.get("Err")
        result_info = "ERROR"
    else:
        # TODO: show user some info (use niri msg)
        result_content = result
        result_info = "UNKNOWN ERROR"
    return result_info, result_content

    # if isinstance(result_content, dict):
    #     output_config_msg: str | None = result_content.get("OutputConfigChanged")
    #     if output_config_msg == "Applied":
    #         # no need to do anything, monitor will turn on
    #         pass
    #     elif output_config_msg == "OutputWasMissing":
    #         # TODO: show user some info (use niri msg)
    #         ...
    #     else:
    #         # TODO: show user some info (use niri msg)
    #         ...

    # print(result_info, result_content)


def get_hdmi_monitor_state() -> bool | None:
    result_info, result_content = connect_to_niri_socket(OUTPUTS)
    if result_info != "OK":
        return
    else:
        try:
            current_mode = result_content.get("Outputs").get(HDMI_NAME).get("current_mode")
            if current_mode is not None:
                return True
            else:
                return False
        except AttributeError:
            return

def main():
    hdmi_turned_on: bool | None = get_hdmi_monitor_state()
    if hdmi_turned_on is True:
        connect_to_niri_socket(HDMI_ACTION_OFF)
    elif hdmi_turned_on is False:
        connect_to_niri_socket(HDMI_ACTION_ON)

if __name__ == "__main__":
    main()
     