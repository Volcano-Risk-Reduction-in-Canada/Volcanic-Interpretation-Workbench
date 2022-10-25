# Script to copy 

# DOWNLOADDIR=/Users/drotheram/GitHub/Volcanic-Interpretation-Workbench/app/Data/LavaFork/3M41/
DOWNLOADDIR=/Users/drotheram/Projects/Volcano_InSAR/Meager/5M3/insar/
DOWNLOADDIR=/Users/drotheram/Projects/Volcano_InSAR/Meager/5M21/insar/

mkdir -p $DOWNLOADDIR
cd $DOWNLOADDIR

cart=https://data.eodms-sgdot.nrcan-rncan.gc.ca/rcm/carts/ce1aacd4-4abb-409e-b74d-7d1035cce0a8/1483640/d2b5108e-2df6-4ce6-b6c0-007d500d53b8
cart=https://data.eodms-sgdot.nrcan-rncan.gc.ca/rcm/carts/7a32c4fa-fed1-43a4-b4fb-827c09011456/1515469/a72e9678-d925-4b8f-a9b2-0a210f550cfd/a72e9678-d925-4b8f-a9b2-0a210f550cfd

/usr/local/bin/wget --user $EODMSUSERNAME --password $EODMSPASSWORD $cart --recursive --no-parent

cd /Users/drotheram/Projects/Volcano_InSAR/Tseax/3M19/insar/data.eodms-sgdot.nrcan-rncan.gc.ca/rcm/carts/6b78d25e-f1e0-4bc3-b80a-095d25c28fbe/1479035/2a33641c-d8d8-4007-9548-f66e0d12c99e/2a33641c-d8d8-4007-9548-f66e0d12c99e/insar

for file in 2*HH*HH
do 
echo $file
mv $file/$file.adf.wrp.geo.tif $DOWNLOADDIR
mv $file/$file.cc.geo.tif $DOWNLOADDIR
done

for file in 2*HH*HH/geo/*.tif
do 
echo "Processing: "${file:28:24}
gdal_calc.py --calc='10*log10(A)' \
            --outfile=/Users/drotheram/Projects/Volcano_InSAR/Meager/5M21/rmli/${file:28:20}.db.tif \
            --overwrite \
            -A $file
done





