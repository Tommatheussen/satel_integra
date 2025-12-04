import asyncio
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from satel_integra.commands import SatelReadCommand
from satel_integra.handlers import registry


@pytest.mark.asyncio
async def test_start_monitoring_success(satel, mock_queue):
    mock_msg = MagicMock()
    mock_msg.msg_data = b"\xff"
    mock_queue.add_message.return_value = mock_msg

    await satel.start_monitoring()

    mock_queue.add_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_monitoring_rejected(satel, mock_queue, caplog):
    mock_msg = MagicMock()
    mock_msg.msg_data = b"\x00"
    mock_queue.add_message.return_value = mock_msg

    await satel.start_monitoring()

    assert "Monitoring not accepted" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,args",
    [
        ("arm", ("1234", [1], 0)),
        ("disarm", ("1234", [1])),
        ("clear_alarm", ("1234", [1])),
        ("set_output", ("1234", 3, True)),
    ],
)
async def test_send_methods_call_queue_add(satel, mock_queue, method, args):
    await getattr(satel, method)(*args)
    mock_queue.add_message.assert_awaited()


@pytest.mark.asyncio
async def test_close_cancels_tasks(satel):
    satel._reading_task = asyncio.create_task(asyncio.sleep(999))
    satel._keepalive_task = asyncio.create_task(asyncio.sleep(999))

    await satel.close()

    assert satel._reading_task is None
    assert satel._keepalive_task is None


@pytest.mark.asyncio
async def test_read_data_exception_returns_none(satel):
    satel._connection.read_frame.side_effect = Exception("boom")

    result = await satel._read_data()
    assert result is None


@pytest.mark.asyncio
async def test_start_starts_background_tasks(satel):
    satel._reading_task = None
    satel._keepalive_task = None

    satel._reading_loop = AsyncMock()
    satel._keepalive_loop = AsyncMock()
    satel.start_monitoring = AsyncMock()

    await satel.start(enable_monitoring=True)

    # Tasks are created
    assert satel._reading_task is not None
    assert satel._keepalive_task is not None

    # Monitoring called
    satel.start_monitoring.assert_awaited()


@pytest.mark.asyncio
async def test_start_skips_monitoring(satel):
    satel._reading_task = None
    satel._keepalive_task = None

    satel._reading_loop = AsyncMock()
    satel._keepalive_loop = AsyncMock()
    satel.start_monitoring = AsyncMock()

    await satel.start(enable_monitoring=False)

    satel.start_monitoring.assert_not_awaited()


@pytest.mark.asyncio
async def test_keepalive_loop_sends_message(satel):
    satel._keepalive_timeout = 0.01
    satel._send_data = AsyncMock()

    # Close after 1 call
    type(satel).closed = PropertyMock(side_effect=[False, True])

    await satel._keepalive_loop()

    satel._send_data.assert_called_once()


@pytest.mark.asyncio
async def test_reading_loop_processes_message(satel):
    type(satel).closed = PropertyMock(side_effect=[False, True])
    satel._queue.on_message_received = MagicMock()

    msg = MagicMock()
    msg.cmd = SatelReadCommand.ZONES_VIOLATED

    satel._read_data = AsyncMock(side_effect=[msg, None])  # Return one msg then None

    handler_spy = MagicMock()
    registry._handlers[SatelReadCommand.ZONES_VIOLATED] = handler_spy

    await satel._reading_loop()

    satel._queue.on_message_received.assert_called_once()
    handler_spy.assert_called_once_with(satel, msg)
