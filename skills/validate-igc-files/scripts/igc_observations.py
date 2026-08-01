"""Per-file measurements that are reported but never affect conformance.

These answer 'what should a scrutineer look at?' rather than 'is this file
well formed?', so they are deliberately kept out of the rule registry.
"""

import math

# A running engine reads 700+; aerotow noise sits around 400-500. Isolated
# high readings are radio calls, gear warnings or vario beeps, so engine-on is
# only declared for a continuous run - a bare threshold flags ~75% of pure
# glider files.
ENL_ENGINE_ON = 500
ENL_MIN_RUN_SECONDS = 30

# Above this speed between consecutive valid fixes the position data is not
# physically plausible. A handful of events is flight-recorder clock tolerance;
# a cluster suggests GPS jamming or spoofing.
SPOOF_MAX_KNOTS = 300
SPOOF_CLUSTER = 5

_EARTH_RADIUS_NM = 3440.065          # nautical miles
# Below this coordinate delta no pair can exceed SPOOF_MAX_KNOTS at a 1s
# interval, so the trigonometry can be skipped. Keeps the sweep cheap across
# ~19,000 fixes per file.
_DELTA_PREFILTER_DEG = 0.05


def _hms(seconds):
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def enl_engine_on(doc):
    """Return engine-noise stats when the file shows a sustained run, else None."""
    values = [(f.time, int(f.ext["ENL"]))
              for f in doc.fixes
              if f.ext.get("ENL", "").isdigit()]
    if not values:
        return None

    runs, start, end = [], None, None
    high = 0
    for t, v in values:
        if v > ENL_ENGINE_ON:
            high += 1
            if start is None:
                start = t
            end = t
        elif start is not None:
            runs.append((start, end))
            start = end = None
    if start is not None:
        runs.append((start, end))

    long_runs = [(s, e) for s, e in runs if e - s >= ENL_MIN_RUN_SECONDS]
    if not long_runs:
        return None

    s, e = max(long_runs, key=lambda r: r[1] - r[0])
    return {
        "max": max(v for _, v in values),
        "high": high,
        "fixes": len(values),
        "n_runs": len(long_runs),
        "longest": f"{_hms(s)}-{_hms(e)} UTC ({e - s}s)",
    }


def _distance_nm(lat1, lon1, lat2, lon2):
    """Great-circle distance on the IGC sphere, which the rules document
    permits in place of Vincenty."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = (math.sin(dp / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * _EARTH_RADIUS_NM * math.asin(min(1.0, math.sqrt(a)))


def gps_anomaly(doc):
    """Return groundspeed-anomaly stats, or None when the track is plausible."""
    valid = [f for f in doc.fixes if f.valid == "A"]
    events, max_knots, first = 0, 0.0, None

    for prev, cur in zip(valid, valid[1:]):
        dt = cur.time - prev.time
        if dt <= 0:
            continue
        if (abs(cur.lat - prev.lat) < _DELTA_PREFILTER_DEG * dt
                and abs(cur.lon - prev.lon) < _DELTA_PREFILTER_DEG * dt):
            continue
        knots = _distance_nm(prev.lat, prev.lon, cur.lat, cur.lon) / (dt / 3600.0)
        if knots > SPOOF_MAX_KNOTS:
            events += 1
            if knots > max_knots:
                max_knots = knots
            if first is None:
                first = _hms(cur.time)

    if not events:
        return None
    return {
        "events": events,
        "cluster": events >= SPOOF_CLUSTER,
        "max_knots": round(max_knots),
        "first": first,
    }
