#!/bin/bash

docker run -d -p 8080:8080 --name geoserver-cog -e COMMUNITY_EXTENSIONS=cog-plugin kartoza/geoserver:2.19.0

docker run -d -p 8080:8080 --name geoserver-s3 kartoza/geoserver:2.19.0



curl -v -u admin:geoserver -XPOST -H "Content-type: text/xml" \
  -d "<workspace><name>lan  dslides</name></workspace>" \
  http://localhost:8080/geoserver/rest/workspaces | json_pp

curl -v -u admin:geoserver -XGET http://localhost:8080/geoserver/rest/workspaces | json_pp


curl -v -u admin:geoserver -XPUT -H "Content-type: application/zip" \
  --data-binary @roads.zip \
  http://localhost:8080/geoserver/rest/workspaces/landslides/datastores/





curl -u admin:geoserver -XGET http://localhost:8080/geoserver/rest/layers.json

curl -v -u admin:geoserver -XPUT -H "Content-type: application/zip" \
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
        "http://localhost:8080/geoserver/rest/workspaces/Volcano-InSAR/coveragestores/20220411_HH_20220427_HH/external.geotiff?configure=first&coverageName=20220411_HH_20220427_HH.adf.wrp.geo"



        # ?configure=first&coverageName=20220411_HH_20220427_HH




#######################
## Load Meeager Data ##
#######################

WORKSPACE=Meager_5M3
INPUTDIR=/Users/drotheram/Projects/Volcano_InSAR/Meager/5M3/insar/

python3 calcAvgCoh.py --ccDir=$INPUTDIR
python3 genAvgCohMatrix.py --ccDir=$INPUTDIR

curl -v -u admin:geoserver -XPOST -H "Content-type: text/xml" \
  -d "<workspace><name>${WORKSPACE}</name></workspace>" \
  http://localhost:8080/geoserver/rest/workspaces

curl -v -u admin:geoserver -XGET http://localhost:8080/geoserver/rest/workspaces | json_pp


# Load interferograms
for file in "$INPUTDIR"/*wrp.geo.tif
do
  echo "$file"
  filename=$(basename "$file")
  dates=${filename:0:23}

  docker cp "$file" geoserver-cog:opt/geoserver/data_dir/workspaces/${WORKSPACE}/

  curl -v -u admin:geoserver -XPOST -H 'Content-Type: application/xml' \
      -d "<coverageStore><name>${dates}.adf.wrp.geo</name>
          <workspace>${WORKSPACE}</workspace>
          <type>GeoTIFF</type>
          <enabled>true</enabled></coverageStore>" \
          http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores

  curl -v -u admin:geoserver -XPUT -H "Content-type: text/plain"  \
      -d "file:///opt/geoserver/data_dir/workspaces/${WORKSPACE}/${dates}.adf.wrp.geo.tif"  \
          "http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores/${dates}.adf.wrp.geo/external.geotiff?configure=first&coverageName=${dates}.adf.wrp.geo"
done

# Load Backscatter imagery
for file in /Users/drotheram/Projects/Volcano_InSAR/Meager/5M3/rmli/*tif
do
  echo "$file"
  filename=$(basename "$file")
  date=${filename:0:8}

  docker cp "$file" geoserver-cog:opt/geoserver/data_dir/workspaces/${WORKSPACE}/

  curl -v -u admin:geoserver -XPOST -H 'Content-Type: application/xml' \
      -d "<coverageStore><name>${date}_HH.rmli.geo.db.tif</name>
          <workspace>${WORKSPACE}</workspace>
          <type>GeoTIFF</type>
          <enabled>true</enabled></coverageStore>" \
          http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores

  curl -v -u admin:geoserver -XPUT -H "Content-type: text/plain"  \
      -d "file:///opt/geoserver/data_dir/workspaces/${WORKSPACE}/${date}_HH.rmli.geo.db.tif"  \
          "http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores/${date}_HH.rmli.geo.db/external.geotiff?configure=first&coverageName=${date}_HH.rmli.geo.db"
done



###################################################
## Load North Slide Deformation Time series Data ##
###################################################

WORKSPACE=NorthSlide_3M14D

curl -v -u admin:geoserver -XPOST -H "Content-type: text/xml" \
  -d "<workspace><name>${WORKSPACE}</name></workspace>" \
  http://localhost:8080/geoserver/rest/workspaces

curl -v -u admin:geoserver -XGET http://localhost:8080/geoserver/rest/workspaces | json_pp

for file in ~/Projects/RGHRP/Thompson_River_Valley/NorthSlide/InSAR/insar/MSBAS_output/Run19_20220425_fixedunwrap/MSBAS_2*LOS.tif
do
  echo "$file"
  filename=$(basename "$file")
  dates=${filename:6:8}
  echo "$filename"
  echo "$dates"

  docker cp "$file" geoserver-cog:opt/geoserver/data_dir/workspaces/${WORKSPACE}/

  # curl -v -u admin:geoserver -XPOST -H 'Content-Type: application/xml' \
  #     -d "<coverageStore><name>MSBAS_${dates}_LOS</name>
  #         <workspace>${WORKSPACE}</workspace>
  #         <type>GeoTIFF</type>
  #         <enabled>true</enabled></coverageStore>" \
  #         http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores

  curl -v -u admin:geoserver -XPUT -H "Content-type: text/plain"  \
      -d "file:///opt/geoserver/data_dir/workspaces/${WORKSPACE}/${filename}"  \
          "http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores/MSBAS_${dates}_LOS/external.geotiff?configure=first&coverageName=MSBAS_${dates}_LOS"
done



#########################
## Load Garibaldi Data ##
#########################

WORKSPACE=Garibaldi_3M23
INPUTDIR=/Users/drotheram/Projects/Volcano_InSAR/Garibaldi/3M23/

curl -v -u admin:geoserver -XPOST -H "Content-type: text/xml" \
  -d "<workspace><name>${WORKSPACE}</name></workspace>" \
  http://localhost:8080/geoserver/rest/workspaces

curl -v -u admin:geoserver -XGET http://localhost:8080/geoserver/rest/workspaces | json_pp



for file in "${INPUTDIR}"/*wrp.geo.tif
do
  echo "$file"
  filename=$(basename "$file")
  dates=${filename:0:23}

  docker cp "$file" geoserver-cog:opt/geoserver/data_dir/workspaces/${WORKSPACE}/

  curl -v -u admin:geoserver -XPOST -H 'Content-Type: application/xml' \
      -d "<coverageStore><name>${dates}.adf.wrp.geo</name>
          <workspace>${WORKSPACE}</workspace>
          <type>GeoTIFF</type>
          <enabled>true</enabled></coverageStore>" \
          http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores

  curl -v -u admin:geoserver -XPUT -H "Content-type: text/plain"  \
      -d "file:///opt/geoserver/data_dir/workspaces/${WORKSPACE}/${dates}.adf.wrp.geo.tif"  \
          "http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores/${dates}.adf.wrp.geo/external.geotiff?configure=first&coverageName=${dates}.adf.wrp.geo"
done


#########################
## Load Tseax     Data ##
#########################

python3 calcAvgCoh.py --ccDir=/Users/drotheram/Projects/Volcano_InSAR/Tseax/3M19
python3 genAvgCohMatrix.py --ccDir=/Users/drotheram/Projects/Volcano_InSAR/Tseax/3M19


WORKSPACE=Tseax_3M19
INPUTDIR=/Users/drotheram/Projects/Volcano_InSAR/Tseax/3M19/

curl -v -u admin:geoserver -XPOST -H "Content-type: text/xml" \
  -d "<workspace><name>${WORKSPACE}</name></workspace>" \
  http://localhost:8080/geoserver/rest/workspaces

curl -v -u admin:geoserver -XGET http://localhost:8080/geoserver/rest/workspaces | json_pp



for file in "${INPUTDIR}"/*wrp.geo.tif
do
  echo "$file"
  filename=$(basename "$file")
  dates=${filename:0:23}

  docker cp "$file" geoserver-cog:opt/geoserver/data_dir/workspaces/${WORKSPACE}/

  curl -v -u admin:geoserver -XPOST -H 'Content-Type: application/xml' \
      -d "<coverageStore><name>${dates}.adf.wrp.geo</name>
          <workspace>${WORKSPACE}</workspace>
          <type>GeoTIFF</type>
          <enabled>true</enabled></coverageStore>" \
          http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores

  curl -v -u admin:geoserver -XPUT -H "Content-type: text/plain"  \
      -d "file:///opt/geoserver/data_dir/workspaces/${WORKSPACE}/${dates}.adf.wrp.geo.tif"  \
          "http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores/${dates}.adf.wrp.geo/external.geotiff?configure=first&coverageName=${dates}.adf.wrp.geo"
done


#########################
## Load LavaFork  Data ##
#########################

python3 calcAvgCoh.py --ccDir=/Users/drotheram/Projects/Volcano_InSAR/LavaFork/3M41
python3 genAvgCohMatrix.py --ccDir=/Users/drotheram/Projects/Volcano_InSAR/LavaFork/3M41


WORKSPACE=LavaFork_3M41
INPUTDIR=/Users/drotheram/Projects/Volcano_InSAR/LavaFork/3M41

curl -v -u admin:geoserver -XPOST -H "Content-type: text/xml" \
  -d "<workspace><name>${WORKSPACE}</name></workspace>" \
  http://localhost:8080/geoserver/rest/workspaces

curl -v -u admin:geoserver -XGET http://localhost:8080/geoserver/rest/workspaces | json_pp


for file in "${INPUTDIR}"/*wrp.geo.tif
do
  echo "$file"
  filename=$(basename "$file")
  dates=${filename:0:23}

  docker cp "$file" geoserver-cog:opt/geoserver/data_dir/workspaces/${WORKSPACE}/

  curl -v -u admin:geoserver -XPOST -H 'Content-Type: application/xml' \
      -d "<coverageStore><name>${dates}.adf.wrp.geo</name>
          <workspace>${WORKSPACE}</workspace>
          <type>GeoTIFF</type>
          <enabled>true</enabled></coverageStore>" \
          http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores

  curl -v -u admin:geoserver -XPUT -H "Content-type: text/plain"  \
      -d "file:///opt/geoserver/data_dir/workspaces/${WORKSPACE}/${dates}.adf.wrp.geo.tif"  \
          "http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores/${dates}.adf.wrp.geo/external.geotiff?configure=first&coverageName=${dates}.adf.wrp.geo"
done
