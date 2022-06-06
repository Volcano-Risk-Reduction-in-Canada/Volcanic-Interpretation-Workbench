# Script to copy 

DOWNLOADDIR=/Users/drotheram/Projects/Volcano_InSAR/Tseax/3M19/insar
FINDIR=/Users/drotheram/Projects/Volcano_InSAR/Tseax/3M19/

mkdir -p $DOWNLOADDIR
cd $DOWNLOADDIR

cart=https://data.eodms-sgdot.nrcan-rncan.gc.ca/rcm/carts/6b78d25e-f1e0-4bc3-b80a-095d25c28fbe/1479035/2a33641c-d8d8-4007-9548-f66e0d12c99e

/usr/local/bin/wget --user $EODMSUSERNAME --password $EODMSPASSWORD $cart --recursive --no-parent

cd /Users/drotheram/Projects/Volcano_InSAR/Tseax/3M19/insar/data.eodms-sgdot.nrcan-rncan.gc.ca/rcm/carts/6b78d25e-f1e0-4bc3-b80a-095d25c28fbe/1479035/2a33641c-d8d8-4007-9548-f66e0d12c99e/2a33641c-d8d8-4007-9548-f66e0d12c99e/insar

for file in 2*HH*HH
do 
echo $file
cp $file/$file.adf.wrp.geo.tif $DOWNLOADDIR
cp $file/$file.cc.geo.tif $DOWNLOADDIR

done






