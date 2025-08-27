FROM library/caddy

COPY --from=local/ai-tutor-app /app/.web/build/client /srv
ADD Caddyfile /etc/caddy/Caddyfile
