Run PsiZ inside docker
===

This example uses images as stimuli.

## Download

`git clone https://github.com/psiz-org/psiz-collect`

## Option 1: With docker-compose

`docker-compose up`

## Option 2: Create containers manually

### Create docker network

`docker network create psiz`

### Create app container

#### Create `mysql_credentials` file on server in `psiz-collect/` directory

(Change `password` & `username` to your needs)

`vim mysql_credentials`

```
[psiz]
servername = psiz-db
username = psiz
password = psiz
database = psiz
```


#### Create container

(make sure to be in the `psiz-collect/` directory)

```
docker run -dit --name psiz-app -h psiz-app --net psiz -v "${PWD}"/website:/var/www/html -v "${PWD}"/python:/var/www/python -v "${PWD}"/mysql_credentials:/var/opt/mysql_credentials -p 9090:80 -e DIR_COLLECT=/var/www/html -e MYSQL_CRED=/var/opt/mysql_credentials php:8.1-apache
```

#### Install mysql in psiz-app container

`docker exec -it psiz-app docker-php-ext-install mysqli pdo pdo_mysql`

`docker exec -it psiz-app service apache2 reload`

#### Create project

1) Create folder (e.g. `rocks`) inside `psiz-collect/website/projects/` folder
2) Copy image files (`.png` or `.jpg`) into this folder
3) Create `stimuli.txt` file
  
  (make sure you are inside the `psiz-collect/website/` folder)

`find projects/rocks/ -type f -iname "*.jpg" -o -iname "*.png" | sort > ./projects/rocks/stimuli.txt`
4) Create protocol (JSON-File, e.g. `protocol_0.json`) inside the project folder (e.g. `rocks`)

Example:

```
{
   "docket": [
       {
           "content": "blockSpec",
           "nTrial": 30,
           "nCatch": 1,
           "nReference": 8,
           "nSelect": 2,
           "isRanked": true
       }
   ]
}
```
### Create database container

#### Create container
(make sure to be in the `psiz-collect/` directory and that `MYSQL_USER`, `MYSQL_PASSWORD` & `MYSQL_DATABASE` match above created `mysql_credentials` file)
)

```
docker run -dit --name psiz-db -h psiz-db --net psiz -e MYSQL_ROOT_PASSWORD=psiz -e MYSQL_USER=psiz -e MYSQL_PASSWORD=psiz -e MYSQL_DATABASE=psiz -v "${PWD}/sql":/opt -p 3306:3306 mysql
```

#### Create database inside container

`docker exec -it psiz-db bash`

`mysql -u psiz -p`

`mysql> SOURCE /opt/install_db_psiz.sql;`

### Access the app

(Change `projectId` host and port according to your needs)

Open url: `http://localhost:9090/index.php?projectId=rocks`
