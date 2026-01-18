#include "otr_assets.h"

namespace OTRAssets {

const char* us_v10_yaml = R"(
segments:
  - type: bin
    subsegments:
      - [0, "bin", "segment1"]
      - [4096, "bin", "segment2"]
)"; // Replace with full YAML content

const size_t us_v10_size = sizeof(us_v10_yaml) - 1;

const char* pal_yaml = R"(
segments:
  - type: bin
    subsegments:
      - [0, "bin", "segment1"]
      - [4096, "bin", "segment2"]
)"; // Replace with full YAML content

const size_t pal_size = sizeof(pal_yaml) - 1;

}