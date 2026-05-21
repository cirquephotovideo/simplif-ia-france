FROM nginx:1.27-alpine

RUN apk add --no-cache curl

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY public /usr/share/nginx/html

# Fix permissions · les fichiers source du Mac ont des perms 600, on les rend lisibles par nginx
RUN chmod -R a+rX /usr/share/nginx/html \
    && chown -R nginx:nginx /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/health || exit 1
