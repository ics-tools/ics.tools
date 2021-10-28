#!/bin/bash
ROOT="$1"
HTTP="$2"
OUTPUT="$3"

i=0
echo "# Index:" > $OUTPUT
for i in `find "$ROOT" -maxdepth 1 -mindepth 1 -type d| sort`; do
    dir=`basename "$i"`
    echo "- [$dir/](${HTTP}${dir})" >> $OUTPUT
done
for i in `find "$ROOT" -maxdepth 1 -mindepth 1 -type f| sort`; do
    file=`basename "$i"`
    echo "- [$file](${HTTP}${file})" >> $OUTPUT
done
