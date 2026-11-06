#!/usr/bin/env bash
# Installs the NAS -> website publisher on a Raspberry Pi.
# Run on the Pi with:
#   bash <(curl -fsSL https://raw.githubusercontent.com/Nduwimanaclaude/NduwimanaClaude-site/main/tools/install.sh)
set -euo pipefail

REPO_SLUG="Nduwimanaclaude/NduwimanaClaude-site"
REPO_DIR="$HOME/nduwimanaclaude-site"
MOUNT="/mnt/nas-website"
KEY="$HOME/.ssh/nduwimanaclaude_deploy"
bold(){ printf '\n\033[1m%s\033[0m\n' "$*"; }

bold "1/6  Installing packages (git, Pillow, NFS client)"
sudo apt-get update -qq
sudo apt-get install -y -qq git python3-pil nfs-common >/dev/null
echo "done"

bold "2/6  Connecting to the NAS Website folder"
read -rp "NAS address [100.64.254.116]: " NAS_IP; NAS_IP=${NAS_IP:-100.64.254.116}
read -rp "NFS path of the Website share [/volume1/Website]: " NAS_PATH; NAS_PATH=${NAS_PATH:-/volume1/Website}
sudo mkdir -p "$MOUNT"
LINE="$NAS_IP:$NAS_PATH $MOUNT nfs ro,soft,timeo=50,nofail,_netdev,x-systemd.automount,x-systemd.idle-timeout=600 0 0"
sudo sed -i "\# $MOUNT #d" /etc/fstab
echo "$LINE" | sudo tee -a /etc/fstab >/dev/null
sudo systemctl daemon-reload
sudo systemctl restart "$(systemd-escape -p --suffix=automount "$MOUNT")" 2>/dev/null || true
if ls "$MOUNT" >/dev/null 2>&1 && [ -n "$(ls -A "$MOUNT" 2>/dev/null)" ]; then
  echo "Mounted. Folders found: $(ls "$MOUNT" | tr '\n' ' ')"
else
  echo "Couldn't see the Website folder yet. Check the NFS permission on the NAS, then re-run this script."
  exit 1
fi

bold "3/6  Creating a GitHub key that can only write to the site repo"
mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
[ -f "$KEY" ] || ssh-keygen -t ed25519 -N "" -C "claude14-site-publisher" -f "$KEY" >/dev/null
if ! grep -q "Host github-site" "$HOME/.ssh/config" 2>/dev/null; then
  cat >> "$HOME/.ssh/config" <<EOF

Host github-site
  HostName github.com
  User git
  IdentityFile $KEY
  IdentitiesOnly yes
EOF
  chmod 600 "$HOME/.ssh/config"
fi
ssh-keyscan -q github.com >> "$HOME/.ssh/known_hosts" 2>/dev/null || true
echo
echo "Copy this whole line (it's the PUBLIC half of the key, safe to share):"
echo
cat "$KEY.pub"
echo
echo "Then on GitHub: repo Settings > Deploy keys > Add deploy key"
echo "  Title: claude14   Key: (paste)   [x] Allow write access   > Add key"
read -rp "Press Enter once it's added... " _
until ssh -T github-site 2>&1 | grep -q "successfully authenticated"; do
  read -rp "GitHub didn't accept the key yet. Add it (with write access), then press Enter... " _
done
echo "Key works."

bold "4/6  Downloading the site repo"
if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" remote set-url origin "git@github-site:$REPO_SLUG.git"
  git -C "$REPO_DIR" fetch -q origin && git -C "$REPO_DIR" reset -q --hard origin/main
else
  git clone -q "git@github-site:$REPO_SLUG.git" "$REPO_DIR"
fi
git -C "$REPO_DIR" config user.name "claude14 (NAS publisher)"
git -C "$REPO_DIR" config user.email "nclaude@nduwimanaclaude.com"
cat > "$REPO_DIR/tools/config.env" <<EOF
WEBSITE_DIR=$MOUNT
REPO_DIR=$REPO_DIR
SITE_URL=https://nduwimanaclaude.com
MAX_EDGE=2400
JPEG_QUALITY=86
SMALL_EDGE=1200
GIT_PUSH=1
EOF
echo "done"

bold "5/6  Scheduling it to check every 3 minutes"
sudo tee /etc/systemd/system/site-publisher.service >/dev/null <<EOF
[Unit]
Description=Publish NAS Website folder to nduwimanaclaude.com
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$USER
ExecStart=/usr/bin/python3 $REPO_DIR/tools/publish.py
Nice=10
EOF
sudo tee /etc/systemd/system/site-publisher.timer >/dev/null <<EOF
[Unit]
Description=Check the NAS Website folder every 3 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=3min
Persistent=true

[Install]
WantedBy=timers.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now site-publisher.timer >/dev/null
echo "done"

bold "6/6  First publish (this one takes a minute)"
python3 "$REPO_DIR/tools/publish.py" --force

bold "All set."
echo "Drop edited photos into the Website folders on the NAS; the site updates within ~5 minutes."
echo "See what it's doing anytime:  journalctl -u site-publisher -n 30"
