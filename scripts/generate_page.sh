#!/bin/bash

mkdir -p ../page/
mkdir -p ../page/Ferien
mkdir -p ../page/Feiertage

cp -r ../Ferien/* ../page/Ferien/
cp -r ../Feiertage/* ../page/Feiertage/
cp ../CNAME ../page/
cp ../robots.txt ../page/
cp ../sitemap.txt ../page

python3 fill_placeholder.py "[[feiertage-tree]]" ../page/Feiertage/ "Feiertage/" ../index_template.md ../page/index.md
python3 fill_placeholder.py "[[ferien-tree]]" ../page/Ferien/ "Ferien/" ../page/index.md ../page/index.md