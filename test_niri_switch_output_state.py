import pytest
import json


# filepath: .test_niri_switch_output_state.py
from niri_switch_output_state import OutputSwitcher

NIRI_RESULT_OK = b'{"Ok":{"Outputs":{"HDMI-A-1":{"current_mode":"On"}}}}'
NIRI_RESULT_ERR = b'{"Err":"Some error occurred"}'
NIRI_RESULT_U_ERR = b'"Some unknown error occurred"'
NIRI_OUTPUT_RESULT = b'''
{"Ok": {"Outputs": {"HDMI-A-1": {"name": "HDMI-A-1", "make": "Eizo Nanao Corporation", "model": "EV2785", "serial": "0x019FBA10", "physical_size": [
                    600,
                    340
                ], "modes": [
                    {"width": 3840, "height": 2160, "refresh_rate": 60000, "is_preferred": true
                    }
                ], "current_mode": null, "vrr_supported": false, "vrr_enabled": false, "logical": null
            }, "DP-1": {"name": "DP-1", "make": "PNP(OBX)", "model": "MIRA253", "serial": "BOOX MIRA253", "physical_size": [
                    560,
                    320
                ], "modes": [
                    {"width": 3200, "height": 1800, "refresh_rate": 29998, "is_preferred": true
                    }
                ], "current_mode": 0, "vrr_supported": false, "vrr_enabled": false, "logical": {"x": 1920, "y": 1100, "width": 1600, "height": 900, "scale": 2.0, "transform": "Normal"
                }
            }
        }
    }
}
'''


class MockSocket:
    def __init__(self, *args: list, **kwargs: dict):
        self.return_buffer: dict[str, bytes] = dict(
            return_value = NIRI_RESULT_OK,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def connect(self, address):
        pass

    def sendall(self, data):
        pass

    def recv(self, bufsize):
        return self.return_buffer.pop("return_value", None)
    
    def send(self, data):
        pass


@pytest.fixture
def output_switcher():
    return OutputSwitcher()


@pytest.mark.parametrize(("action, expected_result_info, raw_result"), [
    pytest.param(
        OutputSwitcher.OUTPUT_ACTION_ON,
        "OK",
        NIRI_RESULT_OK,
        id="output_action_on"),
    pytest.param(
        OutputSwitcher.OUTPUT_ACTION_OFF,
        "OK",
        NIRI_RESULT_OK,
        id="output_action_off"),
    pytest.param(
        OutputSwitcher.OUTPUTS,
        "OK",
        NIRI_OUTPUT_RESULT,
        id="outputs"),
    pytest.param(
        OutputSwitcher.OUTPUTS,
        "ERROR",
        NIRI_RESULT_ERR,
        id="niri_error"),
    pytest.param(
        OutputSwitcher.OUTPUTS,
        "UNKNOWN ERROR",
        NIRI_RESULT_U_ERR,
        id="niri_unknown_error"),
])
def test_connect_to_niri_socket_success(
    action, expected_result_info, raw_result, monkeypatch, output_switcher
):
    """Test successful connection to NIRI socket with all questions/actions."""
    class MockSocketMod(MockSocket):
        def __init__(self, *args: list, **kwargs: dict):
            self.return_buffer: dict[str, bytes] = dict(
                return_value = raw_result,
            )
    monkeypatch.setattr("niri_switch_output_state.socket.socket", MockSocketMod)
    result_info, result_content = output_switcher.connect_to_niri_socket(action)
    assert result_info == expected_result_info
    result = json.loads(raw_result)
    if isinstance(result, dict):
        assert result_content == list(result.values())[0]
    else:
        assert result_content == result


def test_connect_to_niri_socket_json_error(monkeypatch, output_switcher):
    class MockSocketForError(MockSocket):
        def __init__(self, *args: list, **kwargs: dict):
            self.return_buffer: dict[str, bytes] = dict(
                return_value = b'invalid json',
            )
    monkeypatch.setattr("niri_switch_output_state.socket.socket", MockSocketForError)
       
    with pytest.raises(SystemExit):
        output_switcher.connect_to_niri_socket(output_switcher.OUTPUTS)


def test_get_hdmi_monitor_state_success(monkeypatch, output_switcher):
    """Test successful retrieval of HDMI monitor state."""
    class MockSocketForState(MockSocket):
        def __init__(self, *args: list, **kwargs: dict):
            self.return_buffer: dict[str, bytes] = dict(
                return_value = NIRI_OUTPUT_RESULT,
            )
    monkeypatch.setattr("niri_switch_output_state.socket.socket", MockSocketForState)
    
    result_info, result_content = output_switcher.connect_to_niri_socket(output_switcher.OUTPUTS)
    assert result_info == "OK"
    assert result_content == json.loads(NIRI_OUTPUT_RESULT)["Ok"]

    assert output_switcher.get_hdmi_monitor_state() is False
