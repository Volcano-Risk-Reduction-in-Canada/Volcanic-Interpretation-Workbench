#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT
file
Copyright (C) 2021-2023 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
"""

from scripts_config import s3

BUCKET_NAME = 'vrrc-insar-store'
FILE_EXTENSION = '.adf.wrp.geo.tif'


def count_objects_with_extension(bucket_name, file_extension):
    '''Count the number of objects with a specific extension '''
    # Initialize counter for the file count
    file_count = 0
    # Paginator to handle pagination
    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name)
    # Iterate over pages of objects
    for page in page_iterator:
        # Check if Contents key exists in the response
        if 'Contents' in page:
            # Iterate over objects and count files with the specified extension
            for obj in page['Contents']:
                if obj['Key'].endswith(file_extension):
                    file_count += 1
    return file_count


if __name__ == '__main__':
    total_count = count_objects_with_extension(BUCKET_NAME, FILE_EXTENSION)
    print(f'Total {FILE_EXTENSION} files in {BUCKET_NAME}: {total_count}')
