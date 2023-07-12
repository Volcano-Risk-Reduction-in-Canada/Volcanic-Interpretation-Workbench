#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
"""
import argparse
import configparser
import boto3


def main():
    args = parse_args()
    config = get_config_params("config.ini")

    # Copy file from S3 into filesystem
    s3 = boto3.client('s3')
    s3.download_file(Bucket=config.get('AWS', 'bucketName'),
                     Key=f'{args.site}/{args.beam}/CoherenceMatrix.csv',
                     Filename=f'Data/{args.site} \
                               /{args.beam}/CoherenceMatrix.csv')


def get_config_params(args):
    """
    Parse Input/Output columns from supplied *.ini file
    """
    configParseObj = configparser.ConfigParser()
    configParseObj.read(args)
    return configParseObj


def parse_args():
    parser = argparse.ArgumentParser(
        description="Copy latest coherence matrix into ")
    parser.add_argument("--site",
                        type=str,
                        help="Volcano Site Name, i.e. 'Meager'",
                        required=True)
    parser.add_argument("--beam",
                        type=str,
                        help="RCM Beam Mode Mnemonic, i.e. '5M3'",
                        required=True)
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    main()
