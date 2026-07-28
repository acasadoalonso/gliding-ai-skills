# Appendix A — IGC Flight Data File Format

**Technical Specification for IGC-Approved GNSS Flight Recorders**
*January 2026 — with Amendment AL10*

> **Source:** FAI/IGC Technical Specification for IGC-Approved GNSS Flight Recorders,  
> January 2026 with AL10 — `igc_specification_january_2026_with_al10_0.pdf`

-----

## Contents

- [1. Introduction](#1-introduction)
  - [1.1 Background and IGC File Production](#11-background-and-igc-file-production)
  - [1.2 Revision Control](#12-revision-control)
- [2. General](#2-general)
  - [2.1 File Structure](#21-file-structure)
  - [2.2 Record Types](#22-record-types)
  - [2.3 Record Order](#23-record-order)
  - [2.4 Units](#24-units)
  - [2.5 File Naming](#25-file-naming)
- [3. Single Instance Data Records](#3-single-instance-data-records)
  - [3.1 A Record — FR Manufacturer and Identification](#31-a-record--fr-manufacturer-and-identification)
  - [3.2 G Record — Security](#32-g-record--security)
  - [3.3 H Record — File Header](#33-h-record--file-header)
  - [3.4 I Record — Extension to the Fix (B) Record](#34-i-record--extension-to-the-fix-b-record)
  - [3.5 J Record — Extension to the K Record](#35-j-record--extension-to-the-k-record)
  - [3.6 C Record — Task/Declaration](#36-c-record--taskdeclaration)
- [4. Multiple Instance Data Records](#4-multiple-instance-data-records)
  - [4.1 B Record — Fix](#41-b-record--fix)
  - [4.2 E Record — Events](#42-e-record--events)
  - [4.3 F Record — Satellite Constellation](#43-f-record--satellite-constellation)
  - [4.4 K Record — Extension Data](#44-k-record--extension-data)
  - [4.5 L Record — Logbook/Comments](#45-l-record--logbookcomments)
  - [4.6 D Record — Differential GPS](#46-d-record--differential-gps)
- [5. Definitions](#5-definitions)
- [6. Valid Characters](#6-valid-characters)
- [7. Three-Letter Codes (TLC)](#7-three-letter-codes-tlc)
- [8. GNSS Geodetic Datums](#8-gnss-geodetic-datums)
- [9. Example IGC-Format File](#9-example-igc-format-file)

-----

## 1. Introduction

### 1.1 Background and IGC File Production

The IGC Data File Standard was initially developed by a group consisting of representatives of IGC, glider FR manufacturers and a number of independent software developers mainly concerned with flight data analysis programs. After discussion and development during 1993 and 1994 it was initially defined in December 1994 and became part of official IGC/FAI documents after approval by IGC in March 1995. It has been refined and developed afterwards, through regular amendments. It provides a common world standard data format for the verification of badge, record, and competition flights to FAI/IGC criteria. The Standard may also be used by other FAI sports and activities.

**1.1.1** Production of Flight Data File. It must be possible to produce a separate and complete IGC flight data file for each flight including all record types (para 2.2) relevant to the flight such as header records, flight declaration, etc. Two ways of achieving this are by continuous recording of fixes between the times that the FR was switched on and off, or, for FRs that have a “standby” state on switch-on, only recording fixes after pre-set movement and pressure-change thresholds are exceeded (ceasing recording when changes are below the thresholds, but see 1.1.1.2 on short periods without external power). *(AL3)*

**1.1.1.1** Thresholds for starting and stopping recording, also Power-on Protocol for creating new IGC files. The following thresholds before fixes are recorded have been found suitable in the past: lat/long change, 10–15 km/hr; pressure altitude change, 1 metre per second for 5 seconds. Pre-takeoff and after-landing baselines of at least 20 fixes must be provided. For the pre-takeoff baseline, a small memory circuit can be used that continuously stores the appropriate number of previous fixes and, when movement is detected, puts them into the flight data record. After landing, this can be achieved by a time delay before stopping the recording of fixes. This condition may also apply to a period in wave or ridge lift with little or no vertical or horizontal movement. Therefore, a new IGC file must not be started while external power is still connected and the recorder is still switched on, even when no movement is being detected and no fixes are being recorded. Note that this “power-on protocol” is also needed for barograph calibrations so that a new file is not produced while the calibrator is making small adjustments to the pressure at each level of the calibration. A new IGC file is produced under the “Power-off Protocol” described under 1.1.1.2 below. *(AL5, modified by AL9)*

**1.1.1.2** Loss of external power for short periods — Power-off Protocol for creating new IGC files. To allow for events such as changing or switching batteries in flight, a period of 5 minutes with no external power shall be allowed to elapse before a new Flight Data File is created on powering up again. After this period has elapsed a new IGC file must be produced, so that if several flights are made on one day, each has a complete IGC data file of its own. *(AL3)*

**1.1.1.3** Data transfer to a PC. If the data for several flights is held in the FR memory, it must be ensured that when the data is transferred, all record types in IGC files that are subsequent to the first file are those relevant to each subsequent individual flight. If any record types are changed between flights (such as declaration, pilot name, etc.) the changes must be included in the subsequent (but not previous) flight data files. *(AL3)*

**1.1.1.4** Recorders operating on internal power. Some recorders are designed so that all of their functions are available on internal power. For these recorders, external power is used for charging and as a backup for long flights. When operating on internal power it must be ensured that under flight conditions of little horizontal or vertical movement (such as in ridge or wave flying), the IGC file continues to be able to record data and is not ended while flight continues. The IGC file shall be ended after one of the following three conditions:

1. If no horizontal or vertical movement has been detected for 10 minutes (thresholds as in 1.1.1.1 above);
1. After the recorder is switched off by deliberate action; or
1. If the recorder is still powered after the flight, when the user establishes a connection for purposes of downloading from the recorder.

*(AL10)*

### 1.2 Revision Control

The IGC flight data file format is revised through the normal amendment process for this document. See amendment procedures and list of amendments on page (i).

-----

## 2. General

### 2.1 File Structure

An IGC-format file consists of lines of characters, each line giving a set of data such as for a GNSS fix. Each line starts with an upper-case letter denoting one of the Record types listed in para 2.2, and ends with CRLF (Carriage Return Line Feed). Each line is limited to 76 characters in length, excluding the CRLF which is hidden and does not appear in text form. Some Record types take up only one line; some, such as task and header, take up several lines. For instance, the task/declaration (C) Record includes a line for each Waypoint, and the Header (H) Record includes separate lines for GNSS FR type, pilot name, glider identification, etc. The order of Record types within an IGC file is given in para 2.3.

Some Record types occur only once in the file (single instance Records); others such as fixes re-occur as time progresses (multiple instance Records). Only characters listed as valid in para 6 shall be used in the file. If accented characters (acutes, háčeks, umlauts, etc.) in names of airfields and turn points are used in a manufacturer’s proprietary format, such characters shall be converted to a valid character as part of the conversion to IGC format.

### 2.2 Record Types

The Record types are prefixed by upper-case letters as follows:

```
IGC DATA FILE FORMAT — RECORD TYPE IDENTIFICATION LETTERS

A  - FR manufacturer and identification
B  - Fix
C  - Task/declaration
D  - Differential GPS
E  - Event
F  - Constellation
G  - Security
H  - File header
I  - List of extension data included at end of each fix (B record)
J  - List of data included in each extension (K) Record
K  - Extension data
L  - Logbook/comments
M, N, etc. - Spare
```

### 2.3 Record Order

The FR I/D (A) Record is always the first in the file and the last is the Security (G) Record. After the single-line A record is the multi-line Header (H) Record, followed by the I and J Records that list extension data which applies to later Record types in the file. These are followed by other Record types indicating that certain data is recorded in the file, including the task/declaration (C) Record, and the initial Satellite Constellation (F). Time-specific Records follow, placed in the file in time order using either GNSS fix-time (if GNSS is locked on) or the FR Real Time Clock (RTC); these are B (fix), E (event), F (constellation change) and K (extension data). The logbook/comments (L) Record data may be placed anywhere after the H, I and J records and can have several lines throughout the file.

The following sequence of Record types is typical:

```
IGC DATA FILE FORMAT — ORDER OF RECORD TYPES IN AN IGC FILE

A  - FR manufacturer and identification  (always first)
H  - File header
I  - Fix extension list
J  - Extension list of data in each K record line
C  - Task/declaration (if used)
L  - Logbook/comments (if used)
D  - Differential GPS (if used)
F  - Initial Satellite Constellation
B  - Fix plus any extension data listed in I Record
B  - Fix plus any extension data listed in I Record
E  - Pilot Event (PEV)
B  - Fix plus any extension data listed in I Record
K  - Extension data as defined in J Record
B  - Fix plus any extension data listed in I Record
B  - Fix plus any extension data listed in I Record
F  - Constellation change
B  - Fix plus any extension data listed in I Record
K  - Extension data as defined in J Record
B  - Fix plus any extension data listed in I Record
E  - Pilot Event (PEV)
B  - Fix plus any extension data listed in I Record
B  - Fix plus any extension data listed in I Record
B  - Fix plus any extension data listed in I Record
K  - Extension data as defined in J Record
L  - Logbook/comments (if used)
G  - Security record  (always last)
```

### 2.4 Units

Data in the IGC file shall use the following unit system:

- **Time** — UTC, obtained from the same GNSS data package from which the recorded lat/long and GPS altitude are also obtained, or, if GPS is not locked on, from the Real-Time Clock in the recorder. Note that UTC is not the same as GPS internal system time, which is different by 18 seconds as of 2026 due to the addition of leap seconds since the GPS system first became operational in January 1980. The correction to UTC available within the GPS system must be applied to time recorded in IGC files. *(AL9)*
- **Distance** — Kilometres and decimal kilometres.
- **Speed** — Kilometres per hour.
- **Date** (of the first line in the B record) — UTC DDMMYY (day, month, year). *(AL6)*
- **Direction** — Degrees True, clockwise from 000 (North).
- **Latitude and Longitude** — Degrees, minutes and decimal minutes with N, S, E, W designators.
- **Altitude** — Metres, separate records for GNSS and pressure altitudes.
- **Pressure** — Hectopascals (same as millibars) to two decimal places.

The above items shall be recorded in the flight log as follows:

**Time — `HHMMSSsss` (UTC)**

- `HH` — Hours, fixed to 2 digits with leading zero where necessary
- `MM` — Minutes, fixed to 2 digits with leading zero where necessary
- `SS` — Seconds, fixed to 2 digits with leading zero where necessary
- `sss` — Decimal seconds: the number of fields available in the Record, less fields already used for HHMMSS *(AL8)*

**Distance — `DDDDddd`**  
Kilometres up to 9999 with leading zeros as required, then three decimal places (last figure is metres).

**Speed — `SSSsss`**

- `SSS` — Fixed to 3 digits with leading zero
- `sss` — Speed decimals available in the Record, less fields used for SSS

**Date — `DDMMYY`**

- `DD` — Day of the month, fixed to 2 digits with leading zero
- `MM` — Month of the year, fixed to 2 digits with leading zero
- `YY` — Year modulo 100, fixed to 2 digits with leading zero

**Direction — `DDDddd`**

- `DDD` — Fixed to 3 digits with leading zero
- `ddd` — Direction decimals available in the Record, less fields used for DDD

**Lat/Long — `DDMMmmmN` / `DDDMMmmmE`**

- `DD` — Latitude degrees with leading zero where necessary
- `DDD` — Longitude degrees with leading zero(s) where necessary
- `MMmmm` — Minutes with leading zero, 3 decimal places (mandatory, not optional)
- `N/S/E/W` — North, South, East, or West as appropriate

**Altitude — `AAAAAaaa`**

- `AAAAA` — Fixed to 5 digits with leading zero
- `aaa` — Altitude decimals available in the Record, less fields used for AAAAA

**Pressure — `PPPPpp`**  
Pressure in hPa (mb) with two decimal places, fixed to 6 digits with leading zero. For example, 1013.25 mb (ISA Sea Level) = `101325`; 980 mb = `098000`.

> **Note:** An altimeter setting may be recorded where the FR feeds a cockpit display (three-letter code ATS, see para 7). However, it must not be used to change the pressure altitude recorded with each fix in the IGC file, which must remain with respect to the ISA sea level datum (1013.25 mb) at all times.

**GNSS Altitude:** Where GNSS altitude is not available (e.g., in the case of a 2D fix), it shall be recorded as zero so that the lack of valid GNSS altitude can be seen during post-flight analysis. *(AL3)*

### 2.5 File Naming

**2.5.1** Short file name style: `YMDCXXXF.IGC`

|Character|Meaning                                                 |
|---------|--------------------------------------------------------|
|`Y`      |Year: value 0–9, cycling every 10 years                 |
|`M`      |Month: 1–9, then A=10, B=11, C=12                       |
|`D`      |Day: 1–9, then A=10, B=11, …, V=31                      |
|`C`      |Manufacturer’s single-character IGC code letter         |
|`XXX`    |Unique FR Serial Number (S/N); 3 alphanumeric characters|
|`F`      |Flight number of the day: 1–9, then A=10 through Z=35   |

**2.5.2** Long file name style. This uses a full set of characters in each field, a hyphen separating each field, with the same order as in the short file name. For example, if the short name is `36HXABC2.IGC`, the equivalent long file name is `2003-06-17-XXX-ABC-02.IGC`. *(AL3)*

**2.5.3** FR Serial Number (S/N). The three-character FR S/N must be used in the A record and be imprinted on the case of the recorder unless there is an easily-accessible electronic display which includes the S/N.

**2.5.3.1** Existing FRs using serial numbers with coded systems where the XXX translates to a different five-number numerical code used in the A record have “Grandfather Rights” and do not need to be changed. New FRs must use the three-alphanumeric system described above.

**2.5.4** Date of flight. The date used in the file name and in the H record (DTE code) is the UTC date of the first valid fix in the flight log transferred after flight — i.e., the date applicable to the time in the first B (fix) record line, not the date at the time of switching on or take-off. *(AL6)*

**2.5.5** Security of file name. The file name is not protected by the electronic security system, which only applies to data within the file itself (see para 2.8). File names may be changed for specific purposes such as competitions. No loss of data or security occurs, since all of the data in the IGC file name is repeated in the file itself in the A and H records. *(AL2)*

**2.5.6** Manufacturer codes. Single- and three-character codes are tabulated below. Manufacturers applying for IGC-approval who are not listed should apply to the Chairman of GFAC for allocation of codes. Manufacturers using the IGC file format but not applying for IGC-approval should use the `X` and `XXX` codes.

**2.5.6.1** Name of Intermediate Format file. If a manufacturer uses an intermediate format (e.g., binary), the file name for that intermediate format shall be as for the IGC file but with the manufacturer’s three-letter code used instead of `IGC` after the dot. *(AL8)*

#### Table: Manufacturer Codes for IGC-Approved Flight Recorders *(AL5)*

|1-char|3-char|Manufacturer                        |
|------|------|------------------------------------|
|A     |GCS   |Garrecht                            |
|C     |CAM   |Cambridge Aero Instruments          |
|D     |DSX   |Data Swan/DSX                       |
|E     |EWA   |EW Avionics                         |
|F     |FIL   |Filser                              |
|G     |GCS   |Garrecht (alt.)                     |
|H     |SCH   |Scheffel                            |
|I     |IMI   |IMI Gliding Equipment               |
|K     |NKL   |Nielsen Kellerman                   |
|L     |LGS   |Logstream                           |
|M     |MLE   |MLR Electronics (Posigraph)         |
|N     |NAV   |Naviter                             |
|O     |ONI   |O’I Avionics                        |
|P     |PRT   |Pertholet                           |
|R     |REZ   |Renschler                           |
|S     |SDI   |Streamline Data Instruments         |
|T     |TRI   |Triadis Engineering GmbH            |
|V     |—     |—                                   |
|W     |WAL   |Westerboer                          |
|X     |XXX   |Unknown or non-approved manufacturer|
|Y     |—     |—                                   |
|Z     |ZAN   |Zander                              |


> **Note 1:** New types of FR must use the IGC long file name/ID format; see A2.5 for long and short IGC file names. If data follows the FR ID, a hyphen should be used to separate the file name from data that follows.
> 
> **Note 2:** Manufacturers using the IGC format but not applying for approval should use code `X` (single character) and `XXX` (three characters). These are not allocated to any specific manufacturer.

-----

## 3. Single Instance Data Records

### 3.1 A Record — FR Manufacturer and Identification

The A Record is always the first record in the file. It contains the manufacturer’s IGC code and the unique serial number of the FR.

**Format:**

```
A M M M S S S A D D
```

|Bytes|Description                                                   |
|-----|--------------------------------------------------------------|
|1    |`A` — Record type identifier                                  |
|2–4  |Manufacturer’s three-letter IGC code (e.g., `XXX` for unknown)|
|5–7  |Unique FR Serial Number (S/N) — 3 alphanumeric characters     |
|8–end|Additional data (optional), separated from S/N by a hyphen    |

**Example:**

```
AXXXABC FLIGHT:1
```

> If the manufacturer does not have an allocated IGC code, `XXX` shall be used. Additional free-text data may follow after the S/N, separated by a hyphen.

-----

### 3.2 G Record — Security

The G Record is always the last record in the file. It contains the electronic security value (digital signature/hash) calculated by the FR over the data in the file. Multiple G records are allowed if required by the security algorithm.

**Format:**

```
G C C C C C C C C C C C C C C C C ...
```

|Bytes|Description                                                      |
|-----|-----------------------------------------------------------------|
|1    |`G` — Record type identifier                                     |
|2–end|Security characters — up to 75 characters per line (alphanumeric)|

**Example:**

```
GREJNGJERJKNJKRE31895478537H43982FJN9248F942389T433T
GJNJK2489IERGNV3089IVJE9GO398535J3894N358954983O0934
```

The security system uses a digital signature stored in the G record(s). Validation programs check the G record against the remainder of the file content. The security key/algorithm details are in Appendix B of the specification (manufacturer-specific, held by GFAC).

If the FR has been tampered with or the security microswitch was activated, the `HFFRS` record in the IGC file must be changed to read `SECURITY SUSPECT` (or other relevant data such as `SECURITY MICROSWITCH OPERATED`).

-----

### 3.3 H Record — File Header

The H Record contains header information that describes the flight and the recorder. There are multiple H Record lines, each with a specific sub-type indicated by a three-letter code.

**General format:**

```
H F X X X Subtype text
```

|Bytes|Description                                                       |
|-----|------------------------------------------------------------------|
|1    |`H` — Record type identifier                                      |
|2    |Source: `F` = FR (mandatory), `O` = Official Observer, `P` = Pilot|
|3–5  |Three-letter code (TLC) identifying the data type                 |
|6–end|Data (format depends on TLC)                                      |

#### Mandatory H Records

The following H records are required:

|TLC  |Full name               |Format                                   |Example                                  |
|-----|------------------------|-----------------------------------------|-----------------------------------------|
|`DTE`|Date of flight (UTC)    |`DDMMYY`                                 |`HFDTE160701`                            |
|`FXA`|Fix Accuracy            |3-digit number in metres                 |`HFFXA035`                               |
|`PLT`|Pilot in Charge         |Free text, preceded by `PILOTINCHARGE:`  |`HFPLTPILOTINCHARGE:Bloggs Bill D`       |
|`GTY`|Glider Type             |Free text, preceded by `GLIDERTYPE:`     |`HFGTYGLIDERTYPE:Schleicher ASH-25`      |
|`GID`|Glider ID               |Free text, preceded by `GLIDERID:`       |`HFGIDGLIDERID:N116EL`                   |
|`DTM`|GNSS Datum              |3-digit code and name                    |`HFDTM100GPSDATUM:WGS-1984`              |
|`RFW`|Firmware Revision       |Free text, preceded by `FIRMWAREVERSION:`|`HFRFWFIRMWAREVERSION:6.4`               |
|`RHW`|Hardware Revision       |Free text, preceded by `HARDWAREVERSION:`|`HFRHWHARDWAREVERSION:3.0`               |
|`FTY`|FR Type                 |Free text, preceded by `FRTYPE:`         |`HFFTYFRTYPE:Manufacturer,Model`         |
|`GPS`|GPS Receiver            |Free text                                |`HFGPSMarconini,Superstar,12ch,10000m`   |
|`PRS`|Pressure Altitude Sensor|Free text, preceded by `PRESSALTSENSOR:` |`HFPRSPRESSALTSENSOR:Sensyn,XYZ11,11000m`|
|`FRS`|FR Security             |Security string                          |`HFFRSBASE91HASH`                        |

#### Optional H Records

|TLC  |Full name        |Description                                      |
|-----|-----------------|-------------------------------------------------|
|`CM2`|Crew Member 2    |Second pilot name in a two-seater                |
|`CID`|Competition ID   |Competition registration, e.g., glider fin number|
|`CCL`|Competition Class|Free text, e.g., `Standard`, `15m Motor Glider`  |
|`SIT`|Site             |Takeoff site name                                |
|`TZN`|Time Zone Offset |Offset from UTC of local time, e.g., `+01:00`    |

**H Record date format (`DTE`):**

```
HFDDEMMYY
```

From AL8 onwards, an optional day field is included for the HFDTE record:

```
HFDTEDATE:DDMMYY,NN
```

Where `NN` is the day number (optional; omit for single-day flights).

**Example header block:**

```
HFFXA035
HFDTE160701
HFPLTPILOTINCHARGE:Bloggs Bill D
HFCM2CREW2:Smith-Barry John A
HFGTYGLIDERTYPE:Schleicher ASH-25
HFGIDGLIDERID:N116EL
HFDTM100GPSDATUM:WGS-1984
HFRFWFIRMWAREVERSION:6.4
HFRHWHARDWAREVERSION:3.0
HFFTYFRTYPE:Manufacturer,Model
HFGPSMarconi,Superstar,12ch,10000m
HFPRSPRESSALTSENSOR:Sensyn,XYZ11,11000m
HFCIDCOMPETITIONID:B21
HFCCLCOMPETITIONCLASS:15m Motor Glider
```

-----

### 3.4 I Record — Extension to the Fix (B) Record

The I Record defines additional data fields appended to each B (fix) record line. It appears only once in the file, before the first B record.

**Format:**

```
I N N S S E E T L C S S E E T L C ...
```

|Bytes         |Description                                        |
|--------------|---------------------------------------------------|
|1             |`I` — Record type identifier                       |
|2–3           |`NN` — Number of extensions defined (2 digits)     |
|Per extension:|                                                   |
|4–5           |`SS` — Start byte of extension data within B record|
|6–7           |`EE` — End byte of extension data within B record  |
|8–10          |`TLC` — Three-letter code identifying the data type|

**Example:**

```
I033638FXA3940SIU4143ENL
```

This defines 3 extensions:

- Bytes 36–38: FXA (Fix Accuracy)
- Bytes 39–40: SIU (Satellites In Use)
- Bytes 41–43: ENL (Engine Noise Level)

> **Note:** FXA is the only mandatory extension (as of AL3). ENL is mandatory if any engine is fitted to the aircraft. ENL must follow FXA and SIU in the I record if those are recorded.

-----

### 3.5 J Record — Extension to the K Record

The J Record defines additional data fields in K (extension) records. It appears only once in the file. Its format is identical to the I record but applies to K records instead of B records.

**Format:**

```
J N N S S E E T L C ...
```

**Example:**

```
J010812HDT
```

This defines 1 extension for the K record:

- Bytes 8–12: HDT (True Heading)

-----

### 3.6 C Record — Task/Declaration

The C Record contains the pre-flight task declaration. It is optional. The first C record line contains the declaration details; subsequent lines each define a waypoint.

**First C Record line format:**

```
C D D M M Y Y H H M M S S D D M M Y Y N N N N T T f r e e t e x t
```

|Bytes |Description                                                  |
|------|-------------------------------------------------------------|
|1     |`C` — Record type identifier                                 |
|2–7   |`DDMMYY` — Date of declaration (UTC)                         |
|8–13  |`HHMMSS` — Time of declaration (UTC)                         |
|14–19 |`DDMMYY` — Date of intended flight (UTC)                     |
|20–23 |`NNNN` — Task number (0001–9999)                             |
|24–25 |`TT` — Number of turn points (not including Start and Finish)|
|26–end|Free text — task description                                 |

**Subsequent C Record lines (waypoints):**

```
C D D M M m m m N D D D M M m m m E t e x t
```

|Bytes |Description                          |
|------|-------------------------------------|
|1     |`C` — Record type identifier         |
|2–9   |Latitude `DDMMmmmN`                  |
|10–17 |Longitude `DDDMMmmmE`                |
|18–end|Free text — waypoint name/description|

**Example declaration (500 km triangle from Lasham, UK):**

```
C150701213841160701000102500K Tri
C5111359N00101899WLasham Clubhouse
C5110179N00102644WLasham Start S, Start
C5209092N00255227WSarnesfield, TP1
C5230147N00017612WNorman Cross, TP2
C5110179N00102644WLasham Start S, Finish
C5111359N00101899WLasham Clubhouse
```

The order of C Record waypoint lines is:

1. Take-off location
1. Start of Speed Section (or Start)
1. Turnpoint 1
1. … (additional turnpoints)
1. Finish of Speed Section (or Finish)
1. Landing location

-----

## 4. Multiple Instance Data Records

### 4.1 B Record — Fix

The B Record is the primary time-series record containing each GNSS position fix. There will be many B records in a file.

**Format:**

```
B H H M M S S D D M M m m m N D D D M M m m m E V P P P P P G G G G G e x t e n s i o n s
```

|Bytes |Field      |Description                                                      |
|------|-----------|-----------------------------------------------------------------|
|1     |Record type|`B`                                                              |
|2–7   |`HHMMSS`   |Fix time (UTC)                                                   |
|8–15  |`DDMMmmmN` |Latitude (degrees, minutes, decimal minutes, N/S)                |
|16–24 |`DDDMMmmmE`|Longitude (degrees, minutes, decimal minutes, E/W)               |
|25    |`V`        |Fix validity: `A` = 3D fix (valid), `V` = 2D fix or invalid      |
|26–30 |`PPPPP`    |Pressure altitude in metres (ISA 1013.25 mb datum), leading zeros|
|31–35 |`GGGGG`    |GNSS altitude in metres (WGS84 ellipsoid), leading zeros         |
|36–end|Extensions |As defined by the I Record                                       |

**Validity flag (`V` field):**

|Value|Meaning                                       |
|-----|----------------------------------------------|
|`A`  |3D GNSS fix — valid, all fields reliable      |
|`V`  |2D GNSS fix or data not valid for IGC purposes|


> **Note on GNSS altitude:** Where GNSS altitude is unavailable (2D fix), it shall be recorded as `00000`.

**Example B record (with FXA, SIU, ENL extensions):**

```
B1602405407121N00249342WA002800042120509950
```

Decoded:

- Time: 16:02:40 UTC
- Latitude: 54° 07.121’ N
- Longitude: 002° 49.342’ W
- Validity: A (3D fix)
- Pressure altitude: 00280 m
- GNSS altitude: 00421 m
- FXA: 205 m
- SIU: 09 satellites
- ENL: 950 (engine running)

-----

### 4.2 E Record — Events

The E Record records a time-stamped event. It must be immediately followed by a B record with the same timestamp giving the position at the time of the event.

**Format:**

```
E H H M M S S T L C e x t r a d a t a
```

|Bytes |Description                                      |
|------|-------------------------------------------------|
|1     |`E` — Record type identifier                     |
|2–7   |`HHMMSS` — Event time (UTC)                      |
|8–10  |`TLC` — Three-letter event code (see para 7)     |
|11–end|Additional data (optional, depends on event type)|

**Example:**

```
E160245PEV
B1602455107126N00149300WA002880042919509020
```

The most common event code is `PEV` (Pilot EVent), used to mark special moments such as when the pilot is inside a Turnpoint Observation Zone. When a PEV is recorded, the FR must then log fixes at 1-second intervals for at least 30 seconds. *(AL10)*

-----

### 4.3 F Record — Satellite Constellation

The F Record records the satellite constellation in view at a given time. It appears once at the beginning of the flight, and again whenever the constellation changes.

**Format:**

```
F H H M M S S I D I D I D ...
```

|Bytes|Description                                     |
|-----|------------------------------------------------|
|1    |`F` — Record type identifier                    |
|2–7  |`HHMMSS` — Time of constellation recording (UTC)|
|8–end|Satellite IDs, each two digits, space-separated |

**Example:**

```
F160240040609123624221821
```

At 16:02:40 UTC, the logger could see 9 satellites with IDs: 04, 06, 09, 12, 36, 24, 22, 18, 21.

-----

### 4.4 K Record — Extension Data

The K Record carries data defined by the J Record — information that needs to be recorded less frequently than fixes (e.g., heading, magnetic variation). Each K record includes a timestamp and the data fields defined by the J record.

**Format:**

```
K H H M M S S d a t a
```

|Bytes|Description                           |
|-----|--------------------------------------|
|1    |`K` — Record type identifier          |
|2–7  |`HHMMSS` — Time (UTC)                 |
|8–end|Data fields as defined by the J Record|

**Example (with heading from J record `J010812HDT`):**

```
K16024800090
```

At 16:02:48 UTC, True Heading = 090°.

> The K record must be accompanied by a B record with the same or adjacent timestamp to provide the position context.

-----

### 4.5 L Record — Logbook/Comments

The L Record is a free-text comment record. It can appear anywhere in the file after the H, I and J records.

**Format:**

```
L T L C f r e e t e x t
```

|Bytes|Description                                                                                                   |
|-----|--------------------------------------------------------------------------------------------------------------|
|1    |`L` — Record type identifier                                                                                  |
|2–4  |Source code: manufacturer 3-letter code, `PLT` (pilot), `OOI` (Official Observer), `PFC` (post-flight comment)|
|5–end|Free text                                                                                                     |

**Example:**

```
LXXXRURITANIAN STANDARD NATIONALS DAY 1
LXXXFLIGHT TIME: 4:14:25, TASK SPEED:58.48KT
```

-----

### 4.6 D Record — Differential GPS

The D Record records the use of a Differential GPS (DGPS) station. It is optional.

**Format:**

```
D Q I D I D I D I D
```

|Bytes|Description                                                   |
|-----|--------------------------------------------------------------|
|1    |`D` — Record type identifier                                  |
|2    |`Q` — `1` = DGPS data available, `2` = DGPS station ID follows|
|3–6  |DGPS Station ID (4 digits)                                    |

**Example:**

```
D20331
```

DGPS station ID = 0331.

-----

## 5. Definitions

|Term     |Definition                                                                       |
|---------|---------------------------------------------------------------------------------|
|**CRLF** |Carriage Return (0x0D) + Line Feed (0x0A) — required at end of each record line  |
|**ENL**  |Engine Noise Level — 3-digit value 000–999 recorded as extension in B record     |
|**FR**   |Flight Recorder — the IGC-approved GNSS recording device                         |
|**FXA**  |Fix Accuracy — estimated horizontal accuracy of fix, in metres                   |
|**GFAC** |GNSS Flight Recorder Approval Committee — FAI/IGC body responsible for approvals |
|**GNSS** |Global Navigation Satellite System — includes GPS, GLONASS, Galileo, etc.        |
|**GPS**  |Global Positioning System — the US GNSS system                                   |
|**IGC**  |International Gliding Commission — the FAI body responsible for gliding standards|
|**ISA**  |International Standard Atmosphere — sea level pressure 1013.25 hPa               |
|**MOP**  |Means Of Propulsion — 3-digit extension field in B record                        |
|**NAC**  |National Airsport Control body                                                   |
|**PEV**  |Pilot EVent — button-press event by the pilot, stored as an E record             |
|**RTC**  |Real Time Clock — internal clock in the FR used when GNSS is not locked          |
|**S/N**  |Serial Number — unique 3-alphanumeric identifier for each FR unit                |
|**SIU**  |Satellites In Use — count of satellites used in the position fix                 |
|**TLC**  |Three-Letter Code — used to identify data fields throughout the IGC format       |
|**UTC**  |Coordinated Universal Time — all times in IGC files are UTC                      |
|**WGS84**|World Geodetic System 1984 — the GNSS altitude reference ellipsoid               |

-----

## 6. Valid Characters

Only the following characters are valid in an IGC file:

|Category          |Characters|
|------------------|----------|
|Upper-case letters|`A` to `Z`|
|Digits            |`0` to `9`|
|Space             |` ` (0x20)|
|Hyphen/Minus      |`-`       |
|Plus sign         |`+`       |
|Period/Full stop  |`.`       |
|Comma             |`,`       |
|Colon             |`:`       |
|Slash             |`/`       |


> **Note:** Accented characters, lower-case letters, and other special characters are **not** valid. Such characters occurring in names (e.g., airfield names with umlauts) must be replaced by their nearest valid equivalent.

-----

## 7. Three-Letter Codes (TLC)

Three-letter codes (TLCs) are used throughout the IGC format to identify data fields in I, J, H, and E records. The following table lists defined TLCs:

### Extension TLCs (used in I and J records)

|TLC  |Full Name                            |Unit/Format       |Notes                             |
|-----|-------------------------------------|------------------|----------------------------------|
|`ENL`|Engine Noise Level                   |000–999           |Mandatory if engine fitted        |
|`FXA`|Fix Accuracy                         |metres, 3 digits  |Mandatory extension in B record   |
|`SIU`|Satellites In Use                    |count, 2 digits   |                                  |
|`MOP`|Means Of Propulsion                  |3 digits          |Must follow SIU if ENL is recorded|
|`TAS`|True Air Speed                       |km/h              |                                  |
|`GSP`|Ground SPeed                         |km/h              |                                  |
|`TRT`|Track True                           |degrees           |                                  |
|`TRM`|Track Magnetic                       |degrees           |                                  |
|`OAT`|Outside Air Temperature              |degrees Celsius   |                                  |
|`HDT`|Heading True                         |degrees           |                                  |
|`HDM`|Heading Magnetic                     |degrees           |                                  |
|`WDI`|Wind Direction                       |degrees True      |                                  |
|`WVE`|Wind Velocity                        |km/h              |                                  |
|`VAT`|Compensated variometer (total energy)|m/s               |                                  |
|`ACZ`|Acceleration, normal (Z-axis)        |m/s²              |                                  |
|`GFO`|G-Force                              |(dimensionless)   |                                  |
|`ATS`|Altimeter Setting                    |hPa × 100 (PPPPpp)|                                  |
|`RAI`|Runway Altitude ISA                  |metres            |                                  |
|`RAW`|Runway Altitude WGS84                |metres            |                                  |

### Event TLCs (used in E records)

|TLC  |Event              |Description                                      |
|-----|-------------------|-------------------------------------------------|
|`PEV`|Pilot EVent        |Button press by pilot; triggers 1-second fix rate|
|`PFC`|Post-Flight Comment|Added after flight                               |
|`STA`|Start              |Start of speed section                           |
|`FIN`|Finish             |Finish of speed section                          |
|`WTP`|WayPoint           |Aircraft is in/at a waypoint OZ                  |

### Header TLCs (used in H records)

|TLC  |Full Name               |Format                                     |
|-----|------------------------|-------------------------------------------|
|`ATC`|ATC call sign           |Free text                                  |
|`CCL`|Competition Class       |Free text                                  |
|`CID`|Competition ID          |Free text                                  |
|`CM2`|Crew Member 2           |Free text                                  |
|`DTE`|Date                    |`DDMMYY`                                   |
|`DTM`|GNSS Datum              |Code + name                                |
|`FRS`|FR Security             |Security string                            |
|`FTY`|FR Type                 |Manufacturer, model                        |
|`FXA`|Fix Accuracy            |Metres                                     |
|`GID`|Glider ID               |Free text (registration)                   |
|`GPS`|GPS receiver            |Manufacturer, model, channels, max altitude|
|`GTY`|Glider Type             |Free text                                  |
|`OOI`|Official Observer ID    |Free text                                  |
|`PLT`|Pilot in charge         |Free text                                  |
|`PRS`|Pressure Altitude Sensor|Manufacturer, model, max altitude          |
|`RFW`|Firmware revision       |Free text                                  |
|`RHW`|Hardware revision       |Free text                                  |
|`SIT`|Site/Airfield           |Free text                                  |
|`TZN`|Time zone offset        |`±HH:MM`                                   |

-----

## 8. GNSS Geodetic Datums

The datum code used in the `HFDTM` header record is a three-digit number. The primary datum is:

|Code |Name    |Description                                                                                |
|-----|--------|-------------------------------------------------------------------------------------------|
|`100`|WGS-1984|World Geodetic System 1984 — the standard GNSS datum; must be used for all IGC-format files|

All latitudes and longitudes in the B, C, and E records must be in WGS-1984. If a different datum is used by the GNSS receiver internally, it must be converted to WGS-1984 before recording in the IGC file.

Other datum codes may be defined in the full specification; however, WGS-1984 (`100`) is the only datum currently accepted for IGC validation purposes.

-----

## 9. Example IGC-Format File

The following is a complete example of an IGC-format file. Spaces have been added for readability; in a real file, fields are concatenated without spaces.

```
AXXXABC FLIGHT:1
HFFXA035
HFDTE160701
HFPLTPILOTINCHARGE:Bloggs Bill D
HFCM2CREW2:Smith-Barry John A
HFGTYGLIDERTYPE:Schleicher ASH-25
HFGIDGLIDERID:N116EL
HFDTM100GPSDATUM:WGS-1984
HFRFWFIRMWAREVERSION:6.4
HFRHWHARDWAREVERSION:3.0
HFFTYFRTYPE:Manufacturer,FunkyLogger77
HFGPSMarconi,Superstar,12ch,10000m
HFPRSPRESSALTSENSOR:Sensyn,XYZ11,11000m
HFCIDCOMPETITIONID:B21
HFCCLCOMPETITIONCLASS:15m Motor Glider
I033638FXA3940SIU4143ENL
J010812HDT
C150701213841160701000102500K Tri
C5111359N00101899WLasham Clubhouse
C5110179N00102644WLasham Start S, Start
C5209092N00255227WSarnesfield, TP1
C5230147N00017612WNorman Cross, TP2
C5110179N00102644WLasham Start S, Finish
C5111359N00101899WLasham Clubhouse
F1602400406091236242218 21
B1602405407121N00249342WA002800042120509950
B1602455107126N00149300WA002880042919509020
B1602505107134N00149283WA002900043221009015
B1602555107140N00149221WA002900043020009012
B1603005107150N00149202WA002910043225608009
D20331
E160245PEV
B1602455107126N00149300WA002880042919509020
B1603055107180N00149185WA002910043521008015
B1603105107212N00149174WA002930043519608024
K16024800090
B1602485107220N00149150WA004940043619008018
B1602525107330N00149127WA004960043919508015
LXXXRURITANIAN STANDARD NATIONALS DAY 1
LXXXFLIGHT TIME: 4:14:25, TASK SPEED:58.48KT
GREJNGJERJKNJKRE31895478537H43982FJN9248F942389T433T
GJNJK2489IERGNV3089IVJE9GO398535J3894N358954983O0934
GSKTO5427FGTNUT5621WKTC6714FT8957FGMKJ134527FGTR6751
GK2489IERGNV3089IVJE39GO398535J3894N358954983FTGY546
G12560DJUWT28719GTAOL5628FGWNIST78154INWTOLP7815FITN
```

### Annotated walkthrough

|Record             |Meaning                                                                                                      |
|-------------------|-------------------------------------------------------------------------------------------------------------|
|`AXXXABC FLIGHT:1` |Manufacturer code `XXX`, unit serial number `ABC`, additional info `FLIGHT:1`                                |
|`HFFXA035`         |Typical fix accuracy: 35 metres                                                                              |
|`HFDTE160701`      |Flight date: 16 July 2001 (UTC)                                                                              |
|`HFPLT...`         |Pilot in charge: Bloggs Bill D                                                                               |
|`HFGTY...`         |Glider type: Schleicher ASH-25                                                                               |
|`I03...`           |3 B-record extensions: FXA (bytes 36–38), SIU (39–40), ENL (41–43)                                           |
|`J01...`           |1 K-record extension: HDT True Heading (bytes 8–12)                                                          |
|`C150701...`       |Task declaration: 500K Tri, declared on 15 Jul 2001 at 21:38:41, for flight on 16 Jul                        |
|`C5110179N...Start`|Start waypoint at Lasham                                                                                     |
|`F160240...`       |Satellite constellation at 16:02:40: 9 satellites in view                                                    |
|`B160240...`       |Fix at 16:02:40 — lat 54°07.121’N, lon 002°49.342’W, press alt 280m, GNSS alt 421m, FXA=205m, SIU=09, ENL=950|
|`E160245PEV`       |Pilot Event at 16:02:45                                                                                      |
|`K160248...`       |Extension data at 16:02:48: True Heading = 090°                                                              |
|`LXXX...`          |Comment records                                                                                              |
|`G...` (×5)        |Security hash records — always last                                                                          |

-----

*End of Appendix A*

-----

> **References:**
> 
> - FAI/IGC Technical Specification for IGC-Approved GNSS Flight Recorders, January 2026 with AL10
> - Amendment AL10 (January 2026) — added section 1.1.1.4 on internal-power recorders
> - Amendment AL8 (2023) — updated time format and intermediate file naming
> - Amendment AL9 — UTC/GPS leap second correction requirement
> - Amendment AL6 — distance/speed unit conversions, date format
> - Amendment AL5 — manufacturer codes table
> - Amendment AL3 — production, transfer and baseline requirements
