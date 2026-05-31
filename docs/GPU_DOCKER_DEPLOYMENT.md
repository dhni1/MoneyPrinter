# GPU Docker 배포 가이드

이 문서는 GPU로 `faster-whisper` 자막 생성을 가속해 처리 속도를 높이는 방법을 설명합니다.

## GPU 가속이 필요한 이유

MoneyPrinterTurbo에서 딥러닝을 직접 사용하는 핵심 단계는 **faster-whisper 음성 인식**입니다. 이 단계는 오디오를 타임스탬프가 있는 자막으로 변환합니다.

- **CPU 모드**(기본값): `large-v3` 모델의 자막 생성 속도가 느릴 수 있습니다.
- **GPU 모드**: NVIDIA GPU와 CUDA를 사용해 보통 **5-10배** 빠르게 처리할 수 있습니다.

> 참고: 대본 생성, 음성 합성, 영상 편집 단계는 GPU 가속 대상이 아닙니다. GPU는 Whisper 기반 자막 생성에만 사용됩니다.

## 배포 방식

프로젝트는 두 가지 Docker 배포 방식을 제공합니다. **기본 CPU 배포는 그대로 사용할 수 있습니다.**

### CPU 배포(기본, 변경 없음)

```bash
docker compose up -d
```

기존 `Dockerfile`(`python:3.11-slim-bullseye`)을 사용하며 GPU가 필요하지 않습니다.

### GPU 배포(NVIDIA GPU 사용자)

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

`Dockerfile.gpu`(`nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04`)를 사용하고 API 서비스에 GPU를 마운트합니다.

## 사전 조건

### 1. 하드웨어

- NVIDIA GPU(6GB 이상 VRAM 권장)
- `large-v3` 모델은 GPU `float16` 기준 약 1.5GB VRAM을 사용합니다.

### 2. 소프트웨어

- **NVIDIA 드라이버**: 최신 버전을 권장하며 `nvidia-smi`로 확인합니다.
- **Docker Desktop**
- **NVIDIA Container Toolkit**: `docker info`의 Runtimes 목록에 `nvidia`가 있는지 확인합니다.

### 3. 환경 확인

```bash
# NVIDIA 드라이버 확인
nvidia-smi

# Docker GPU 지원 확인(Runtimes에 nvidia가 있어야 함)
docker info | grep -i runtime
```

`nvidia` runtime이 없다면 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)을 먼저 설치하세요.

## Whisper GPU 설정

`config.toml`에서 다음처럼 설정합니다.

```toml
[app]
subtitle_provider = "whisper"

[whisper]
model_size = "large-v3"
device = "cuda"           # GPU 사용, CPU 사용자는 "cpu"
compute_type = "float16"  # GPU 권장값, CPU 사용자는 "int8"
```

## 파일 설명

| 파일 | 용도 |
| --- | --- |
| `Dockerfile` | 기본 CPU 이미지 |
| `Dockerfile.gpu` | NVIDIA CUDA 기반 GPU 이미지 |
| `docker-compose.yml` | 기본 CPU 배포 설정 |
| `docker-compose.gpu.yml` | GPU 배포용 override 설정 |

## 배포 단계

### 1단계: CUDA 기반 이미지 가져오기

```bash
docker pull nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04
```

> 일부 미러 가속 환경은 `nvidia/cuda` 이미지에 403을 반환할 수 있습니다. Docker Hub에서 직접 받을 수 있는지 확인하세요.

### 2단계: `config.toml` 수정

위 설정처럼 `subtitle_provider = "whisper"`, `device = "cuda"`를 지정합니다.

### 3단계: 빌드 및 실행

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

### 4단계: GPU 적용 확인

```bash
docker compose exec api nvidia-smi
```

GPU 정보가 보이면 GPU 마운트가 정상입니다.

## VRAM과 동시 작업 권장값

| GPU VRAM | 권장 최대 동시 작업 수 |
| --- | --- |
| 4GB | 1 |
| 6GB | 1-2 |
| 8GB | 2 |
| 12GB 이상 | 3 이상 |

동시 작업 수는 `config.toml`의 `max_concurrent_tasks`로 조절할 수 있습니다.

## 문제 해결

### 문제 1: 이미지 pull 실패(403 Forbidden)

일부 이미지 미러가 `nvidia/cuda`에 403을 반환할 수 있습니다.

- 다른 미러를 설정합니다.
- 또는 `docker pull nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04`로 직접 받습니다.

### 문제 2: pip 설치 중 `Cannot uninstall blinker` 오류

Ubuntu 22.04 기본 `blinker`가 `distutils`로 설치되어 pip가 제거하지 못하는 경우입니다. `Dockerfile.gpu`는 `apt-get remove -y python3-blinker`로 이 문제를 처리합니다.

### 문제 3: 컨테이너에서 `nvidia-smi`가 GPU를 찾지 못함

- 호스트에 NVIDIA Container Toolkit이 설치되어 있는지 확인합니다.
- `docker info`의 Runtimes에 `nvidia`가 있는지 확인합니다.
- GPU 배포 명령을 사용했는지 확인합니다: `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d`

### 문제 4: Whisper CUDA 오류

- `config.toml`의 `device = "cuda"`를 확인합니다. 대소문자를 구분하며 `"CPU"`가 아닙니다.
- `compute_type = "float16"`인지 확인합니다.
- `subtitle_provider = "whisper"`인지 확인합니다.
