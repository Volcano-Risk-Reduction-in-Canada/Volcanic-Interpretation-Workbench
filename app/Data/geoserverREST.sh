curl -v -u admin:geoserver -XPOST -H "Content-type: text/xml" \
  -d "<workspace><name>landslides</name></workspace>" \
  http://localhost:8080/geoserver/rest/workspaces | json_pp

curl -v -u admin:geoserver -XGET http://localhost:8080/geoserver/rest/workspaces | json_pp


curl -v -u admin:geoserver -XPUT -H "Content-type: application/zip"
  --data-binary @roads.zip
  http://localhost:8080/geoserver/rest/workspaces/landslides/datastores/





curl -u admin:geoserver -XGET http://localhost:8080/geoserver/rest/layers.json

curl -v -u admin:geoserver -XPUT -H "Content-type: application/zip"
  --data-binary /Users/drotheram/GitHub/Volcanic-Interpretation-Workbench/app/Data/20220411_HH_20220423_HH.adf.wrp.geo.tif

curl -v -u admin:geoserver  http://localhost:8080/geoserver/rest/blobstores

## Docker copy image to filesystem
docker cp 20220411_HH_20220427_HH.adf.wrp.geo.tif geoserver:opt/geoserver/data_dir/workspaces/Volcano-InSAR/
docker cp 20220411_HH_20220423_HH.adf.wrp.geo.tif geoserver:opt/geoserver/data_dir/workspaces/Volcano-InSAR/

## Create Datastore with geotiff objects
curl -v -u admin:geoserver -XPOST -H 'Content-Type: application/xml' \
    -d '<coverageStore><name>20220411_HH_20220427_HH</name>
        <workspace>Volcano-InSAR</workspace>
        <type>GeoTIFF</type>
        <enabled>true</enabled></coverageStore>' \
         http://localhost:8080/geoserver/rest/workspaces/Volcano-InSAR/coveragestores

        # <url>file:workspaces/Volcano-InSAR/20220411_HH_20220427_HH.adf.wrp.geo.tif",

curl -v -u admin:geoserver -XPUT -H "Content-type: text/plain"  \
    -d "file:///opt/geoserver/data_dir/workspaces/Volcano-InSAR/20220411_HH_20220427_HH.adf.wrp.geo.tif"  \
        http://localhost:8080/geoserver/rest/workspaces/Volcano-InSAR/coveragestores/20220411_HH_20220427_HH/external.geotiff?configure=first\&coverageName=20220411_HH_20220427_HH.adf.wrp.geo



        ?configure=first\&coverageName=20220411_HH_20220427_HH




#######################
## Load Meeager Data ##
#######################

WORKSPACE=Meager_5M3A

curl -v -u admin:geoserver -XPOST -H "Content-type: text/xml" \
  -d "<workspace><name>${WORKSPACE}</name></workspace>" \
  http://localhost:8080/geoserver/rest/workspaces

curl -v -u admin:geoserver -XGET http://localhost:8080/geoserver/rest/workspaces | json_pp



for file in /Users/drotheram/Projects/Volcano_InSAR/Meager/5M3/insar/cropped/*wrp.geo.crop.tif
do
  echo $file
  fileSplit=(${file//// })
  filename=${fileSplit[8]}
  dates=${fileSplit[8]:0:23}

  docker cp $file geoserver:opt/geoserver/data_dir/workspaces/${WORKSPACE}/

  curl -v -u admin:geoserver -XPOST -H 'Content-Type: application/xml' \
      -d "<coverageStore><name>${dates}.adf.wrp.geo.crop</name>
          <workspace>${WORKSPACE}</workspace>
          <type>GeoTIFF</type>
          <enabled>true</enabled></coverageStore>" \
          http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores

  curl -v -u admin:geoserver -XPUT -H "Content-type: text/plain"  \
      -d "file:///opt/geoserver/data_dir/workspaces/${WORKSPACE}/${dates}.adf.wrp.geo.crop.tif"  \
          http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores/${dates}.adf.wrp.geo.crop/external.geotiff?configure=first\&coverageName=${dates}.adf.wrp.geo.crop
done
