"""Tests for message handlers."""

import logging
from unittest.mock import MagicMock


from satel_integra.commands import SatelReadCommand
from satel_integra.satel_integra import AlarmState
from satel_integra.handlers.zones import zones_violated
from satel_integra.handlers.outputs import outputs_state
from satel_integra.handlers.partitions import partitions_armed_state
from satel_integra.handlers.result import command_result
from satel_integra.handlers import registry


def test_zones_violated_handler(satel):
    """Test zones_violated handler processes zone violations correctly."""
    msg = MagicMock()
    msg.get_active_bits.return_value = [1]

    called = {}
    satel.register_callbacks(zone_changed_callback=lambda status: called.update(status))

    zones_violated(satel, msg)

    assert called == {1: 1, 2: 0}
    assert satel.violated_zones == [1]


def test_zones_violated_handler_no_violations(satel):
    """Test zones_violated handler when no zones are violated."""
    msg = MagicMock()
    msg.get_active_bits.return_value = []

    called = {}
    satel.register_callbacks(zone_changed_callback=lambda status: called.update(status))

    zones_violated(satel, msg)

    assert called == {1: 0, 2: 0}
    assert satel.violated_zones == []


def test_outputs_state_handler(satel):
    """Test outputs_state handler processes output state changes."""
    msg = MagicMock()
    msg.get_active_bits.return_value = [4]

    called = {}
    satel.register_callbacks(
        output_changed_callback=lambda status: called.update(status)
    )

    outputs_state(satel, msg)

    assert called == {3: 0, 4: 1}
    assert satel.violated_outputs == [4]


def test_outputs_state_handler_no_outputs(satel):
    """Test outputs_state handler when no outputs are active."""
    msg = MagicMock()
    msg.get_active_bits.return_value = []

    called = {}
    satel.register_callbacks(
        output_changed_callback=lambda status: called.update(status)
    )

    outputs_state(satel, msg)

    assert called == {3: 0, 4: 0}
    assert satel.violated_outputs == []


def test_partitions_armed_state_handler(satel):
    """Test partitions_armed_state handler updates partition states."""
    msg = MagicMock()
    msg.get_active_bits.return_value = [1]
    msg.cmd = SatelReadCommand.PARTITIONS_ARMED_MODE0

    called = False

    def set_called():
        nonlocal called
        called = True

    satel.register_callbacks(alarm_status_callback=set_called)

    partitions_armed_state(satel, msg)

    assert satel.partition_states[AlarmState.ARMED_MODE0] == [1]
    assert called


def test_partitions_armed_state_handler_multiple_modes(satel):
    """Test partitions_armed_state handler with different partition modes."""
    msg = MagicMock()
    msg.get_active_bits.return_value = [1, 2]
    msg.cmd = SatelReadCommand.PARTITIONS_ARMED_MODE1

    satel.register_callbacks(alarm_status_callback=MagicMock())

    partitions_armed_state(satel, msg)

    assert satel.partition_states[AlarmState.ARMED_MODE1] == [1, 2]


def test_command_result_handler_success(satel, caplog):
    """Test command_result handler with success status."""
    msg = MagicMock()
    msg.msg_data = b"\xff"

    with caplog.at_level(logging.DEBUG):
        command_result(satel, msg)

    assert "COMMAND_ACCEPTED" in caplog.text


def test_command_result_handler_ok(satel, caplog):
    """Test command_result handler with OK status."""
    msg = MagicMock()
    msg.msg_data = b"\x00"

    with caplog.at_level(logging.DEBUG):
        command_result(satel, msg)

    assert "OK" in caplog.text


def test_zones_violated_handler_registered():
    """Test that zones_violated handler is registered in the registry."""
    assert registry.has_handler(SatelReadCommand.ZONES_VIOLATED)


def test_outputs_state_handler_registered():
    """Test that outputs_state handler is registered in the registry."""
    assert registry.has_handler(SatelReadCommand.OUTPUTS_STATE)


def test_command_result_handler_registered():
    """Test that command_result handler is registered in the registry."""
    assert registry.has_handler(SatelReadCommand.RESULT)


def test_partition_handlers_registered():
    """Test that all partition handlers are registered."""
    partition_commands = [
        SatelReadCommand.PARTITIONS_ARMED_MODE0,
        SatelReadCommand.PARTITIONS_ARMED_MODE1,
        SatelReadCommand.PARTITIONS_ARMED_MODE2,
        SatelReadCommand.PARTITIONS_ARMED_MODE3,
        SatelReadCommand.PARTITIONS_ARMED_SUPPRESSED,
        SatelReadCommand.PARTITIONS_ENTRY_TIME,
        SatelReadCommand.PARTITIONS_EXIT_COUNTDOWN_OVER_10,
        SatelReadCommand.PARTITIONS_EXIT_COUNTDOWN_UNDER_10,
        SatelReadCommand.PARTITIONS_ALARM,
        SatelReadCommand.PARTITIONS_FIRE_ALARM,
    ]

    for cmd in partition_commands:
        assert registry.has_handler(cmd), f"Handler not registered for {cmd}"
