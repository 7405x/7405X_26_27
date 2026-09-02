"""Layout v1 must match VEX's V5Comm.py / ai_jetson.h byte for byte."""
import os
import struct
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "generated"))
import vaic_protocol as P  # noqa: E402


def vex_reference_payload(pos, dets):
    """Hand-copied from JetsonExample/V5Comm.py + V5Position.py."""
    out = struct.pack("<i", len(dets))
    out += struct.pack("<iiffffff", *pos)
    for classID, prob, depth, img, mp in dets:
        out += struct.pack("<iff", classID, prob, depth)
        out += struct.pack("<iiii", *img)
        out += struct.pack("<fff", *mp)
    return out


class LayoutTests(unittest.TestCase):
    def test_sizes_match_c_header(self):
        self.assertEqual(P.POS_RECORD.SIZE, 32)
        self.assertEqual(P.IMAGE_DETECTION.SIZE, 16)
        self.assertEqual(P.MAP_DETECTION.SIZE, 12)
        self.assertEqual(P.DETECTION_OBJECT.SIZE, 40)
        self.assertEqual(P.AI_RECORD.SIZE, 4 + 32 + 50 * 40)
        self.assertEqual(P.HEADER_SIZE, 12)

    def test_payload_matches_vex_reference(self):
        pos = (7, 1, 0.5, -0.25, 0.1, 90.0, 1.0, -1.0)
        dets = [(2, 0.75, 1.5, (10, 20, 30, 40), (0.1, 0.2, 0.3)),
                (0, 0.5, 3.0, (1, 2, 3, 4), (-1.0, -2.0, 0.0))]
        rec = P.AI_RECORD(pos=P.POS_RECORD(*pos))
        for c, p, d, img, mp in dets:
            rec.detections.append(P.DETECTION_OBJECT(c, p, d, P.IMAGE_DETECTION(*img), P.MAP_DETECTION(*mp)))
        self.assertEqual(rec.pack(), vex_reference_payload(pos, dets))

    def test_header_matches_vex_reference(self):
        payload = b"\x00" * 36
        pkt = P.build_packet(payload, P.PACKET_TYPE_AI_RECORD)
        self.assertEqual(pkt[:4], bytes([0xAA, 0x55, 0xCC, 0x33]))
        length, ptype, crc = struct.unpack_from("<HHI", pkt, 4)
        self.assertEqual((length, ptype), (36, 1))
        self.assertEqual(crc, P.crc32(payload))

    def test_crc_matches_vex_table_algorithm(self):
        # Same algorithm as AIRecord.__Crc32Generate in V5Comm.py.
        table = []
        for i in range(256):
            a = i << 24
            for _ in range(8):
                a = (a << 1) ^ 0x04C11DB7 if a & 0x80000000 else a << 1
            table.append(a)
        data = bytes(range(200))
        acc = 0
        for b in data:
            acc = (acc << 8) ^ table[((acc >> 24) ^ b) & 0xFF]
        self.assertEqual(P.crc32(data), acc & 0xFFFFFFFF)

    def test_roundtrip_and_truncation(self):
        rec = P.AI_RECORD(pos=P.POS_RECORD(x=1.0), detections=[P.DETECTION_OBJECT(classID=k) for k in range(60)])
        back = P.decode_ai_record(P.encode_ai_record(rec))
        self.assertEqual(back.detectionCount, P.MAX_DETECTIONS)
        self.assertEqual(len(back.detections), P.MAX_DETECTIONS)
        self.assertEqual(back.pos.x, 1.0)

    def test_bad_crc_rejected(self):
        pkt = bytearray(P.encode_ai_record(P.AI_RECORD()))
        pkt[-1] ^= 0xFF
        with self.assertRaises(ValueError):
            P.parse_packet(bytes(pkt))

    def test_generated_files_are_fresh(self):
        import subprocess
        r = subprocess.run([sys.executable, os.path.join(HERE, "..", "generate.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_layout_hash_agrees_with_header(self):
        h = open(os.path.join(HERE, "..", "generated", "vaic_protocol.h")).read()
        self.assertIn(f'#define VAIC_LAYOUT_HASH        "{P.LAYOUT_HASH}"', h)


if __name__ == "__main__":
    unittest.main()
