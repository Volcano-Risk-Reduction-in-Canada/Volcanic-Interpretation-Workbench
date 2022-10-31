docker build -t volc_interp_wb .

docker run -p 8050:8050/tcp --name volc_interp_wb volc_interp_wb &

