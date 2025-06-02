import socket
from os import getenv
import json
from functools import wraps, partial
import subprocess
import logging
from typing import Any
import argparse

# logger
logger = logging.getLogger(__file__.split("/")[-1].rstrip(".py"))
# Create a logger andler
console_handler = logging.StreamHandler()
# link handler to logger
logger.addHandler(console_handler)
# Set the logging level for the handler
logger.setLevel(logging.INFO)

NIRI_SOCKET = getenv("NIRI_SOCKET")
# This script will not work without Niri WM
if not NIRI_SOCKET:
    logger.error("NIRI_SOCKET was not found.")
    exit(1)

DEFAULT_OUTPUT_NAME = "HDMI-A-1"

# helper functions
def notify_and_log(title: str, text: str):
    """This method will send text to desktop notification area and log it to console like error message."""
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

hdmi_switch_error = partial(notify_and_log, "HDMI SWITCH ERROR")

class OutputSwitcher:
    """This class is used to switch output state on or off."""
    OUTPUT_ACTION_ON = json.dumps({"Output":{"output":DEFAULT_OUTPUT_NAME,"action":"On"}}).encode()
    OUTPUT_ACTION_OFF = json.dumps({"Output":{"output":DEFAULT_OUTPUT_NAME,"action":"Off"}}).encode()
    OUTPUTS = json.dumps("Outputs").encode()

    def __init__(self, output_name: str = DEFAULT_OUTPUT_NAME):
        self.output_name = output_name

    @staticmethod
    def check_action_return_values(func):
        """Decorator to check return values of actions"""
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
    def connect_to_niri_socket(self, cmd: bytes) -> tuple[str, Any]:
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
        except json.JSONDecodeError:
            hdmi_switch_error("We weren't able to decode data from NIRI socket, see log for more details.")
            logger.exception("Decoding data from NIRI socket went wrong.")
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


    def get_hdmi_monitor_state(self) -> bool | None:
        result_info, result_content = self.connect_to_niri_socket(self.OUTPUTS)
        if result_info != "OK":
            return None
        else:
            try:
                outputs = result_content.get("Outputs")
            except AttributeError:
                logger.exception("Return value from NIRI_SOCKET doesn't include 'Outputs' key.")
                return None
            try:
                output_name = outputs.get(self.output_name)
            except AttributeError:
                logger.exception("The output name probably doesn't exists.")
                return None
            try:
                current_mode = output_name.get("current_mode")
            except AttributeError:
                logger.exception("It wasn't possible detect current output state.")
                return None
                
            if current_mode is not None:
                return True
            else:
                return False
    
    def __call__(self) -> None:
        hdmi_turned_on: bool | None = self.get_hdmi_monitor_state()
        if hdmi_turned_on is True:
            result_info, result_content = self.connect_to_niri_socket(self.OUTPUT_ACTION_OFF)
            logger.info(f"Output {self.output_name} was turned OFF.") 
        elif hdmi_turned_on is False:
            result_info, result_content = self.connect_to_niri_socket(self.OUTPUT_ACTION_ON)
            logger.info(f"Output {self.output_name} was turned ON.") 
        else:
            hdmi_switch_error("Some error occurred, see log for more details.")
            exit(1)


def main()->None:
    # command line argument parser
    parser = argparse.ArgumentParser(
                        prog='niri_switch_output_state',
                        description='Turn on the monitor if it is off and opposite',
                        epilog='This script will not work without Niri WM')
    parser.add_argument('-o', metavar="OUTPUT_NAME", default=DEFAULT_OUTPUT_NAME, required=False, help="Use name of output from 'niri msg outputs'")
    args = parser.parse_args()
    OUTPUT_NAME = args.o
    output_switcher = OutputSwitcher(output_name=OUTPUT_NAME)
    # call the output switcher will turn on or off the monitor
    output_switcher()
    


if __name__ == "__main__":
    main()
