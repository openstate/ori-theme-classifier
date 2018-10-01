# Open Raadsinformatie Theme Classifier
Classifier that can be trained to a model to classify Open Raadsinformatie documents into 9 themes (hoofdfuncties from Iv3).


## Requirements
[Docker Compose](https://docs.docker.com/compose/install/)

## Run
- Clone or download this project from GitHub:
- Copy `docker/docker-compose.yml.example` to `docker/docker-compose.yml` and edit it
   - Fill in a password at `<DB_PASSWORD>`
- Copy `config.py.example` to `config.py` and edit it
   - Create a SECRET_KEY as per the instructions in the file
   - Fill in the same `<DB_PASSWORD>` as used in `docker/docker-compose.yml`
   - Specify email related information in order for the application to send emails
- Production
   - Make sure to extract the latest MySQL backup in `docker/docker-entrypoint-initdb.d` if you want to import it: `gunzip latest-mysqldump-daily.sql.gz`
   - `cd docker`
   - `sudo docker-compose up -d`
   - Set up backups
      - Copy `docker/backup.sh.example` to `docker/backup.sh` and edit it
         - Fill in the same `<DB_PASSWORD>` as used in `docker/docker-compose.yml`
      - To run manually use `sudo ./backup.sh`
      - To set a daily cronjob at 03:46
         - `sudo crontab -e` and add the following line (change the path below to your `multilateral-organisations/docker` directory path)
         - `46 3 * * * (cd <PATH_TO_multilateral-organisations/docker> && sudo ./backup.sh)`
      - The resulting SQL backup files are saved in `docker/docker-entrypoint-initdb.d`
- Development; Flask debug will be turned on which automatically reloads any changes made to Flask files so you don't have to restart the whole application manually
   - Make sure to extract the latest MySQL backup in `docker/docker-entrypoint-initdb.d` if you want to import it: `gunzip latest-mysqldump-daily.sql.gz`
   - `cd docker`
   - `docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d`
   - Retrieve the IP address of the nginx container `docker inspect otc_nginx_1` and add it to your hosts file `/etc/hosts`: `<IP_address> open-multilaterals.org`
- Useful commands
   - Remove and rebuild everything (this also removes the MySQL volume containing all records (this is required if you want to load the .sql files from `docker/docker-entrypoint-initdb.d` again))
      - Production: `docker-compose down --rmi all && docker volume rm otc_otc-mysql-volume && docker-compose up -d`
      - Development: `docker-compose -f docker-compose.yml -f docker-compose-dev.yml down --rmi all && docker volume rm otc_otc-mysql-volume && docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d`
   - Reload Nginx: `sudo docker exec otc_nginx_1 nginx -s reload`
   - Reload uWSGI (only for production as development environment doesn't use uWSGI and automatically reloads changes): `sudo touch uwsgi-touch-reload`

## CLI
To access the CLI of the app run `sudo docker exec -it otc_app_1 bash` and run `flask`.

## To enter the MySQL database
   - `sudo docker exec -it otc_mysql_1 bash`
   - `mysql -p`
   - Retrieve database password from `docker/docker-compose.yml` and enter it in the prompt
