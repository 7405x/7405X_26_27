#include <stdio.h>
#include <string.h>
#include "vaic_odom.h"

namespace vaic {

static uint32_t table[256];

uint32_t crc32(const uint8_t *data, uint32_t n, uint32_t acc) {
  // Same non-reflected CRC as ai_jetson.cpp / protocol crc32()
  if (table[1] == 0) {
    for (uint32_t i = 0; i < 256; i++) {
      uint32_t c = i << 24;
      for (int j = 0; j < 8; j++)
        c = (c & 0x80000000) ? (c << 1) ^ VAIC_CRC32_POLY : (c << 1);
      table[i] = c;
    }
  }
  for (uint32_t k = 0; k < n; k++) {
    uint32_t i = ((acc >> 24) ^ data[k]) & 0xFF;
    acc = (acc << 8) ^ table[i];
  }
  return acc;
}

bool send_odom(uint32_t t_ms, float x, float y, float heading_deg, int32_t status) {
  struct __attribute__((__packed__)) { VAIC_PACKET_HEADER h; ODOM_RECORD o; } pkt;
  const uint8_t sync[4] = VAIC_SYNC_BYTES;
  memcpy(pkt.h.sync, sync, 4);
  pkt.h.length = sizeof(ODOM_RECORD);
  pkt.h.type = PACKET_TYPE_ODOM;
  pkt.o.t_ms = t_ms; pkt.o.x = x; pkt.o.y = y; pkt.o.heading = heading_deg; pkt.o.status = status;
  pkt.h.crc32 = crc32((const uint8_t *)&pkt.o, sizeof(ODOM_RECORD), 0);

  FILE *fp = fopen("/dev/serial1", "w");
  if (fp == NULL) return false;
  size_t n = fwrite(&pkt, 1, sizeof(pkt), fp);
  fclose(fp);
  return n == sizeof(pkt);
}

}  // namespace vaic
