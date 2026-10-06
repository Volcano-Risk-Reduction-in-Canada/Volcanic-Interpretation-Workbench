#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2026 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>

Build vector tiles (MBTiles) and a stats sidecar from a point-target
deformation GeoPackage, for the site page's Timeseries tab.

Inputs/outputs live alongside the site's other data:
    app/Data/{site}/{beam}/{site}_{beam}.gpkg              (input)
    app/Data/{site}/{beam}/{site}_{beam}_points.mbtiles    (vector tiles)
    app/Data/{site}/{beam}/{site}_{beam}_points.json       (stats sidecar)

Only the colour attributes go into the tiles (long-term rate plus per-year
rates, all in mm/yr); the full displacement time series is looked up from
the GeoPackage by fid when a point is clicked.

Requires GDAL's ogr2ogr and tippecanoe on the PATH
(e.g. `brew install gdal tippecanoe`).
"""
import argparse
import json
import os
import re
import sqlite3
import subprocess
import tempfile

import numpy as np

LONG_TERM_RATE_COLUMN = 'deformation rate (mm/y)'
YEARLY_RATE_PATTERN = re.compile(r'^rate_(\d{4})$')
# rate_YYYY columns are stored in m/yr; tiles carry mm/yr.
YEARLY_RATE_SCALE = 1000
TILE_LAYER = 'points'
MIN_ZOOM = 8
MAX_ZOOM = 14
PERCENTILES = [1, 5, 50, 95, 99]


def main():
    """Export the GeoPackage points to MBTiles and write the stats sidecar."""
    args = parse_args()
    data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'app', 'Data', args.site, args.beam
    )
    stem = f'{args.site}_{args.beam}'
    gpkg = os.path.join(data_dir, f'{stem}.gpkg')
    mbtiles = os.path.join(data_dir, f'{stem}_points.mbtiles')
    stats_json = os.path.join(data_dir, f'{stem}_points.json')
    if not os.path.exists(gpkg):
        raise SystemExit(f'GeoPackage not found: {gpkg}')

    con = sqlite3.connect(f'file:{gpkg}?mode=ro', uri=True)
    table = _feature_table(con)
    variables = _tile_variables(con, table)
    print(f'{gpkg}: table "{table}", variables {list(variables)}')

    with tempfile.TemporaryDirectory() as tmp:
        geojsonl = os.path.join(tmp, 'points.geojsonl')
        _export_geojsonseq(gpkg, table, variables, geojsonl)
        _run_tippecanoe(geojsonl, mbtiles)

    stats = _variable_stats(con, table, variables)
    stats['bounds'] = _mbtiles_bounds(mbtiles)
    stats['minzoom'] = MIN_ZOOM
    stats['maxzoom'] = MAX_ZOOM
    with open(stats_json, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f'wrote {stats_json}')
    _print_tile_summary(mbtiles)


def _feature_table(con):
    row = con.execute(
        "SELECT table_name FROM gpkg_contents WHERE data_type = 'features'"
    ).fetchone()
    if row is None:
        raise SystemExit('No feature table in GeoPackage')
    return row[0]


def _tile_variables(con, table):
    """Map tile attribute name -> (SQL expression, label)."""
    columns = [r[1] for r in con.execute(f'PRAGMA table_info("{table}")')]
    if LONG_TERM_RATE_COLUMN not in columns:
        raise SystemExit(f'Missing column "{LONG_TERM_RATE_COLUMN}"')
    variables = {
        'rate': (f'"{LONG_TERM_RATE_COLUMN}"', 'Long-term rate'),
    }
    for column in columns:
        match = YEARLY_RATE_PATTERN.match(column)
        if match:
            year = match.group(1)
            variables[f'r{year}'] = (
                f'"{column}" * {YEARLY_RATE_SCALE}', f'{year} rate'
            )
    return variables


def _export_geojsonseq(gpkg, table, variables, out_path):
    # Rounding to 0.1 mm/yr keeps the per-tile value tables small.
    selects = ', '.join(
        f'ROUND({expr}, 1) AS {name}'
        for name, (expr, _) in variables.items()
    )
    sql = f'SELECT fid, geom, {selects} FROM "{table}"'
    cmd = [
        'ogr2ogr', '-f', 'GeoJSONSeq', out_path, gpkg,
        # Writes fid as each Feature's top-level "id", which tippecanoe
        # carries through as the MVT feature id (what a map click returns).
        '-preserve_fid',
        '-t_srs', 'EPSG:4326',
        '-lco', 'COORDINATE_PRECISION=6',
        '-sql', sql,
    ]
    print('exporting points:', ' '.join(cmd[:6]), '...')
    subprocess.run(cmd, check=True)


def _run_tippecanoe(geojsonl, mbtiles):
    cmd = [
        'tippecanoe',
        '-o', mbtiles,
        '--force',
        '--read-parallel',
        '--layer', TILE_LAYER,
        '--minimum-zoom', str(MIN_ZOOM),
        '--maximum-zoom', str(MAX_ZOOM),
        # Full density at the max zoom; thinned progressively below it.
        '--base-zoom', str(MAX_ZOOM),
        '--drop-densest-as-needed',
        geojsonl,
    ]
    print('building tiles:', ' '.join(cmd))
    subprocess.run(cmd, check=True)


def _variable_stats(con, table, variables):
    exprs = ', '.join(expr for expr, _ in variables.values())
    values = np.array(
        con.execute(f'SELECT {exprs} FROM "{table}"').fetchall(), dtype=float
    )
    stats = {'count': int(values.shape[0]), 'variables': {}}
    for i, (name, (_, label)) in enumerate(variables.items()):
        column = values[:, i]
        column = column[~np.isnan(column)]
        pcts = np.percentile(column, PERCENTILES)
        stats['variables'][name] = {
            'label': label,
            'units': 'mm/yr',
            **{f'p{p}': round(float(v), 2) for p, v in zip(PERCENTILES, pcts)},
            'default_range': _default_range(pcts[1], pcts[3]),
        }
    return stats


def _default_range(p5, p95):
    """Symmetric +/-R, R = max(|p5|, |p95|) rounded to the nearest 5."""
    half = max(5, 5 * round(max(abs(p5), abs(p95)) / 5))
    return [-half, half]


def _mbtiles_bounds(mbtiles):
    con = sqlite3.connect(f'file:{mbtiles}?mode=ro', uri=True)
    row = con.execute(
        "SELECT value FROM metadata WHERE name = 'bounds'"
    ).fetchone()
    con.close()
    return [float(v) for v in row[0].split(',')]


def _print_tile_summary(mbtiles):
    con = sqlite3.connect(f'file:{mbtiles}?mode=ro', uri=True)
    rows = con.execute(
        'SELECT zoom_level, COUNT(*), MAX(LENGTH(tile_data)), '
        'SUM(LENGTH(tile_data)) FROM tiles GROUP BY zoom_level'
    ).fetchall()
    con.close()
    print(f'{mbtiles} ({os.path.getsize(mbtiles) / 1e6:.1f} MB)')
    print(' zoom  tiles  max_kB  total_MB')
    for zoom, count, max_bytes, total_bytes in rows:
        print(f'{zoom:5d} {count:6d} {max_bytes / 1e3:7.1f} '
              f'{total_bytes / 1e6:9.1f}')


def parse_args():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: An object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Build Timeseries-tab vector tiles from a point-target "
                    "deformation GeoPackage")
    parser.add_argument("--site",
                        type=str,
                        help="Volcano Site Name, i.e. 'Meager'",
                        required=True)
    parser.add_argument("--beam",
                        type=str,
                        help="RCM Beam Mode Mnemonic, i.e. '5M10'",
                        required=True)
    return parser.parse_args()


if __name__ == '__main__':
    main()
