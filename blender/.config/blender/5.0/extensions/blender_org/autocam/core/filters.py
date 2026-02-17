"""
Signal processing utilities for rotation key data.

- _unwrap_euler(): unwraps Euler angle sequences to avoid 2pi jumps.
- Key reduction: _simplify_flat_runs(), _simplify_sliding_window(), _rdp_1d(), _simplify_best().
- Smoothing: zero-phase, detrended 2nd-order Butterworth via _biquad_zero_phase() with cutoff from UI using _cutoff_from_slider().

"""


import math


def _unwrap_euler(values):
    if not values:
        return values
    out = [values[0]]
    prev = values[0]
    for v in values[1:]:
        dv = v - prev
        two_pi = 2.0 * math.pi
        while dv > math.pi:
            v -= two_pi
            dv = v - prev
        while dv < -math.pi:
            v += two_pi
            dv = v - prev
        out.append(v)
        prev = v
    return out


def _simplify_flat_runs(frames, values, epsilon):
    n = len(values)
    if n < 3 or epsilon <= 0.0:
        return frames[:], values[:]
    keep_f = [frames[0]]
    keep_v = [values[0]]
    last = values[0]
    for i in range(1, n - 1):
        if abs(values[i] - last) > epsilon:
            keep_f.append(frames[i])
            keep_v.append(values[i])
            last = values[i]
    # always keep the last key
    if keep_f[-1] != frames[-1]:
        keep_f.append(frames[-1])
        keep_v.append(values[-1])
    return keep_f, keep_v


def _butter_zero_phase_detrended(seg, cutoff_norm):
    n = len(seg)
    if n < 3:
        return seg[:]
    y0, y1 = seg[0], seg[-1]
    base = []
    if n == 1 or n == 2:
        base = [y0] * n
    else:
        inv = 1.0 / (n - 1)
        base = [y0 + (i * inv) * (y1 - y0) for i in range(n)]
    detr = [seg[i] - base[i] for i in range(n)]
    sm = _biquad_zero_phase(detr, cutoff_norm=cutoff_norm)
    out = [sm[i] + base[i] for i in range(n)]
    return out


def _butterworth_coeffs(cutoff_norm, q=1 / math.sqrt(2)):
    cutoff_norm = max(1e-4, min(0.5, float(cutoff_norm)))
    w0 = math.pi * (cutoff_norm / 0.5)  # normalize to Nyquist
    cw = math.cos(w0)
    sw = math.sin(w0)
    alpha = sw / (2 * q)

    b0 = (1 - cw) * 0.5
    b1 = 1 - cw
    b2 = (1 - cw) * 0.5
    a0 = 1 + alpha
    a1 = -2 * cw
    a2 = 1 - alpha

    b0 /= a0
    b1 /= a0
    b2 /= a0
    a1 /= a0
    a2 /= a0
    return b0, b1, b2, a1, a2


def _biquad_zero_phase(vals, cutoff_norm):
    n = len(vals)
    if n < 5:
        return vals[:]

    b0, b1, b2, a1, a2 = _butterworth_coeffs(cutoff_norm)

    pad = min(max(6, n // 8), n - 2)
    left = vals[1:pad+1][::-1]
    right = vals[-pad-1:-1][::-1]
    ext = left + vals + right

    def filt(seq):
        y1 = y2 = 0.0
        x1 = x2 = 0.0
        out = []
        for x in seq:
            y = b0*x + b1*x1 + b2*x2 - a1*y1 - a2*y2
            out.append(y)
            x2, x1 = x1, x
            y2, y1 = y1, y
        return out

    y = filt(ext)
    y.reverse()
    y = filt(y)
    y.reverse()

    y = y[pad:pad + n]

    y[0] = vals[0]
    y[-1] = vals[-1]
    return y


def simplify_rdp(frames, values, epsilon):
    """
    Iterative Ramer-Douglas-Peucker simplification.
    Guarantees monotonic simplification (higher epsilon = fewer keys).
    """
    n = len(values)
    if n < 3 or epsilon <= 0.0:
        return frames[:], values[:]

    # Stack for iterative processing: (start_index, end_index)
    stack = [(0, n - 1)]
    keep = {0, n - 1}

    while stack:
        start, end = stack.pop()
        
        # Skip if segment is too small
        if end <= start + 1:
            continue

        x0, x1 = frames[start], frames[end]
        y0, y1 = values[start], values[end]

        dmax = -1.0
        idx = -1

        # Standard line equation check
        if x1 == x0:
            # Vertical segment (shouldn't happen in time-series but good for safety)
            for i in range(start + 1, end):
                d = abs(values[i] - y0)
                if d > dmax:
                    dmax = d
                    idx = i
        else:
            # Normal time-series segment
            inv = 1.0 / (x1 - x0)
            dy = y1 - y0
            for i in range(start + 1, end):
                t = (frames[i] - x0) * inv
                y_est = y0 + t * dy
                d = abs(values[i] - y_est)
                if d > dmax:
                    dmax = d
                    idx = i

        if dmax > epsilon:
            keep.add(idx)
            stack.append((start, idx))
            stack.append((idx, end))

    idxs = sorted(keep)
    return [frames[i] for i in idxs], [values[i] for i in idxs]


def _cutoff_from_slider(val, max_cutoff=0.5, min_cutoff=5e-6):
    decades = max(0.0, float(val)) / 10.0
    ratio = (min_cutoff / max_cutoff)
    cutoff = max_cutoff * (ratio ** decades)
    return max(min_cutoff, min(max_cutoff, cutoff))
