FROM nginx:1.27-alpine

COPY frontend/index.html /usr/share/nginx/html/index.html
COPY frontend/styles.css /usr/share/nginx/html/styles.css
COPY frontend/script.js /usr/share/nginx/html/script.js
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY other/svoy_dom_logo.png /usr/share/nginx/html/svoy_dom_logo.png
