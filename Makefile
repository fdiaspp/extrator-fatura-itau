help:
	@echo 'Run "make <target>" where <target> is one of the following:'
	@echo '  dockerDev'

docker-build:
	docker compose --file docker-compose.yml up app --build -d --quiet-pull
docker:
	docker compose --file docker-compose.yml up app --build --quiet-pull

docker-test:
	docker compose --file docker-compose.yml up tests --build --quiet-pull

# dockerProd:
# 	git pull && sudo docker compose --file .docker/docker-compose.yml up pgadmin postgres nginx --build -d --quiet-pull

# dockerMigrate:
# 	sudo docker compose --file .docker/docker-compose.yml up migrate-deploy --build -d --quiet-pull
