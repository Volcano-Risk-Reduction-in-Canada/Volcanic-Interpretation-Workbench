#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2024 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
"""
import logging
from flask import Response, request
import requests

from global_variables import s3

logger = logging.getLogger(__name__)


def add_routes(server):
    """ add routes"""
    def get_signed_url(bucket, key):
        logger.debug("Bucket: %s",
                     bucket)
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=60  # URL expires in 60 seconds
        )
        logger.debug("URL: %s",
                     url)
        return url

    @server.route('/getTileUrl')
    def get_tile_url():
        x = int(request.args.get('x'))
        y = int(request.args.get('y'))
        z = int(request.args.get('z'))
        site = request.args.get('site')
        beam = request.args.get('beam')
        startdate = request.args.get('startdate')
        enddate = request.args.get('enddate')
        bucket = request.args.get('bucket')
        key = f"{site}/{beam}/{startdate}_{enddate}/{z}/{x}/{y}.png"
        signed_url = get_signed_url(bucket, key)
        try:
            response = requests.get(signed_url, timeout=10)
        except requests.exceptions.RequestException as exception:
            # A single flaky/slow tile (e.g. an S3 SSL hiccup) shouldn't
            # take down the whole map -- fail that one tile and let the
            # map keep rendering the rest, instead of raising and
            # returning a slow/uncaught error for this request.
            logger.warning(
                'Failed to fetch interferogram tile %s: %s', key, exception
            )
            return Response(status=204)
        if response.status_code != 200:
            # S3 errors (missing key, expired signature, etc.) come back
            # as a 200-from-Flask's-perspective XML body -- if forwarded
            # as-is with an image/png content type, the browser can't
            # decode it and MapLibre throws mid-render instead of just
            # skipping the tile.
            logger.warning(
                'Interferogram tile %s returned status %s',
                key, response.status_code
            )
            return Response(status=204)
        return Response(response.content, mimetype='image/png')

    @server.route('/getDemTileUrl')
    def get_dem_tile_url():
        """
        Same-origin proxy for the public AWS Open Data elevation-tiles-prod
        Terrarium DEM tiles. MapLibre's raster-dem terrain has to decode
        pixel values client-side (unlike the opaque basemap/interferogram
        raster layers), which requires non-CORS-tainted images -- and the
        bucket only advertises CORS on OPTIONS preflight requests, not on
        the actual GET responses. Proxying same-origin sidesteps that.
        """
        x = int(request.args.get('x'))
        y = int(request.args.get('y'))
        z = int(request.args.get('z'))
        upstream_url = (
            'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/'
            f'{z}/{x}/{y}.png'
        )
        try:
            response = requests.get(upstream_url, timeout=10)
        except requests.exceptions.RequestException as exception:
            logger.warning(
                'Failed to fetch DEM tile %s/%s/%s: %s', z, x, y, exception
            )
            return Response(status=204)
        if response.status_code != 200:
            logger.warning(
                'DEM tile %s/%s/%s returned status %s',
                z, x, y, response.status_code
            )
            return Response(status=204)
        return Response(
            response.content,
            mimetype='image/png',
            headers={'Cache-Control': 'public, max-age=604800'},
        )
