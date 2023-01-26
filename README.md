# Volcanic-Interpretation-Workbench
A Docker-Dash application for interpreting InSAR measurements of Canadian Volcanoes


![Screen Shot 2023-01-26 at 3 57 31 PM](https://user-images.githubusercontent.com/7228960/214976899-a2b3e2c8-1187-43d8-bd5b-0bdad686b11b.png)


Build the Docker image with a command simmilar to
docker build volcanic-interpretation-workbench .

Start Docker container with a command like:
`sudo docker run -p 8050:8050/tcp --name volc_interp_wb volc_interp_wb &
