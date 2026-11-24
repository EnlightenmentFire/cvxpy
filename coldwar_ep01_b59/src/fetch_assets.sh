#!/usr/bin/env bash
# Re-download public-domain map data (Natural Earth) and archive photos.
set -euo pipefail
cd "$(dirname "$0")/../assets"
mkdir -p data archive
for f in 50m/physical/ne_50m_coastline 50m/physical/ne_50m_land 10m/cultural/ne_10m_populated_places_simple; do
  n=$(basename "$f")
  curl -sL -o "data/$n.zip" "https://naciscdn.org/naturalearth/$f.zip"
  mkdir -p "data/$n" && python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "data/$n.zip" "data/$n"
  rm "data/$n.zip"
done
# B-59 photos (U.S. Navy, NARA RG 428, c. 28-29 Oct 1962) as published in NSA EBB 399
for i in 1 2 3; do curl -sL -o "archive/b59_asw$i.jpg" "https://nsarchive2.gwu.edu/NSAEBB/NSAEBB399/docs/asw$i.jpg"; done
echo "U-2 photo: Wikimedia Commons, 'MRBM Field Launch Site San Cristobal No. 1 14 October 1962 - NARA - 193926.tif'"
