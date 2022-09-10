FROM php:8.1-apache

COPY mysql_credentials /var/opt/mysql_credentials
COPY python /var/www/python
COPY website /var/www/html

ENV DIR_COLLECT=/var/www/html
ENV MYSQL_CRED=/var/opt/mysql_credentials

RUN docker-php-ext-install mysqli pdo pdo_mysql

EXPOSE 80