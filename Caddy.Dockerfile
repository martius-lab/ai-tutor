FROM library/caddy

COPY --from=local/ai-tutor-app /app/.web/_static /srv
ADD Caddyfile /etc/caddy/Caddyfile
