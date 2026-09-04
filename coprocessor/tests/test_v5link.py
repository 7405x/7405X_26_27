import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import vaic_protocol as P  # noqa: E402
from vaic.v5link import PacketParser, V5Link  # noqa: E402


class ParserTests(unittest.TestCase):
    def test_request_line_split_across_reads(self):
        p = PacketParser()
        self.assertEqual(p.feed(b"AA55C"), [])
        self.assertEqual(p.feed(b"C3301\r\nAA55CC3301\r\n"), [("request",), ("request",)])

    def test_binary_odom_packet_and_garbage(self):
        p = PacketParser()
        odom = P.ODOM_RECORD(t_ms=100, x=1.0, y=-1.0, heading=90.0, status=1)
        frame = P.build_packet(odom.pack(), P.PACKET_TYPE_ODOM)
        ev = p.feed(b"\x00\x11" + frame[:7]) + p.feed(frame[7:] + b"AA55CC3301\n")
        self.assertEqual(ev[0][0], "packet")
        self.assertEqual(ev[0][1], P.PACKET_TYPE_ODOM)
        self.assertEqual(P.ODOM_RECORD.unpack(ev[0][2]), odom)
        self.assertEqual(ev[1], ("request",))
        self.assertEqual(bytes(p.buf), b"")

    def test_corrupt_packet_is_skipped(self):
        frame = bytearray(P.build_packet(P.ODOM_RECORD().pack(), P.PACKET_TYPE_ODOM))
        frame[-1] ^= 1
        p = PacketParser()
        self.assertEqual(p.feed(bytes(frame) + b"AA55CC3301\n"), [("request",)])


class LinkTests(unittest.TestCase):
    def test_request_gets_current_record_and_odom_callback(self):
        got = []
        link = V5Link(on_odom=got.append)
        rec = P.AI_RECORD(pos=P.POS_RECORD(x=2.0), detections=[P.DETECTION_OBJECT(classID=1)])
        link.set_record(rec)
        written = []
        link.handle(("request",), written.append)
        self.assertEqual(P.decode_ai_record(written[0]).pos.x, 2.0)
        odom = P.ODOM_RECORD(t_ms=5, x=0.5, status=1)
        link.handle(("packet", P.PACKET_TYPE_ODOM, odom.pack()), written.append)
        self.assertEqual(got, [odom])
        self.assertEqual((link.requests, link.odom_packets, link.packets_sent), (1, 1, 1))
