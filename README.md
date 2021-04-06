# Data registry

[![][travis-master-img]][travis-master-url] [![][travis-develop-img]][travis-develop-url]

The SCRC data registry is a Django website and REST API which is used by the data-pipeline to store metadata about code runs and their inputs and outputs.

User documentation is available [here](docs/index.md).

Development and maintenance guides are availabe in the Wiki.

## Local registry

### Installation
To initialise a local registry, run the following command from your terminal:
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/ScottishCovidResponse/data-registry/local-registry/scripts/initialise_registry.sh)"
```
This will install the registry and all the related files will be stored in `~/.scrc`.

To run the server, run the `~/.scrc/scripts/run_server.sh` script, then navigate to http://localhost:8000 in your browser to check that the server is up and running.

To stop the server, run the `~/.scrc/scripts/stop_server.sh` script.

[travis-master-img]: https://img.shields.io/travis/com/ScottishCovidResponse/data-registry/master?label=build-master
[travis-master-url]: https://travis-ci.com/ScottishCovidResponse/data-registry?branch=master

[travis-develop-img]: https://img.shields.io/travis/com/ScottishCovidResponse/data-registry/develop?label=build-develop
[travis-develop-url]: https://travis-ci.com/ScottishCovidResponse/data-registry?branch=develop

### Logging in
Go to http://localhost:8000/admin in your browser. Login with username `admin` and password `admin`. You can now click on **View site** to return to http://localhost:8000/.

After logging in you can go to http://localhost:8000/get-token to obtain an API access token.
