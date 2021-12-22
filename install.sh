#!/bin/bash

set -e

DEST_BIN="/usr/local/bin"
DEST_SYSTEMD="/etc/systemd/system"

SOURCE_DIR=`dirname $0`

# install executable scripts
install $SOURCE_DIR/photo.py $DEST_BIN
install $SOURCE_DIR/photo-upload.sh $DEST_BIN

# install systemd service
install $SOURCE_DIR/photos.timer $DEST_SYSTEMD
install $SOURCE_DIR/photos.service $DEST_SYSTEMD

# add a system user
id -u photo &>/dev/null || useradd -r photo

# bootstrap the service
systemctl daemon-reload

systemctl status photos

systemctl start photos

systemctl status photos

systemctl enable photos

systemctl status photos

