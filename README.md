# Project Knyfe
칼 같은 예약 관리 시스템

## 시작하기
### 필요한 준비
1. Docker가 설치되어 있어야 합니다.
2. `dev.sh` 파일에 권한을 부여해야합니다.
```sh
chmod u+r+x ./dev.sh
```

### Build
컨테이너를 빌드하고 서버를 시작합니다. 첫 번째 빌드인 경우에, 기본값으로 env 파일을 생성합니다.
```sh
./dev.sh build
```

### Test
Django 테스트러너를 사용하여 테스트를 실행합니다.
```sh
./dev.sh test
```

### Remove
컨테이너를 멈추고, 컨테이너, 네트워크, 볼륨을 제거합니다. **이 커맨드는 Knyfe의 데이터베이스 테이터도 지웁니다.** 서비스의 모든 자원을 제거할 때 사용하십시오.
```sh
./dev.sh remove
```


## 스키마 생성하기
커맨드 `./dev.sh build`를 활용하여 빌드하고, 로컬 환경해서 스키마와 API문서를 확인해보십시오.
* [Swagger-UI](http://localhost:8000/schema/redoc)
* [ReDoc](http://localhost:8000/schema/swagger-ui)
