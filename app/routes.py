# routes.py
from flask import jsonify, request
import boto3
from dash_app import server



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
    x = request.args.get('x')
    y = request.args.get('y')
    z = request.args.get('z')
    key = f"Meager/5M3/20220809_20220914/{z}/{x}/{y}.png"
    TILES_BUCKET = "vrrc-insar-tiles-store-dev"
    signed_url = get_signed_url(TILES_BUCKET, key)
    return jsonify({'signedUrl': signed_url})



