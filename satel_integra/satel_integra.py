# ruff: noqa
"""Main module."""

import asyncio
import logging
from enum import Enum, unique
from typing import TYPE_CHECKING

from satel_integra.connection import SatelConnection
from satel_integra.message import SatelReadMessage, SatelWriteMessage
from satel_integra.state import AlarmState
from satel_integra.utils import encode_bitmask_le

from .command import SatelReadCommand, SatelResultCode, SatelWriteCommand

if TYPE_CHECKING:
    from collections.abc import Callable

_LOGGER = logging.getLogger(__name__)


class AsyncSatel:
    """Asynchronous interface to talk to Satel Integra alarm system."""

    def __init__(
        self,
        host: str,
        port: int,
        loop,
        monitored_zones: list[int] = [],
        monitored_outputs: list[int] = [],
        partitions: list[int] = [],
    ) -> None:
        """Init the Satel alarm data."""
        self._host = host
        self._port = port
        self._loop = loop
        self._monitored_zones = monitored_zones
        self._monitored_outputs = monitored_outputs
        self._partitions = partitions
        self.violated_zones: list[int] = []
        self.violated_outputs: list[int] = []
        self.partition_states: dict[AlarmState, list[int]] = {}

        self._connection = SatelConnection(host, port)

        self._keep_alive_timeout = 20
        self._reconnection_timeout = 15

        self._alarm_status_callback: Callable[[], None] | None = None
        self._zone_changed_callback: Callable[[dict[int, bool]], None] | None = None
        self._output_changed_callback: Callable[[dict[int, bool]], None] | None = None
        self._command_status_event = asyncio.Event()
        self._command_status = False

        self._message_handlers: dict[
            SatelReadCommand, Callable[[SatelReadMessage], None]
        ] = {
            SatelReadCommand.ZONES_VIOLATED: self._zones_violated,
            SatelReadCommand.PARTITIONS_ARMED_SUPPRESSED: lambda msg: self._partitions_armed_state(
                AlarmState.ARMED_SUPPRESSED, msg
            ),
            SatelReadCommand.PARTITIONS_ARMED_MODE0: lambda msg: self._partitions_armed_state(
                AlarmState.ARMED_MODE0, msg
            ),
            SatelReadCommand.PARTITIONS_ARMED_MODE2: lambda msg: self._partitions_armed_state(
                AlarmState.ARMED_MODE2, msg
            ),
            SatelReadCommand.PARTITIONS_ARMED_MODE3: lambda msg: self._partitions_armed_state(
                AlarmState.ARMED_MODE3, msg
            ),
            SatelReadCommand.PARTITIONS_ENTRY_TIME: lambda msg: self._partitions_armed_state(
                AlarmState.ENTRY_TIME, msg
            ),
            SatelReadCommand.PARTITIONS_EXIT_COUNTDOWN_OVER_10: lambda msg: self._partitions_armed_state(
                AlarmState.EXIT_COUNTDOWN_OVER_10, msg
            ),
            SatelReadCommand.PARTITIONS_EXIT_COUNTDOWN_UNDER_10: lambda msg: self._partitions_armed_state(
                AlarmState.EXIT_COUNTDOWN_UNDER_10, msg
            ),
            SatelReadCommand.PARTITIONS_ALARM: lambda msg: self._partitions_armed_state(
                AlarmState.TRIGGERED, msg
            ),
            SatelReadCommand.PARTITIONS_FIRE_ALARM: lambda msg: self._partitions_armed_state(
                AlarmState.TRIGGERED_FIRE, msg
            ),
            SatelReadCommand.OUTPUTS_STATE: self._outputs_changed,
            SatelReadCommand.PARTITIONS_ARMED_MODE1: lambda msg: self._partitions_armed_state(
                AlarmState.ARMED_MODE1, msg
            ),
            SatelReadCommand.RESULT: self._command_result,
        }

    @property
    def connected(self) -> bool:
        """Return true if there is connection to the alarm."""
        return self._connection.connected

    @property
    def closed(self) -> bool:
        """Return true if connection is closed."""
        return self._connection.closed

    async def connect(self) -> bool:
        """Make a TCP connection to the alarm system."""

        return await self._connection.connect()

    async def start_monitoring(self) -> None:
        """Start monitoring for interesting events."""
        monitored_commands = [
            SatelReadCommand.ZONES_VIOLATED,
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
            SatelReadCommand.OUTPUTS_STATE,
        ]
        monitored_commands_bitmask = encode_bitmask_le(
            [cmd.value + 1 for cmd in monitored_commands], 12
        )

        message = SatelWriteMessage(
            SatelWriteCommand.START_MONITORING,
            raw_data=bytearray(monitored_commands_bitmask),
        )

        await self._send_data(message)

        msg = await self._read_data()

        if msg is None or msg.cmd != SatelResultCode.COMMAND_ACCEPTED:
            _LOGGER.warning("Monitoring not accepted...")
            # TODO: Probably throw an error or something
        else:
            _LOGGER.warning("Monitoring not accepted.")

    def _zones_violated(self, msg: SatelReadMessage) -> None:
        """Message handler for zones violated message."""
        status: dict[int, bool] = {}

        violated_zones = msg.get_active_bits(32)
        self.violated_zones = violated_zones
        _LOGGER.debug("Violated zones: %s", violated_zones)
        for zone in self._monitored_zones:
            status[zone] = True if zone in violated_zones else False

        _LOGGER.debug("Returning status: %s", status)

        if self._zone_changed_callback:
            self._zone_changed_callback(status)

    def _outputs_changed(self, msg: SatelReadMessage) -> None:
        """Message handler for outputs state message."""
        status: dict[int, bool] = {}

        output_states = msg.get_active_bits(32)
        self.violated_outputs = output_states
        _LOGGER.debug("Output states: %s", output_states)
        for output in self._monitored_outputs:
            status[output] = True if output in output_states else False

        _LOGGER.debug("Returning status: %s", status)

        if self._output_changed_callback:
            self._output_changed_callback(status)

    def _partitions_armed_state(self, mode: AlarmState, msg: SatelReadMessage) -> None:
        """Message handler for partitions armed state messages."""
        partitions = msg.get_active_bits(4)

        _LOGGER.debug("Partitions in mode %s: %s", mode, partitions)

        self.partition_states[mode] = partitions

        if self._alarm_status_callback:
            self._alarm_status_callback()

    def _command_result(self, msg: SatelReadMessage) -> None:
        status = {"error": "Some problem!"}
        error_code = msg.msg_data

        if error_code in [b"\x00", b"\xff"]:
            status = {"error": "OK"}
        elif error_code == b"\x01":
            status = {"error": "User code not found"}

        _LOGGER.debug("Received error status: %s", status)
        self._command_status = status
        self._command_status_event.set()
        # return status

    # async def send_and_wait_for_answer(self, data):
    #     """Send given data and wait for confirmation from Satel"""
    #     await self._send_data(data)
    #     try:
    #         await asyncio.wait_for(self._command_status_event.wait(),
    #                                timeout=5)
    #     except asyncio.TimeoutError:
    #         _LOGGER.warning("Timeout waiting for response from Satel!")
    #     return self._command_status

    async def _send_data(self, msg: SatelWriteMessage) -> bool:
        """Send message to the alarm."""
        _LOGGER.debug("Sending command: %s", msg)
        data = msg.encode_frame()

        return await self._connection.send_frame(data)

    async def arm(self, code: str, partition_list: list[int], mode=0) -> None:
        """Send arming command to the alarm. Modes allowed: from 0 till 3."""
        _LOGGER.info("Sending arm command, mode: %s", mode)

        mode_command = SatelWriteCommand(SatelWriteCommand.PARTITIONS_ARM_MODE_0 + mode)

        message = SatelWriteMessage(mode_command, code=code, partitions=partition_list)

        await self._send_data(message)

    async def disarm(self, code: str, partition_list: list[int]) -> None:
        """Send command to disarm."""
        _LOGGER.info("Sending disarm command")

        message = SatelWriteMessage(
            SatelWriteCommand.PARTITIONS_DISARM,
            code=code,
            partitions=partition_list,
        )

        await self._send_data(message)

    async def clear_alarm(self, code: str, partition_list: list[int]) -> None:
        """Send command to clear the alarm."""
        _LOGGER.info("Sending clear the alarm command")

        message = SatelWriteMessage(
            SatelWriteCommand.PARTITIONS_CLEAR_ALARM,
            code=code,
            partitions=partition_list,
        )

        await self._send_data(message)

    async def set_output(self, code: str, output_list: list[int], state: bool) -> None:
        """Send output turn on command to the alarm."""
        _LOGGER.info("Turn %s, output: %s", "on" if state else "off", output_list)

        mode_command = (
            SatelWriteCommand.OUTPUTS_ON if state else SatelWriteCommand.OUTPUTS_OFF
        )

        message = SatelWriteMessage(mode_command, code=code, outputs=output_list)

        await self._send_data(message)

    async def _read_data(self) -> SatelReadMessage | None:
        """Read data from the alarm."""

        data = await self._connection.read_frame()

        if data is None:
            _LOGGER.warning("Read data failed, probably disconnected.")
            return

        msg = SatelReadMessage.decode_frame(data)

        if msg and isinstance(msg, SatelReadMessage):
            _LOGGER.debug("Received command: %s", msg)
            return msg
        else:
            _LOGGER.warning("Failed to decode message!")
            return

    async def keep_alive(self) -> None:
        """A workaround for Satel Integra disconnecting after 25s.

        Every interval it sends some random question to the device, ignoring
        answer - just to keep connection alive.
        """
        # while True:
        #     await asyncio.sleep(self._keep_alive_timeout)
        #     if self.closed:
        #         return
        #     # Command to read status of the alarm
        #     data = generate_query(b"\xee\x01\x01")
        #     await self._send_data(data)

    async def _update_status(self) -> None:
        _LOGGER.debug("Wait...")

        msg = await self._read_data()

        if msg is None:
            return

        if msg.cmd in self._message_handlers:
            _LOGGER.info("Calling handler for command: %s", msg.cmd)
            self._message_handlers[msg.cmd](msg)
        else:
            _LOGGER.info("No handler for command: %s", msg.cmd)

    async def monitor_status(
        self,
        alarm_status_callback=None,
        zone_changed_callback=None,
        output_changed_callback=None,
    ) -> None:
        """Start monitoring of the alarm status.

        Send command to satel integra to start sending updates. Read in a
        loop and call respective callbacks when received messages.
        """
        self._alarm_status_callback = alarm_status_callback
        self._zone_changed_callback = zone_changed_callback
        self._output_changed_callback = output_changed_callback

        _LOGGER.info("Starting monitor_status loop")

        while not self.closed:
            await self._connection.ensure_connected()

            await self.start_monitoring()

            while self.connected and not self.closed:
                await self._update_status()

            await asyncio.sleep(self._reconnection_timeout)

        _LOGGER.info("Closed, quit monitoring.")

    async def disconnect(self) -> None:
        """Gracefully disconnect the Satel panel connection."""
        if self._connection:
            await self._connection.close()
