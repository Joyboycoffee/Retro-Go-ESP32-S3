FROM espressif/idf:v5.1.4

WORKDIR /app

ADD . /app

# Apply patches
RUN cd /opt/esp/idf && \
	(patch --ignore-whitespace -p1 -i "/app/tools/patches/panic-hook (esp-idf 5).diff" || true) && \
	(patch --ignore-whitespace -p1 -i "/app/tools/patches/sdcard-fix (esp-idf 5).diff" || true)

# Build
SHELL ["/bin/bash", "-c"]
RUN . /opt/esp/idf/export.sh && \
	python rg_tool.py --target=esp32-s3-devkit release
