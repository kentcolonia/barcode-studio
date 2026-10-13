# Barcode Studio (self-hosted)

Create, print, scan and save barcodes. Python (Flask) + SQLite, behind nginx.
Saved barcodes live on the server in `data/barcodes.db`, shared by every user.

## Quick test on your own machine
    python3 -m venv venv && . venv/bin/activate
    pip install -r requirements.txt
    python app.py            # http://127.0.0.1:8000  (camera works on localhost)

## Deploy on Ubuntu/Debian
1. Copy this folder to the server (scp / git / unzip).
2. `sudo bash install.sh`   (installs Python, nginx, systemd service; prints a generated login)
3. Edit `server_name` in `/etc/nginx/sites-available/barcode-studio`
   (a plain IP also works for testing), then:
       sudo nginx -t && sudo systemctl reload nginx
4. **HTTPS (required for camera scanning)** - browsers only allow camera on HTTPS:
       sudo apt install certbot python3-certbot-nginx
       sudo certbot --nginx -d barcode.example.com
   No domain? Camera won't work over plain http://IP. Use a hardware scanner or the
   image-upload option, or use a self-signed cert / internal domain with a trusted CA.

## Login
Set in `/etc/barcode-studio.env` (APP_USER / APP_PASSWORD). Leave APP_PASSWORD empty to disable login.
After changing: `sudo systemctl restart barcode-studio`

## Operations
    sudo systemctl status barcode-studio
    sudo journalctl -u barcode-studio -f
    # backup
    cp /opt/barcode-studio/data/barcodes.db ~/barcodes-backup.db
    # update the app: re-run install.sh from the new folder (data and login are kept)

## Printing
Uses the browser's print dialog (Ctrl+P). Choose your label printer there; set margins to "None"
and scale to 100% for sticker/label sizes.

## Files
    app.py               backend + REST API (/api/barcodes)
    static/index.html    the web app
    static/vendor/       JsBarcode + html5-qrcode (bundled, no CDN needed)
    deploy/              systemd + nginx configs

## Docker / Portainer
Files: `Dockerfile`, `docker-compose.yml`. Data lives in the `barcode_data` volume (SQLite at /data/barcodes.db).

**Option A - Git repository (easiest):** push this folder to a Git repo, then in Portainer:
Stacks > Add stack > Repository > set the repo URL and compose path `docker-compose.yml`.
Add environment variables `APP_PASSWORD` (required), `APP_USER`, `HOST_PORT` > Deploy.

**Option B - build the image first, then use the stack:**
1. Portainer > Images > Build a new image > Upload the zip contents as a .tar (or paste the Dockerfile
   into the Web editor only if you also have the files on the host) and name it `barcode-studio:latest`.
   Or over SSH:  `unzip barcode-studio.zip && cd barcode-studio && docker build -t barcode-studio:latest .`
2. Stacks > Add stack > Web editor > paste docker-compose.yml, remove the `build: .` line,
   add the environment variables, Deploy.

Open `http://SERVER-IP:8000` (HOST_PORT). Backup: copy the volume file
`docker run --rm -v barcode_data:/d -v $PWD:/b alpine cp /d/barcodes.db /b/`

**HTTPS (needed for camera scanning):** put the container behind your existing reverse proxy
(Nginx Proxy Manager, Traefik, Caddy) pointing to `barcode-studio:8000` on the same Docker network,
with a certificate for your domain. Over plain http://IP the camera is blocked by the browser;
image upload and USB scanners still work.
