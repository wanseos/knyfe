# Project Knyfe
Seamless and error-free booking management.

## Getting Started
### Prerequisites
1. Install Docker.
2. Grant permissions to execute `dev.sh` file.
```sh
chmod u+r+x ./dev.sh
```

### Build
Build containers and start the server.
```sh
./dev.sh build
```

### Test
Run tests using Django test runner.
```sh
./dev.sh test
```

### Remove
Stop and remove containers, networks, and volumes. **This removes the knyfe's postgresql data too.** Use this command to completely remove the service resources.
```sh
./dev.sh remove
```


## Generating Schema
Build services using `./dev.sh build` and discover schema in local environment.
* [Swagger-UI](http://localhost:8000/schema/redoc)
* [ReDoc](http://localhost:8000/schema/swagger-ui)
