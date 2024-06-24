#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
"""
import argparse
import os
import boto3

from data_utils import get_config_params


def main():
    """
    Main function to execute the coherence matrix copying process.

    This function parses command-line arguments, retrieves configuration
    parameters, and copies the coherence matrix file from an AWS S3 bucket
    into the local filesystem.

    Raises:
        botocore.exceptions.ClientError: If there is an error when
        accessing AWS S3.
    """
    args = parse_args()
    config = get_config_params()

    # Determine the absolute path to the CSV file in the app directory
    current_dir = os.path.dirname(__file__)  # Get the directory of the current script
    csv_file_path = os.path.join(current_dir, '../app/Data', args.site, args.beam, 'CoherenceMatrix.csv')

    # Copy file from S3 into filesystem
    s3 = boto3.client('s3')
    s3.download_file(
        Bucket=config['AWS_BUCKET_NAME'],
        Key=f'{args.site}/{args.beam}/CoherenceMatrix.csv',
        # Filename=f'Data/{args.site}/{args.beam}/CoherenceMatrix.csv')
        Filename=csv_file_path)


def parse_args():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: An object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Copy latest coherence matrix into dashboard application")
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
