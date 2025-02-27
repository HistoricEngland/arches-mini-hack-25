## Mini hack setup

Remove any existing aher_project folder in your workspace (or rename)

Clone this in to its palce: git clone https://github.com/HistoricEngland/arches-mini-hack-25.git aher_project

## DB docker image

So that you can use pg_vector, you will need to build the included pg docker image and update the image reference in the `arches_her/docker/docker-compose-dependencies.yml`.

You need to use the Dockerfile at the path `aher_project/docker_db/Dockerfile`.

In VSCode you can right click and "Build Image" and provide the tag `minihack25_pgsql:pg14_pgv080` when prompted.

alternativey, with a command line prompt at the root of your workspace, run the following:

```sh
docker build --pull --rm -f 'aher_project/docker_db/Dockerfile' -t 'minihack25_pgsql:pg14_pgv080' 'aher_project/docker_db'
```

Now replace the following in your `arches_her/docker/docker-compose-dependencies.yml` file:

```yml
...
db-aherproject:
      container_name: db-aherproject
      #image: postgis/postgis:14-3.2 <<<<< replace with the line below
      image: minihack25_pgsql:pg14_pgv080
      volumes:
        - postgres-data:/var/lib/postgresql/data
        - postgres-log:/var/log/postgresql
        - ./docker/init-unix.sql:/docker-entrypoint-initdb.d/init.sql # to set up the DB template
      ports:
        - '5433:5432'
      env_file: 
        - ./docker/env_file.env
      networks:
        - aherproject-network
...

```