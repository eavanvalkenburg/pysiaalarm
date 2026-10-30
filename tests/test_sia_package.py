# -*- coding: utf-8 -*-
"""Class for tests of pysiaalarm."""
import logging
import asyncio
import pytest
from dataclasses import asdict
from datetime import datetime, timezone

from pytest_cases import parametrize_with_cases, fixture
from unittest.mock import AsyncMock, Mock, patch

from pysiaalarm import (
    SIAAccount,
    SIAClient,
    SIAEvent,
)
from pysiaalarm.aio import SIAClient as SIAClientA
from pysiaalarm.aio.client import SIAClientTCP
from pysiaalarm.aio.server import SIAServerTCP, SIAServerUDP
from pysiaalarm.event import NAKEvent, BaseEvent
from pysiaalarm.const import (
    COUNTER_EVENTS,
    COUNTER_FORMAT,
    COUNTER_USER_CODE,
    COUNTER_VALID,
)
from pysiaalarm.errors import EventFormatError, NoAccountError
from pysiaalarm.sync.handler import SIATCPHandler, SIAUDPHandler
from pysiaalarm.utils import Counter

from tests.test_alarm import send_messages
from tests.test_utils import ACCOUNT, KEY, HOST, create_test_line, crc_calc
from tests.test_sia_package_cases import *  # pylint: disable=W0614


logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


class _FrozenDatetime(datetime):
    """Datetime with a fixed now(): 2026-10-30 23:05:50 UTC."""

    @classmethod
    def now(cls, tz=None):
        frozen = datetime(2026, 10, 30, 23, 5, 50, tzinfo=timezone.utc)
        return frozen.astimezone(tz) if tz else frozen.replace(tzinfo=None)


async def _noop(_: SIAEvent) -> None:
    return None


@pytest.fixture
def account():
    """Return default account."""
    return SIAAccount(ACCOUNT, KEY)


@pytest.fixture
def account_list(account):
    """Return default account."""
    return [account]


@fixture(unpack_into="client, config, good, sync")
@parametrize_with_cases("good", prefix="handler_")
@parametrize_with_cases("key", prefix="encrypted_")
@parametrize_with_cases("sync", prefix="sync_")
@parametrize_with_cases("protocol", prefix="proto_")
def create_client(
    unused_tcp_port_factory,
    event_handler,
    async_event_handler,
    bad_handler,
    async_bad_handler,
    key,
    good,
    protocol,
    sync,
):
    """Fixture to create a SIA Client."""
    config = {
        "host": HOST,
        "port": unused_tcp_port_factory(),
        "account_id": ACCOUNT,
        "key": key,
        "protocol": protocol,
    }

    if sync:
        client = SIAClient(
            host=config["host"],
            port=config["port"],
            accounts=[SIAAccount(config["account_id"], config["key"])],
            function=event_handler if good else bad_handler,
            protocol=config["protocol"],
        )
    else:
        client = SIAClientA(
            host=config["host"],
            port=config["port"],
            accounts=[SIAAccount(config["account_id"], config["key"])],
            function=async_event_handler if good else async_bad_handler,
            protocol=config["protocol"],
        )
    return (client, config, good, sync)


def get_func(type="sync"):
    """Get a test func."""

    async def async_func(event: SIAEvent):
        """Pass for testing."""
        pass

    def func(event: SIAEvent):
        """Pass for testing."""
        pass

    if type == "both":
        return (func, async_func)
    elif type == "aio":
        return async_func
    else:
        return func


@fixture(
    unpack_into="events, event_handler, async_event_handler, bad_handler, async_bad_handler"
)
def get_event_func():
    """Return the handler function."""
    events = []

    async def async_event_handler(event: SIAEvent):
        events.append(event)

    def event_handler(event: SIAEvent):
        events.append(event)

    def bad_handler(_):
        raise ValueError("test error in user func")

    async def async_bad_handler(_):
        raise ValueError("test error in user func")

    return (events, event_handler, async_event_handler, bad_handler, async_bad_handler)


class testSIA(object):
    """Class for pysiaalarm tests."""

    @parametrize_with_cases("cl, dic, clear_account", cases=ToFromDict)
    def test_to_from_dict(self, cl, dic, clear_account):
        """Test the to and from dict methods."""
        _LOGGER.warning("Dict before: %s", dic)
        instance = cl.from_dict(dic)
        _LOGGER.warning("Class instance %s", instance)
        if cl == SIAAccount:
            assert instance.account_id == dic["account_id"]
            assert instance.key == dic["key"]
            dic2 = instance.to_dict()
        else:
            assert instance.account == dic["account"]
            assert instance.code == dic["code"]
            dic2 = instance.to_dict()

        _LOGGER.warning("Dict after: %s", dic2)
        for key, value in dic.items():
            if key == "sia_account":
                if dic[key]:
                    assert instance.sia_account is not None
            elif key == "message_type":
                assert dic2[key].value == value
            elif key == "timestamp":
                assert dic2[key] == value.isoformat()
            else:
                assert dic2[key] == value

    @parametrize_with_cases(
        "line, account_id, code_type, code, error_type, extended_data_flag, encrypted_flag",
        cases=EventParsing,
    )
    def test_event_parsing(
        self,
        line,
        account_id,
        code_type,
        code,
        error_type,
        extended_data_flag,
        encrypted_flag,
    ):
        """Test event parsing methods."""
        catch = error_type if error_type is not None else Exception
        try:
            if extended_data_flag:
                event = SIAEvent.from_line(
                    line,
                    {
                        account_id: SIAAccount(
                            account_id, KEY, allowed_timeband=None  # type: ignore
                        )
                    },
                )
            else:
                event = SIAEvent.from_line(line)
            assert event.code == code
            if not event.valid_message:
                _LOGGER.warning("Event full message: %s", event.full_message)
                _LOGGER.warning("Event sent crc: %s", event.msg_crc)
                _LOGGER.warning("Event calc crc: %s", event.calc_crc)
            # assert event.valid_message
            if code:
                assert event.sia_code
                assert event.sia_code.type == code_type
            assert event.account == account_id
            if extended_data_flag:
                _LOGGER.warning("CRC: %s", event.calc_crc)
                assert event.extended_data is not None
                if event.extended_data[0].identifier == "K":
                    _LOGGER.debug("RSP Response: %s", event.create_response())
                    assert event.response == ResponseType.RSP
                else:
                    assert event.response == ResponseType.ACK
        except NoAccountError:
            assert encrypted_flag
        except AssertionError as e:
            raise e
        except catch as e:
            if error_type is None:
                _LOGGER.debug("Error thrown: %s", e)
                assert False
            if isinstance(e, error_type):
                assert True

    @parametrize_with_cases(
        "line, account_id, code_type, code, error_type, extended_data_flag, encrypted_flag",
        cases=EventParsing,
    )
    def test_event_serialization(
        self,
        line,
        account_id,
        code_type,
        code,
        error_type,
        extended_data_flag,
        encrypted_flag,
    ):
        """Test event parsing methods."""
        if error_type is not None:
            pytest.skip("Wrong messages will not serialize.")
            return
        if encrypted_flag is True:
            pytest.skip("Encrypted messages without account will not serialize.")
            return
        event = BaseEvent.from_line(line)
        event_type = event.__class__
        event_dict = event.to_dict()
        event2 = event_type.from_dict(event_dict)
        assert event == event2

    @parametrize_with_cases("key, account_id, error_type", cases=AccountSetup)
    def test_sia_account_setup(
        self, unused_tcp_port_factory, key, account_id, error_type
    ):
        """Test sia client behaviour."""
        try:
            SIAAccount.validate_account(account_id, key)
            SIAClient(
                host="",
                port=unused_tcp_port_factory(),
                accounts=[SIAAccount(account_id=account_id, key=key)],
                function=get_func("sync"),
            )
            assert True if error_type is None else False
        except Exception as exp:
            assert isinstance(exp, error_type)

    @parametrize_with_cases("key, account_id, error_type", cases=AccountSetup)
    def test_sia_account_validation(self, key, account_id, error_type):
        """Test sia account validation."""
        try:
            SIAAccount.validate_account(account_id, key)
            assert True if error_type is None else False
        except Exception as exp:
            assert isinstance(exp, error_type)

    @parametrize_with_cases("fault", prefix="fault_")
    @pytest.mark.asyncio
    async def test_clients(
        self,
        unused_tcp_port_factory,
        events,
        client,
        config,
        good,
        sync,
        fault,
    ):
        """Test the clients."""
        if sync:
            client.start(poll_interval=0.01)
        else:
            await client.async_start()
        await asyncio.to_thread(
            send_messages,
            config,
            {fault: True},
            connect_timeout=0.25,
            connect_interval=0.01,
            recv_timeout=0.25,
        )

        if sync:
            client.stop()
        else:
            await client.async_stop()

        _LOGGER.warning("Registered events: %s", client.counts)

        if fault is not None:
            assert client.counts.get(fault) == 1
        else:
            assert client.counts.get(COUNTER_VALID) == 1
        if good and not fault:
            assert len(events) == 1
            assert client.counts.get(COUNTER_EVENTS) == 1
        if not good and not fault:
            assert client.counts.get(COUNTER_USER_CODE) == 1
        if not good or fault:
            assert len(events) == 0

    @parametrize_with_cases("msg_type", prefix="msg_")
    @parametrize_with_cases(
        "code, alter_key, wrong_event, response", cases=ParseAndCheckEvent
    )
    @parametrize_with_cases("key", prefix="encrypted_")
    def test_parse_and_check(
        self,
        unused_tcp_port_factory,
        event_handler,
        key,
        code,
        msg_type,
        alter_key,
        wrong_event,
        response,
    ):
        """Test the server parsing."""
        if msg_type in ("ADM-CID", "NULL") and code == "ZX":
            pytest.skip(
                "Unknown code is not usefull to test in ADM-CID and NULL messages."
            )
            return
        if alter_key and msg_type == "NULL":
            pytest.skip(
                "Altered keys on NULL messages can still parse to valid content."
            )
            return
        if alter_key and key is None:
            pytest.skip("Alter key is not usefull to test when not encrypted.")
            return

        siac = SIAClient(
            HOST, unused_tcp_port_factory(), [SIAAccount(ACCOUNT, key)], event_handler
        )
        line = create_test_line(
            account=ACCOUNT,
            key=key,
            code=code,
            msg_type=msg_type,
            wrong_event=wrong_event,
            alter_key=alter_key,
        )

        _LOGGER.warning("Line to parse: %s", line)
        event = siac.sia_server.parse_and_check_event(line.encode())
        _LOGGER.warning("Event received: %s", event)

        assert event.response == response
        if wrong_event or alter_key:
            assert isinstance(event, NAKEvent)
        else:
            assert event.account == ACCOUNT
            assert event.code == "RP" if msg_type == "NULL" else code

    def test_accounts_get_set(self, account_list, unused_tcp_port):
        """Test the account getting and setting."""
        siac = SIAClient(
            host="",
            port=unused_tcp_port,
            accounts=account_list,
            function=(lambda ev: print(ev)),
        )
        assert siac.accounts == account_list
        acc_list2 = [
            SIAAccount(account_id=ACCOUNT, key=KEY, allowed_timeband=(None, None)),
            SIAAccount(account_id="1112", key=KEY, allowed_timeband=(None, None)),
        ]
        siac.accounts = acc_list2
        assert siac.accounts == acc_list2

    @parametrize_with_cases("sync_func", prefix="sync_")
    @parametrize_with_cases("sync_client", prefix="sync_")
    def test_func_errors(
        self,
        account_list,
        unused_tcp_port_factory,
        sync_client,
        sync_func,
    ):
        """Test the function setting."""
        error_type = TypeError if sync_client != sync_func else None
        try:
            if sync_client:
                SIAClient(
                    HOST,
                    unused_tcp_port_factory(),
                    account_list,
                    get_func("sync" if sync_func else "aio"),
                )
            else:
                SIAClientA(
                    HOST,
                    unused_tcp_port_factory(),
                    account_list,
                    get_func("sync" if sync_func else "aio"),
                )
            assert error_type is None
        except Exception as e:
            if isinstance(e, error_type):
                assert True
            else:
                assert False

    @parametrize_with_cases("sync", prefix="sync_")
    @pytest.mark.asyncio
    async def test_context(self, account_list, unused_tcp_port_factory, sync):
        """Test the context manager functions."""
        if sync:
            with patch.object(SIAClient, "stop") as client:
                with SIAClient(
                    HOST,
                    unused_tcp_port_factory(),
                    account_list,
                    function=get_func("sync"),
                ) as cl:
                    assert cl.accounts == account_list
                client.assert_called_once()

        else:
            with patch.object(SIAClientTCP, "async_stop") as client:
                with patch("asyncio.start_server"):
                    # test Async
                    async with SIAClientA(
                        HOST,
                        port=unused_tcp_port_factory(),
                        accounts=account_list,
                        function=get_func("aio"),
                    ) as cl:
                        assert cl.accounts == account_list
                client.assert_awaited_once()

    def test_response_qualifier_in_ack(self):
        """Test response qualifier usage in ACK responses."""
        account = SIAAccount(ACCOUNT, None, response_qualifier="ab", allowed_timeband=None)
        line = create_test_line(
            account=ACCOUNT, key=None, code="RP", use_fixed_time=True
        )
        event = SIAEvent.from_line(line, {ACCOUNT: account})
        response = event.create_response().decode("ascii")
        assert f"#{ACCOUNT}[AB]" in response

    def test_response_qualifier_in_nak(self):
        """Test response qualifier usage in NAK responses."""
        account = SIAAccount(
            ACCOUNT, None, allowed_timeband=(0, 0), response_qualifier="ab"
        )
        line = create_test_line(
            account=ACCOUNT, key=None, code="RP", use_fixed_time=True
        )
        event = SIAEvent.from_line(line, {ACCOUNT: account})
        assert event.response == ResponseType.NAK
        response = event.create_response().decode("ascii")
        assert "A0[AB]" in response

    def test_response_qualifier_in_encrypted_response(self):
        """Test response qualifier usage in encrypted responses."""
        account = SIAAccount(ACCOUNT, KEY, response_qualifier="ab")
        line = create_test_line(account=ACCOUNT, key=KEY, code="RP")
        event = SIAEvent.from_line(line, {ACCOUNT: account})
        response = event.create_response().decode("ascii")
        assert f"#{ACCOUNT}[AB" in response

    def test_default_account_fallback(self):
        """Test using the default account when no direct match exists."""
        default_account = SIAAccount("", KEY)
        line = create_test_line(
            account=ACCOUNT, key=KEY, code="RP", use_fixed_time=True
        )
        event = SIAEvent.from_line(line, {"": default_account})
        assert event.sia_account is default_account
        assert event.code == "RP"

    @pytest.mark.parametrize("cut_to_bytes", [8, 10, 38, 43])
    def test_truncated_ciphertext_is_nak(self, cut_to_bytes):
        """A ciphertext cut short by the panel is a format error answered with NAK.

        Hikvision AX HOME stops the ciphertext at its first 0x00 byte; CRC and length
        match the cut frame. Before, this raised ValueError and dropped the connection.
        """
        account = SIAAccount(ACCOUNT, KEY)
        line = create_test_line(
            account=ACCOUNT, key=KEY, code="RP", truncate_to_bytes=cut_to_bytes
        )
        with pytest.raises(EventFormatError):
            SIAEvent.from_line(line, {ACCOUNT: account})

        server = SIAServerTCP({ACCOUNT: account}, _noop, Counter())
        event = server.parse_and_check_event(line.encode())
        assert isinstance(event, NAKEvent)
        assert event.response == ResponseType.NAK
        assert server.counts.get(COUNTER_FORMAT) == 1

    def test_non_hex_ciphertext_is_nak(self):
        """A ciphertext that is not hex is a format error answered with NAK."""
        account = SIAAccount(ACCOUNT, KEY)
        body = f'"*SIA-DCS"0001L0#{ACCOUNT}[{"G" * 32}'
        line = f"{crc_calc(body)}{len(body):04X}{body}"
        server = SIAServerTCP({ACCOUNT: account}, _noop, Counter())
        event = server.parse_and_check_event(line.encode())
        assert isinstance(event, NAKEvent)
        assert server.counts.get(COUNTER_FORMAT) == 1

    @parametrize_with_cases("key", prefix="encrypted_")
    def test_old_event_block_is_acked(self, key):
        """A retransmission with the DC-03 old event block O is parsed and ACKed."""
        account = SIAAccount(ACCOUNT, key)
        line = create_test_line(account=ACCOUNT, key=key, code="RP", block="O")
        server = SIAServerTCP({ACCOUNT: account}, _noop, Counter())
        event = server.parse_and_check_event(line.encode())
        assert event.code == "RP"
        assert event.ri == "0"
        assert event.response == ResponseType.ACK

    @parametrize_with_cases("key", prefix="encrypted_")
    @pytest.mark.parametrize(
        "sent, minute_precision, response",
        [
            ("_23:05:45,10-30-2026", False, ResponseType.ACK),  # normal panel
            ("_23:05:05,10-30-2026", False, ResponseType.NAK),  # HH:MM:MM, default
            ("_23:05:05,10-30-2026", True, ResponseType.ACK),  # HH:MM:MM, opt-in
            ("_23:03:03,10-30-2026", True, ResponseType.NAK),  # too old: replay check
            ("_23:07:07,10-30-2026", True, ResponseType.NAK),  # too far in the future
        ],
    )
    def test_timestamp_minute_precision(self, key, sent, minute_precision, response):
        """Panels with unreliable seconds can opt in to a minute-precision check.

        now = 23:05:50 UTC and the default band (40, 20) accepts 23:05:10 to 23:06:10.
        """
        account = SIAAccount(ACCOUNT, key, timestamp_minute_precision=minute_precision)
        line = create_test_line(account=ACCOUNT, key=key, code="RP", timestamp=sent)
        with patch("pysiaalarm.event.datetime", _FrozenDatetime):
            event = SIAEvent.from_line(line, {ACCOUNT: account})
            assert event.response == response

    def test_sync_tcp_handler_shutdown_skips_recv(self):
        """Ensure TCP handler does not read when shutdown is requested."""
        server = Mock()
        server.shutdown_flag = True
        request = Mock()
        request.recv = Mock(side_effect=AssertionError("recv called"))
        SIATCPHandler(request, ("127.0.0.1", 1234), server)
        request.recv.assert_not_called()

    def test_sync_udp_handler_shutdown_skips_recv(self):
        """Ensure UDP handler does not process when shutdown is requested."""
        server = Mock()
        server.shutdown_flag = True
        socket = Mock()
        request = (b"data", socket)
        SIAUDPHandler(request, ("127.0.0.1", 1234), server)
        socket.sendto.assert_not_called()

    @pytest.mark.asyncio
    async def test_aio_tcp_handler_shutdown_closes_writer(self, account):
        """Ensure async TCP handler closes writer when shutdown is requested."""
        async def async_func(_: SIAEvent) -> None:
            return None

        server = SIAServerTCP({account.account_id: account}, async_func, Counter())
        server.shutdown_flag = True
        reader = AsyncMock(spec=asyncio.StreamReader)
        writer = AsyncMock(spec=asyncio.StreamWriter)
        writer.close = Mock()
        writer.wait_closed = AsyncMock()

        await server.handle_line(reader, writer)

        reader.read.assert_not_awaited()
        writer.close.assert_called_once()
        writer.wait_closed.assert_awaited_once()

    def test_aio_udp_handler_shutdown_ignores_datagrams(self, account):
        """Ensure async UDP handler ignores datagrams during shutdown."""
        async def async_func(_: SIAEvent) -> None:
            return None

        server = SIAServerUDP({account.account_id: account}, async_func, Counter())
        server.shutdown_flag = True
        with patch.object(server, "parse_and_check_event") as parse_event:
            server.datagram_received(b"data", ("127.0.0.1", 1234))
        parse_event.assert_not_called()
