#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Chloe Lam <chloe.lam@nrcan-rncan.gc.ca>
"""

import os
from dotenv import load_dotenv


def get_config_params():
    """
    Retrieve configuration parameters from environment variables.

    This function loads variables from a .env file into the environment
    and retrieves specific environment variables related to AWS, API,
    and other configurations. It creates a dictionary storing these
    configuration parameters and returns it.

    Returns:
        dict: A dictionary containing configuration parameters. Keys
        correspond to environment variable names, and values are the
        corresponding values retrieved from the environment.
    """
    # Load variables from .env file into environment
    load_dotenv()
    # List of environment variable names
    env_variables = [
        'AWS_BUCKET_NAME',
        'AWS_RAW_BUCKET',
        'AWS_TILES_URL',
        'API_VRRC_IP',
        'WORKBENCH_HOST',
        'WORKBENCH_PORT'
    ]
    # Dictionary to store configuration parameters
    config_params = {}
    # Retrieve configuration parameters using os.getenv()
    # and store them in the dictionary
    for var_name in env_variables:
        config_params[var_name] = os.getenv(var_name)
    # Return the dictionary of configuration parameters
    return config_params
