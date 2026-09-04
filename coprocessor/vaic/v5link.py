"""Serial link to the V5 Brain using the generated protocol.

Brain -> Jetson: the ASCII request line "AA55CC3301\\r\\n" (VEX's original) and,
optionally, binary ODOM packets (PACKET_TYPE_ODOM).
Jetson -> Brain: one AI_RECORD packet per request.

`feed()` is a pure parser so the link is testable without hardware.
"""
import threading
import time
from typing import Callable, List, Optional, Tuple

import vaic_protocol as P

REQUEST = P.REQUEST_LINE.encode()


class PacketParser:
    def __init__(self):
        self.buf = bytearray()

    def feed(self, data: bytes) -> List[Tuple]:
        """Returns events: ("request",) or ("packet", type, payload)."""
        self.buf += data
        events = []
        while self.buf:
            if self.buf.startswith(REQUEST):
                nl = self.buf.find(b"\n", len(REQUEST))
                del self.buf[: (nl + 1) if nl >= 0 else len(REQUEST)]
                events.append(("request",))
                continue
            if self.buf.startswith(P.SYNC_BYTES):
                if len(self.buf) < P.HEADER_SIZE:
                    break
                length = int.from_bytes(self.buf[4:6], "little")
                if len(self.buf) < P.HEADER_SIZE + length:
                    break
                frame = bytes(self.buf[: P.HEADER_SIZE + length])
                try:
                    events.append(("packet",) + P.parse_packet(frame))
                    del self.buf[: len(frame)]
                except ValueError:
                    del self.buf[0]        # bad crc: resync one byte later
                continue
            # neither prefix matches yet; keep bytes that could still start one
            if REQUEST.startswith(bytes(self.buf[:1])) and len(self.buf) < len(REQUEST):
                break
            if P.SYNC_BYTES.startswith(bytes(self.buf[:1])) and len(self.buf) < 4:
                break
            del self.buf[0]
        return events


class V5Link:
    def __init__(self, port: Optional[str] = None, on_odom: Optional[Callable[[P.ODOM_RECORD], None]] = None,
                 serial_factory=None):
        self.port = port
        self.on_odom = on_odom
        self._serial_factory = serial_factory   # for tests; default pyserial
        self._record = P.AI_RECORD()
        self._lock = threading.Lock()
        self._started = False
        self._thread: Optional[threading.Thread] = None
        self.packets_sent = 0
        self.requests = 0
        self.odom_packets = 0
        self.connected = False

    def set_record(self, rec: P.AI_RECORD) -> None:
        with self._lock:
            self._record = rec

    def handle(self, event: Tuple, write: Callable[[bytes], None]) -> None:
        if event[0] == "request":
            self.requests += 1
            with self._lock:
                data = P.encode_ai_record(self._record)
            write(data)
            self.packets_sent += 1
        elif event[0] == "packet" and event[1] == P.PACKET_TYPE_ODOM:
            self.odom_packets += 1
            if self.on_odom:
                self.on_odom(P.ODOM_RECORD.unpack(event[2]))

    # ---- hardware side ----
    @staticmethod
    def find_port() -> Optional[str]:
        from serial.tools.list_ports import comports
        for dev in comports():
            if "V5" in dev.description and "User" in dev.description:
                return dev.device
        return None

    def start(self) -> None:
        self._started = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._started = False
        if self._thread:
            self._thread.join(timeout=2)

    def _open(self):
        if self._serial_factory:
            return self._serial_factory(self.port)
        import serial
        return serial.Serial(self.port, P.BAUD, timeout=0.05)

    def _run(self) -> None:
        parser = PacketParser()
        while self._started:
            if self.port is None:
                self.port = self.find_port()
                if self.port is None:
                    print("[v5link] no V5 Brain user port found, retrying")
                    time.sleep(1)
                    continue
            try:
                ser = self._open()
                self.connected = True
                print("[v5link] connected to", self.port)
                while self._started:
                    data = ser.read(max(1, getattr(ser, "in_waiting", 1)))
                    if data:
                        for ev in parser.feed(data):
                            self.handle(ev, ser.write)
            except Exception as e:  # serial errors: reconnect
                print("[v5link] error:", e)
                time.sleep(1)
            finally:
                self.connected = False
                try:
                    ser.close()
                except Exception:
                    pass
