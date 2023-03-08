# Volcanic-Interpretation-Workbench
A Docker-Dash application for interpreting InSAR measurements of Canadian Volcanoes

![Screen Shot 2023-01-26 at 3 57 31 PM](https://user-images.githubusercontent.com/7228960/214976899-a2b3e2c8-1187-43d8-bd5b-0bdad686b11b.png)

## Quick start

Before the first run, create `app/config.ini` from the sample and edit as necessary:
```
cp -iv app/sample_config.ini app/config.ini
```

Build the Docker image with a command similar to:
```
docker build -t volc_interp_wb .
```

Start Docker container with a command like:
```
docker run -p 8050:8050/tcp --name volc_interp_wb volc_interp_wb &
```

See also `runDocker.sh`
