# Systemd deployment

Run `tm-extractor` as a daily systemd timer. Three files, three commands.

## Prerequisites

- systemd-based Linux
- `uv` installed system-wide so `root` can invoke `uvx`:

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sudo sh
  ```

- `RAWDATA_API_AUTH_TOKEN` from the [Raw Data API](https://github.com/hotosm/raw-data-api/) admins

## Install

1. **Write the env file**

   ```bash
   sudo install -d -m 0750 /etc/tm-extractor
   sudo install -m 0640 .env.example /etc/tm-extractor/.env
   sudo ${EDITOR:-vi} /etc/tm-extractor/.env
   ```

1. **Install the unit files**

   ```bash
   sudo install -m 0644 tm-extractor.service tm-extractor.timer /etc/systemd/system/
   sudo systemctl daemon-reload
   ```

1. **Enable the daily timer**

   ```bash
   sudo systemctl enable --now tm-extractor.timer
   ```

Done. The job fires once a day and will catch up after reboots (`Persistent=true`).

## Verify

```bash
systemctl list-timers tm-extractor.timer   # next scheduled run
systemctl status tm-extractor.service      # last run status
sudo journalctl -u tm-extractor.service -f # tail live logs
```

Trigger a run on demand:

```bash
sudo systemctl start tm-extractor.service
```

## Customise

- **Change the schedule** — edit `OnCalendar=` in `tm-extractor.timer`. Examples: `OnCalendar=*-*-* 02:00:00` (daily at 02:00), `OnCalendar=hourly`, `OnCalendar=Mon *-*-* 06:00:00` (Mondays at 06:00).
- **Change the extraction window** — edit `ExecStart=` args in `tm-extractor.service` (`--fetch-active-projects N` or `--projects 123 456`).
- **Non-root user** — uncomment the `User=`, `Group=` and hardening lines in `tm-extractor.service`, create the user, and make sure `uv` is accessible on their `PATH`.

After any unit change: `sudo systemctl daemon-reload` and (for timer changes) `sudo systemctl restart tm-extractor.timer`.

## Uninstall

```bash
sudo systemctl disable --now tm-extractor.timer
sudo rm /etc/systemd/system/tm-extractor.service /etc/systemd/system/tm-extractor.timer
sudo rm -rf /etc/tm-extractor
sudo systemctl daemon-reload
```
