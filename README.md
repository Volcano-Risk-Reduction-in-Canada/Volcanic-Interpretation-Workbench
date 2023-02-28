# Volcanic-Interpretation-Workbench
A Docker-Dash application for interpreting InSAR measurements of Canadian Volcanoes


![Screen Shot 2023-01-26 at 3 57 31 PM](https://user-images.githubusercontent.com/7228960/214976899-a2b3e2c8-1187-43d8-bd5b-0bdad686b11b.png)

## Deployment

### Docker

Build the Docker image with a command simmilar to
docker build volcanic-interpretation-workbench .

Start Docker container with a command like:
```bash
sudo docker run -p 8050:8050/tcp --name volc_interp_wb volc_interp_wb &
```

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
