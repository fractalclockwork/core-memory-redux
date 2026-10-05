"""BOM part catalog for multi-board PCB emit (from docs/component_selection.md).

Symbol lib_ids use KiCad stock libraries (HC stands in for AHC per component_selection).
Footprints are KiCad stock Package_* / Diode_SMD / Potentiometer_THT.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Part:
    """One placeable BOM line."""

    mpn: str
    lib_id: str
    footprint: str
    pins: int  # pin count for instance uuid stubs
    role: str


# --- ccs_sense (host) -------------------------------------------------------

CCS_CHANNELS = ("X", "Y", "INH")

PART_TL431 = Part(
    "TL431",
    "Reference_Voltage:TL431DBZ",
    "Package_TO_SOT_SMD:SOT-23",
    3,
    "CCS Vref",
)
PART_TRIM = Part(
    "3296W",
    "Device:R_Potentiometer_Trim",
    "Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical",
    3,
    "CCS trim",
)
PART_OPA192 = Part(
    "OPA192",
    "Device:Opamp_Dual",
    "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    8,
    "CCS error amp (Opamp_Dual stand-in)",
)
PART_IRLZ44N = Part(
    "IRLZ44N",
    "Transistor_FET:IRLZ44N",
    "Package_TO_SOT_THT:TO-220-3_Vertical",
    3,
    "CCS throttle MOSFET",
)
PART_RSENSE = Part(
    "1R0",
    "Device:R",
    "Resistor_SMD:R_2512_6332Metric",
    2,
    "CCS sense 1Ω 2W",
)
PART_BAT54S = Part(
    "BAT54S",
    "Diode:BAT54S",
    "Package_TO_SOT_SMD:SOT-23",
    3,
    "Sense clamp",
)
PART_TLV3501 = Part(
    "TLV3501",
    "Comparator:TLV3501AIDBV",
    "Package_TO_SOT_SMD:SOT-23-6",
    6,
    "Sense comparator",
)
PART_74AHC74 = Part(
    "74AHC74",
    "74xx:74HC74",
    "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    14,
    "Write-back latch (HC lib_id)",
)
PART_R1K = Part(
    "1k",
    "Device:R",
    "Resistor_SMD:R_0805_2012Metric",
    2,
    "Sense isolation",
)
PART_R10K = Part(
    "10k",
    "Device:R",
    "Resistor_SMD:R_0805_2012Metric",
    2,
    "Bias / fail-safe",
)
PART_PICO = Part(
    "Pico_Header",
    "Connector_Generic:Conn_02x20_Odd_Even",
    "Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical",
    40,
    "Pico-compatible 2x20 header",
)

# --- axis_octal -------------------------------------------------------------

PART_74AHC138 = Part(
    "74AHC138",
    "74xx:74HC138",
    "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
    16,
    "HS decode (HC lib_id)",
)
PART_74AHC238 = Part(
    "74AHC238",
    "74xx:74HC238",
    "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
    16,
    "LS decode (HC lib_id)",
)
PART_TBD62783 = Part(
    "TBD62783",
    "Transistor_Array:TBD62783A",
    "Package_SO:SOIC-18W_7.5x11.6mm_P1.27mm",
    18,
    "HS DMOS source array",
)
PART_TBD62083 = Part(
    "TBD62083",
    "Transistor_Array:TBD62783A",  # no TBD62083 in KiCad; same SOP-18 body
    "Package_SO:SOIC-18W_7.5x11.6mm_P1.27mm",
    18,
    "LS DMOS sink array (62783A symbol stand-in)",
)
PART_SS14 = Part(
    "SS14",
    "Device:D_Schottky",
    "Diode_SMD:D_SMA",
    2,
    "Steer Schottky",
)
