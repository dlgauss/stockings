#!/bin/sh
# Installs this app's nginx site from the deploy folder, checks it with nginx -t and reloads nginx.
# The deploy runs it as root through sudo, so it takes no arguments and every path is fixed.
#
# One-time setup on the server (after the first deploy has copied this file):
#   sudo install -m 755 -o root -g root ~/stocks-landingpage/deploy/nginx/install-site.sh /usr/local/sbin/stockings-nginx
#   echo 'dlopatenco ALL=(root) NOPASSWD: /usr/local/sbin/stockings-nginx' | sudo tee /etc/sudoers.d/stockings-nginx
#   sudo chmod 440 /etc/sudoers.d/stockings-nginx && sudo visudo -c
set -eu

SRC=/home/dlopatenco/stocks-landingpage/deploy/nginx/stockings.talkboard.chat.conf
DEST=/etc/nginx/conf.d/stockings.talkboard.chat.conf

if [ -f "$DEST" ] && cmp -s "$SRC" "$DEST"; then
    echo "nginx: config unchanged"
    exit 0
fi

# Keep the current config so a broken one never stays on disk (one nginx serves every site).
BACKUP=""
if [ -f "$DEST" ]; then
    BACKUP=$(mktemp)
    cp "$DEST" "$BACKUP"
fi

install -m 644 -o root -g root "$SRC" "$DEST"

if ! nginx -t; then
    if [ -n "$BACKUP" ]; then
        cp "$BACKUP" "$DEST"
    else
        rm -f "$DEST"
    fi
    echo "nginx: new config failed nginx -t, the previous one is kept" >&2
    exit 1
fi

[ -n "$BACKUP" ] && rm -f "$BACKUP"
systemctl reload nginx
echo "nginx: config installed and reloaded"
