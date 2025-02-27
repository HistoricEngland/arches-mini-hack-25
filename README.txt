## Mini hack setup

Remove any existing aher_project folder in your workspace (or rename)

Clone this in to its palce: `git clone https://github.com/HistoricEngland/arches-mini-hack-25.git aher_project`

Ensure that you have arches (stable/7.5.5) and arches_her (stable/1.0.0) cloned into the workspace.

You will need to remove the `he/aher_project:dev_build` image from your docker instance if you already have one as it will need to be rebuilt. 

Use the docker compose files in `aher_project/docker/aher_project` to compose up the environment.