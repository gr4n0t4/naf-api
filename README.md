# naf-api
NAF api created from daily dumps of the database
# How to use
## From scratch
To stand up everything at once you can use the following command
`docker-compose up`
## Stand up the database
To stand up the database by itself
`docker-compose up postgres`
## Fetch the data & insert it in the database
You need to do this to get the new data from the dump (once a day)
`docker-compose up fetcher`
## Stand up the api
To stand up the api you can use this command
`docker-compose up api`
# Browse the api
By default the api will be available in http://localhost:3000/api and swagger with all documentation in http://localhost:3000/api/docs

