#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
"""

import os
import yaml
import boto3

from app.data_utils import get_config_params


def main():
    '''Main function, retrieve latest coherence
    matrix files for all site/beam combos'''
    config = get_config_params()
    s_3 = boto3.client('s3')

    os.chdir('app/Data/')

    with open('beamList.yml', encoding="utf-8") as beam_list_yml:
        beam_list = yaml.safe_load(beam_list_yml)
    for site in beam_list:
        for beam in beam_list[site]:
            print(f'Site: {site}, Beam: {beam}')
            if not os.path.exists(f'{site}/{beam}'):
                os.makedirs(f'{site}/{beam}')

            s_3.download_file(Bucket=config['AWS_BUCKET_NAME'],
                              Key=f'{site}/{beam}/CoherenceMatrix.csv',
                              Filename=f'{site}/{beam}/CoherenceMatrix.csv')


if __name__ == '__main__':
    main()
