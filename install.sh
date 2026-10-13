#!/usr/bin/env bash
# Run on the server as root:  sudo bash install.sh
set -euo pipefail
APP_DIR=/opt/barcode-studio
SRC="$(cd "$(dirname "$0")" && pwd)"

apt-get update
apt-get install -y python3 python3-venv nginx

mkdir -p "$APP_DIR/data"
cp -r "$SRC/app.py" "$SRC/requirements.txt" "$SRC/static" "$APP_DIR/"
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
chown -R www-data:www-data "$APP_DIR"

if [ ! -f /etc/barcode-studio.env ]; then
  PW=$(python3 -c 'import secrets;print(secrets.token_urlsafe(12))')
  cat > /etc/barcode-studio.env <<ENV
APP_USER=admin
APP_PASSWORD=$PW
BARCODE_DB=$APP_DIR/data/barcodes.db
ENV
  chmod 600 /etc/barcode-studio.env
  echo "Login created -> user: admin  password: $PW   (edit /etc/barcode-studio.env to change)"
fi

cp "$SRC/deploy/barcode-studio.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now barcode-studio

cp "$SRC/deploy/nginx.conf" /etc/nginx/sites-available/barcode-studio
ln -sf /etc/nginx/sites-available/barcode-studio /etc/nginx/sites-enabled/barcode-studio
echo "Edit server_name in /etc/nginx/sites-available/barcode-studio, then: nginx -t && systemctl reload nginx"
