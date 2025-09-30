FROM library/caddy

COPY --from=app_image /app/.web/build/client /srv
ADD Caddyfile /etc/caddy/Caddyfile
