# ### Old way to run ###
# docker build -t volc_interp_wb .
# docker run -p 8050:8050/tcp --name volc_interp_wb volc_interp_wb &

# ### Run using Docker Compose ###
#
# Build the image
docker build -t volc_interp_wb .
# Build container and Run
docker-compose up
# Stop and remove containers
docker-compose down

