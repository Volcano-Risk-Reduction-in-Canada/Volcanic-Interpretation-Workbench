#!/bin/bash
# SPDX-License-Identifier: MIT
#
#
# Copyright (C) 2022 Government of Canada
#
# Main Author: Drew Rotheram-Clarke <drew.rotheram-clarke@canada.ca>

############################################################################################
## EntryPoint Script to Populate GeoServer With InSAR data stored in S3                   ##
############################################################################################


# WORKSPACELIST=(Meager_5M3A Meager_5M23 Garibaldi_3M23 Tseax_3M19 LavaFork_3M41)
WORKSPACELIST=(Meager_5M21)



for WORKSPACE in "${WORKSPACELIST[@]}"
do
  curl -v -u admin:geoserver -XPOST -H "Content-type: text/xml" \
    -d "<workspace><name>${WORKSPACE}</name></workspace>" \
    http://localhost:8080/geoserver/rest/workspaces

  # Split $WORKSPACE into the workspace array using "_" as delimiter
  IFS="_" read -r -a workspace <<< "$WORKSPACE"

  for file in /Users/drotheram/Projects/Volcano_InSAR/"${workspace[0]}/${workspace[1]}"/insar/*wrp.geo.tif
  do
    # echo "$file"
    filename=$(basename "$file")
    dates=${filename:0:23}

    docker cp "${file}" geoserver-cog:/opt/geoserver/data_dir/workspaces/"${WORKSPACE}"/

    # Load ADF filtered wrapped rasters
    curl -v -u admin:geoserver -XPOST -H 'Content-Type: application/xml' \
        -d "<coverageStore><name>${dates}.adf.wrp.geo</name>
            <workspace>${WORKSPACE}</workspace>
            <type>GeoTIFF</type>
            <enabled>true</enabled></coverageStore>" \
            "http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores"

    curl -v -u admin:geoserver -XPUT -H "Content-type: text/plain" \
        -d "file:///opt/geoserver/data_dir/workspaces/${WORKSPACE}/${dates}.adf.wrp.geo.tif" \
            "http://localhost:8080/geoserver/rest/workspaces/${WORKSPACE}/coveragestores/${dates}.adf.wrp.geo/external.geotiff?configure=first&coverageName=${dates}.adf.wrp.geo"
  done

done

python3 calcAvgCoh.py --ccDir=/Users/drotheram/Projects/Volcano_InSAR/"${workspace[0]}/${workspace[1]}"/insar
python3 genAvgCohMatrix.py --ccDir=/Users/drotheram/Projects/Volcano_InSAR/"${workspace[0]}/${workspace[1]}"/insar

cp /Users/drotheram/Projects/Volcano_InSAR/"${workspace[0]}"/"${workspace[1]}"/insar/*csv /Users/drotheram/GitHub/Volcanic-Interpretation-Workbench/app/Data/"${workspace[0]}"/"${workspace[1]}"/

tail -f /dev/null & wait
