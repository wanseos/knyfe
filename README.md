# Project Knyfe

## Get Started
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

### Remove
Stop and remove containers, networks, and volumes. **This removes the knyfe's postgresql data too.**
```sh
./dev.sh remove
```
