# Volcanic-Interpretation-Workbench
![flake8](https://github.com/Volcano-Risk-Reduction-in-Canada/Volcanic-Interpretation-Workbench/actions/workflows/flake8.yml/badge.svg)
![pylint](https://github.com/Volcano-Risk-Reduction-in-Canada/Volcanic-Interpretation-Workbench/actions/workflows/pylint.yml/badge.svg)

A Docker-Dash application for interpreting InSAR measurements of Canadian Volcanoes

![Screen Shot 2023-01-26 at 3 57 31 PM](https://user-images.githubusercontent.com/7228960/214976899-a2b3e2c8-1187-43d8-bd5b-0bdad686b11b.png)

## Deployment

### General

Before the first run, create `config.ini` from the sample and edit as necessary:
```
cp -iv sample_config.ini onfig.ini
```

### Docker

Build the Docker image with a command similar to:
```
docker build -t volc_interp_wb .
```

Start Docker container with a command like:
```bash
sudo docker run -p 8050:8050/tcp --name volc_interp_wb volc_interp_wb &
```

See also `runDocker.sh`.

### VSCode (development)

Create an appropriate conda environment:
```bash
conda env create --file vrrc.yml
```
(If the correct version of python is already available on your system,
this could instead be done using a virtualenv.)

Upon first run, and periodically thereafter, the AWS environment variables for "Command line or programmatic access" must be updated, from https://nrcan-rncan.awsapps.com/start#/.

For each session with the workbench, the user must complete the two-factor authentication to login to AWS using:
```bash
aws sso login
```

Find the `vrrc-insar-geoserver` instance ID among the running EC2 instances in `landmass-sandbox`.

Start forwarding local port 8080 to remote port 8080 of the geoserver instance using:
```bash
aws ssm start-session --target <GEOSERVER_INSTANCE_ID> --document-name AWS-StartPortForwardingSession --parameters "portNumber"=["8080"],"localPortNumber"=["8080"]
```

Activate the `vrrc` environment in VSCode and use the launch.json configuration to debug. This is equivalent to:
```bash
conda activate vrrc
cd app
python dash_app.py
```

Either way, VSCode will automatically open port 8050 for the app, and you will be able to interact with the workbench at http://localhost:8050/ on your local machine.

If ever the dependencies change, update the conda environment using:
```bash
conda env update --prune --file vrrc.yml
```

### Utility Scripts (Python)


Utility scripts are included in the dashbaord to get the latest coherence and baseline data. They will usually be run automatically when new SAR imagery is ingested and processed however they can be run manually as well to update coherence and baseline data locally. The user will need to be authenticated with the relevant cloud environment prior to running the script. 

Scripts may have optional or mandatory arguments. Scripts requiring arguments will contain instructions via the --help argument. For example:

```python loadUpdatedCoherenceMatrix.py --help
usage: loadUpdatedCoherenceMatrix.py [-h] --site SITE --beam BEAM

Copy latest coherence matrix into

optional arguments:
  -h, --help   show this help message and exit
  --site SITE  Volcano Site Name, i.e. 'Meager'
  --beam BEAM  RCM Beam Mode Mnemonic, i.e. '5M3'
```
Other scripts do not require arguments and can simply be run as is. For example:

- Get the latest baseline file for every site/beam combo specific in app/beamList.yml

    `python get_latest_baselines.py`

- Get the latest coherence matrix csv files for every site/beam combo specific in app/beamList.yml

    `python getLatestCohMatrices.py`
