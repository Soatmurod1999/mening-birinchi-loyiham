# 1. Asos qilib Nginx veb-serverini olamiz
FROM nginx:alpine

# 2. O'zimiz yaratgan index.html faylini Docker ichidagi Nginx papkasiga nusxalaymiz
COPY index.html /usr/share/nginx/html/index.html

# 3. Server 80-portda tashqi dunyoga ochiladi
EXPOSE 80
