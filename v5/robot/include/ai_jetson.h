/*----------------------------------------------------------------------------*/
/*                                                                            */
/*    Copyright (c) Innovation First 2020, All rights reserved.               */
/*    Licensed under the MIT license.                                         */
/*                                                                            */
/*    Module:     ai_jetson.h                                                 */
/*    Author:     James Pearman                                               */
/*    Created:    3 Aug 2020                                                  */
/*                                                                            */
/*    Revisions:  V0.1                                                        */
/*                                                                            */
/*----------------------------------------------------------------------------*/

#ifndef AI_JETSON_H_
#define AI_JETSON_H_

/*----------------------------------------------------------------------------*/
/** @file    jetson.h
  * @brief   Header for jetson communication
*//*--------------------------------------------------------------------------*/

#ifdef __cplusplus
extern "C" {
#endif

// Wire structs come from the generated, versioned protocol header.
// Edit protocol/schema.py and run `python protocol/generate.py`; never edit vaic_protocol.h.
#include "vaic_protocol.h"

/// GPS status flags (kept for dashboard.cpp)
#define POS_GPS_CONNECTED   POS_STATUS_CONNECTED

// packet from V5
typedef struct __attribute__((__packed__)) _map_packet {
    VAIC_PACKET_HEADER  header;
    AI_RECORD           map;
} map_packet;

#ifdef __cplusplus
}
#endif

namespace ai {
  class jetson  {
      public:
        jetson();
        ~jetson();

        int32_t    get_packets(void);
        int32_t    get_errors(void);
        int32_t    get_timeouts(void);
        int32_t    get_total(void);
        int32_t    get_data( AI_RECORD *map );
        void       request_map();


      private:
        // packet sync bytes
        enum class sync_byte {
            kSync1 = 0xAA,
            kSync2 = 0x55,
            kSync3 = 0xCC,
            kSync4 = 0x33
        };


        enum class jetson_state {
            kStateSyncWait1   = 0,
            kStateSyncWait2,
            kStateSyncWait3,
            kStateSyncWait4,
            kStateLength,
            kStateSpare,
            kStateCrc32,
            kStatePayload,
            kStateGoodPacket,
            kStateBadPacket,
        };

        jetson_state  state;
        int32_t       index;
        vex::timer    timer;
        uint32_t      packets;
        uint32_t      errors;
        uint32_t      timeouts;
        uint16_t      payload_length; 
        uint16_t      payload_type; 
        uint32_t      payload_crc32;
        uint32_t      calc_crc32;
        uint32_t      last_packet_time;
        uint32_t      total_data_received;
        
        union {
          AI_RECORD  map;
          uint8_t     bytes[4096];
        } payload;

        vex::mutex    maplock;

        AI_RECORD    last_map;
        uint32_t      last_payload_length;

        bool          parse( uint8_t data );

        static int    receive_task( void *arg );

        static  uint32_t _crc32_table[256];
        static  uint32_t  crc32( uint8_t *pData, uint32_t numberOfBytes, uint32_t accumulator );
    };
};


#endif /* AI_JETSON_H_ */