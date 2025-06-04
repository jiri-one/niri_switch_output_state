import json
import pytest


# filepath: .test_niri_switch_output_state.py
from niri_switch_output_state import OutputSwitcher


class MockSocket:
    def __init__(self, *args: list, **kwargs: dict):
        self.return_buffer: dict[str, bytes] = dict(
            return_value = b'{"Ok": {"Outputs": {"HDMI-A-1": {"current_mode": "On"}}}}',
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


def test_connect_to_niri_socket_success(monkeypatch, output_switcher):
    """Test successful connection to NIRI socket with all questions/actions."""
    for action in [output_switcher.OUTPUT_ACTION_ON, output_switcher.OUTPUT_ACTION_OFF]:
        monkeypatch.setattr("niri_switch_output_state.socket.socket", MockSocket)
        result_info, result_content = output_switcher.connect_to_niri_socket(action)
        assert result_info == "OK"
        assert "Outputs" in result_content


def test_connect_to_niri_socket_json_error(monkeypatch, output_switcher):
    class MockSocketForError(MockSocket):
        def __init__(self, *args: list, **kwargs: dict):
            self.return_buffer: dict[str, bytes] = dict(
                return_value = b'invalid json',
            )
    monkeypatch.setattr("niri_switch_output_state.socket.socket", MockSocketForError)
       
    with pytest.raises(SystemExit):
        output_switcher.connect_to_niri_socket(output_switcher.OUTPUTS)



# class TestNiriSwitchOutputState(unittest.TestCase):

#     @patch("niri_switch_output_state.socket.socket")
#     @patch("niri_switch_output_state.json.loads")
#     def test_connect_to_niri_socket_success(self, mock_json_loads, mock_socket):
#         # Mock socket behavior
#         mock_socket_instance = MagicMock()
#         mock_socket.return_value.__enter__.return_value = mock_socket_instance
#         mock_socket_instance.recv.side_effect = [b'{"Ok": {"Outputs": {"HDMI-A-1": {"current_mode": "On"}}}}', b'']
        
#         # Mock JSON decoding
#         mock_json_loads.return_value = {"Ok": {"Outputs": {"HDMI-A-1": {"current_mode": "On"}}}}
        
#         result_info, result_content = connect_to_niri_socket(OUTPUTS)
#         self.assertEqual(result_info, "OK")
#         self.assertIn("Outputs", result_content)

#     @patch("niri_switch_output_state.socket.socket")
#     @patch("niri_switch_output_state.json.loads")
#     def test_connect_to_niri_socket_json_error(self, mock_json_loads, mock_socket):
#         # Mock socket behavior
#         mock_socket_instance = MagicMock()
#         mock_socket.return_value.__enter__.return_value = mock_socket_instance
#         mock_socket_instance.recv.side_effect = [b'invalid json', b'']
        
#         # Mock JSON decoding to raise an error
#         mock_json_loads.side_effect = json.JSONDecodeError("Expecting value", "", 0)
        
#         with self.assertRaises(SystemExit):
#             connect_to_niri_socket(OUTPUTS)

#     @patch("niri_switch_output_state.connect_to_niri_socket")
#     def test_get_hdmi_monitor_state_success(self, mock_connect_to_niri_socket):
#         # Mock successful response from connect_to_niri_socket
#         mock_connect_to_niri_socket.return_value = ("OK", {"Outputs": {"HDMI-A-1": {"current_mode": "On"}}})
        
#         state = get_hdmi_monitor_state()
#         self.assertTrue(state)

#     @patch("niri_switch_output_state.connect_to_niri_socket")
#     def test_get_hdmi_monitor_state_failure(self, mock_connect_to_niri_socket):
#         # Mock failure response from connect_to_niri_socket
#         mock_connect_to_niri_socket.return_value = ("ERROR", {})
        
#         state = get_hdmi_monitor_state()
#         self.assertIsNone(state)

#     @patch("niri_switch_output_state.connect_to_niri_socket")
#     @patch("niri_switch_output_state.hdmi_switch_error")
#     def test_main_hdmi_on(self, mock_hdmi_switch_error, mock_connect_to_niri_socket):
#         # Mock monitor state as ON
#         mock_connect_to_niri_socket.side_effect = [
#             ("OK", {"Outputs": {"HDMI-A-1": {"current_mode": "On"}}}),
#             ("OK", {})
#         ]
        
#         main()
#         mock_connect_to_niri_socket.assert_called_with(OUTPUT_ACTION_OFF)

#     @patch("niri_switch_output_state.connect_to_niri_socket")
#     @patch("niri_switch_output_state.hdmi_switch_error")
#     def test_main_hdmi_off(self, mock_hdmi_switch_error, mock_connect_to_niri_socket):
#         # Mock monitor state as OFF
#         mock_connect_to_niri_socket.side_effect = [
#             ("OK", {"Outputs": {"HDMI-A-1": {"current_mode": None}}}),
#             ("OK", {})
#         ]
        
#         main()
#         mock_connect_to_niri_socket.assert_called_with(OUTPUT_ACTION_ON)

#     @patch("niri_switch_output_state.connect_to_niri_socket")
#     @patch("niri_switch_output_state.hdmi_switch_error")
#     def test_main_error(self, mock_hdmi_switch_error, mock_connect_to_niri_socket):
#         # Mock monitor state retrieval failure
#         mock_connect_to_niri_socket.return_value = ("ERROR", {})
        
#         with self.assertRaises(SystemExit):
#             main()
#         mock_hdmi_switch_error.assert_called_once_with("Some error occurred, see log for more details.")

# if __name__ == "__main__":
#     unittest.main()
