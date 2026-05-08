# Backup sidecar — same MongoDB version as production, so mongodump's
# archive format matches the live DB exactly. No extra packages needed:
# the bash loop in entrypoint.sh schedules backups directly, no cron.
FROM mongo:8.0

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY backup.sh /usr/local/bin/backup.sh

RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/backup.sh

# Mount point for the host backup directory.
VOLUME ["/backups"]

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
