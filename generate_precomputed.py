"""Erzeugt `precomputed_pools.json`: je Sicherheitsfaktor eine große Menge unabhängiger Standort-Fenster (Servicegrad).

    python generate_precomputed.py            # etwa eine Minute, nutzt alle Kerne

Jede Einheit ist ein eigener SplitMix64-Strom mit festem Seed (Z-Index, Einheit): das Ergebnis hängt weder von der Zahl der
Prozesse noch von der Plattform ab."""

import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import srm_constants as C
from srm_rng import SplitMix64
from srm_vehicle import window_service_level

OUT = Path(__file__).resolve().parent / "precomputed_pools.json"


def unit_seed(z_index, i):
    return 9_000_011 * (z_index + 1) + 7 * i + 1


def _chunk(args):
    z_index, z, start, stop = args
    return [round(window_service_level(z, SplitMix64(unit_seed(z_index, i))), 6) for i in range(start, stop)]


def main():
    t0 = time.time()
    step = 500
    jobs = [(zi, z, s, min(s + step, C.POOL_SIZE)) for zi, z in enumerate(C.Z_GRID) for s in range(0, C.POOL_SIZE, step)]
    with mp.Pool() as pool:
        parts = pool.map(_chunk, jobs)
    pools = {f"{z:.1f}": [] for z in C.Z_GRID}
    for (zi, z, _s, _e), values in zip(jobs, parts):
        pools[f"{z:.1f}"].extend(values)
    meta = {"pool_size": C.POOL_SIZE, "window_days": C.WINDOW_DAYS, "burn_days": C.BURN_DAYS, "base_mean": C.BASE_MEAN,
            "disp": C.DISP, "lead": C.LEAD, "z_grid": list(C.Z_GRID)}
    OUT.write_text(json.dumps({"meta": meta, "pools": pools}, separators=(",", ":")), encoding="utf-8")
    print(f"{OUT.name}: {len(C.Z_GRID)} Pools à {C.POOL_SIZE} Fenster, {time.time() - t0:.0f} s, "
          f"{OUT.stat().st_size / 1024:.0f} KB", file=sys.stderr)


if __name__ == "__main__":
    main()
