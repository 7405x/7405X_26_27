/*
 * Send the Brain's own pose estimate to the coprocessor (PACKET_TYPE_ODOM).
 * Call from the SAME task that calls jetson_comms.request_map(), after it,
 * because both write to /dev/serial1. The coprocessor uses this pose whenever
 * the GPS has no fix. Enable with VAIC_SEND_ODOM in main.cpp.
 */
#ifndef VAIC_ODOM_H_
#define VAIC_ODOM_H_
#include <stdint.h>
#include "vaic_protocol.h"

namespace vaic {
  // heading_deg: compass style, 0 = +Y, 90 = +X (same as GPS az)
  bool send_odom(uint32_t t_ms, float x, float y, float heading_deg, int32_t status);
  uint32_t crc32(const uint8_t *data, uint32_t n, uint32_t acc);
}
#endif
