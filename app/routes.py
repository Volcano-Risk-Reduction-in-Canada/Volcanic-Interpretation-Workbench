#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2024 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
"""
from flask import Response, request
import requests
import boto3


def add_routes(server):
    def get_signed_url(bucket, key):
        print(bucket)
        s3_client = boto3.client('s3')
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=60  # URL expires in 60 seconds
        )
        print(url)
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
        response = requests.get(signed_url, timeout=10)
        return Response(response.content, mimetype='image/png')
