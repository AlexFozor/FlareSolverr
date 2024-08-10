ARG PYTHON_BASE=3.12-slim-bookworm

FROM python:$PYTHON_BASE AS builder

# Repository information is needed for dynamic versioning
#COPY .git/ /app/.git/ # FIXME Problems copying ~/.git for scm data

# Source
COPY src/ /app/src
COPY pyproject.toml pdm.lock /app/

# Readme is needed to satisfy PyProject
COPY README.md /app/

# Build dummy packages to skip installing them and their dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends equivs \
    && equivs-control libgl1-mesa-dri \
    && printf 'Section: misc\nPriority: optional\nStandards-Version: 3.9.2\nPackage: libgl1-mesa-dri\nVersion: 99.0.0\nDescription: Dummy package for libgl1-mesa-dri\n' >> libgl1-mesa-dri \
    && equivs-build libgl1-mesa-dri \
    && mv libgl1-mesa-dri_*.deb /libgl1-mesa-dri.deb \
    && equivs-control adwaita-icon-theme \
    && printf 'Section: misc\nPriority: optional\nStandards-Version: 3.9.2\nPackage: adwaita-icon-theme\nVersion: 99.0.0\nDescription: Dummy package for adwaita-icon-theme\n' >> adwaita-icon-theme \
    && equivs-build adwaita-icon-theme \
    && mv adwaita-icon-theme_*.deb /adwaita-icon-theme.deb \
    && apt-get purge -y --auto-remove equivs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Extract version from git
ARG REL_REF=3.3.21
#RUN REL_REF=$(git describe --tags --abbrev=0) # FIXME Problems copying ~/.git for scm data
RUN echo "Building FlareSolverr version $REL_REF"

# Build package
RUN pip install --upgrade pdm
ENV PDM_UPDATE_CHECK=false
ENV PDM_BUILD_SCM_VERSION=$REL_REF
RUN pdm install --check --prod --no-editable --verbose

FROM python:$PYTHON_BASE

# Copy dummy packages
COPY --from=builder /libgl1-mesa-dri.deb /adwaita-icon-theme.deb /
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Install dependencies and create flaresolverr user
WORKDIR /app
RUN apt-get update \
    # Install dummy packages
    && dpkg -i /libgl1-mesa-dri.deb \
    && dpkg -i /adwaita-icon-theme.deb \
    && apt-get install -f \
    # Install dependencies
    && apt-get install -y --no-install-recommends chromium xvfb dumb-init \
        procps curl vim xauth python3 \
    # Remove temporary files and hardware decoding libraries
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /usr/lib/x86_64-linux-gnu/libmfxhw* \
    && rm -f /usr/lib/x86_64-linux-gnu/mfx/* \
    # Create flaresolverr user
    && useradd --home-dir /app --shell /bin/sh flaresolverr \
    && chown -R flaresolverr:flaresolverr . \
    # Remove temporary files
    && rm -rf /root/.cache /tmp/*

USER flaresolverr

RUN mkdir -p "/app/.config/chromium/Crash Reports/pending"

EXPOSE 8191
EXPOSE 8192

# dumb-init avoids zombie chromium processes
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-um", "flaresolverr"]

# Local build
# docker build -t ngosang/flaresolverr:3.3.21 .
# docker run -p 8191:8191 ngosang/flaresolverr:3.3.21

# Multi-arch build
# docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
# docker buildx create --use
# docker buildx build -t ngosang/flaresolverr:3.3.21 --platform linux/386,linux/amd64,linux/arm/v7,linux/arm64/v8 .
#   add --push to publish in DockerHub

# Test multi-arch build
# docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
# docker buildx create --use
# docker buildx build -t ngosang/flaresolverr:3.3.21 --platform linux/arm/v7 --load .
# docker run -p 8191:8191 --platform linux/arm/v7 ngosang/flaresolverr:3.3.21
