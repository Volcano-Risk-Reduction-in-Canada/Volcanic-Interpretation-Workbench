#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
"""
import logging
import os
import botocore.exceptions
import yaml

from scripts_config import get_config_params, s3


def get_latest_baselines():
    '''Main function, get latest perpendicular
    baseline files for all site/beam combos'''
    config = get_config_params()
    logging.info('RUNNING get_latest_baselines')
    with open('app/Data/beamList.yml', encoding="utf-8") as beam_list_yml:
        beam_list = yaml.safe_load(beam_list_yml)
        print(beam_list)
    for site in beam_list:
        for beam in beam_list[site]:
            print(f'Site: {site}, Beam: {beam}')
            if not os.path.exists(f'app/Data/{site}/{beam}'):
                os.makedirs(f'app/Data/{site}/{beam}')
            try:
                s3.download_file(
                    Bucket=config['AWS_BUCKET_NAME'],
                    Key=f'{site}/{beam}/bperp_all',
                    Filename=f'app/Data/{site}/{beam}/bperp_all'
                )
            except botocore.exceptions.ClientError:
                print('Perpendicular Baseline File not found')
    logging.info('DONE get_latest_baselines')
