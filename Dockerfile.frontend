# 1. Dùng đúng lõi Python 3.11 chuẩn của dự án
FROM python:3.11-slim

# 2. Bơm trực tiếp toàn bộ lõi đồ họa ảo vào sâu trong nhân Hệ điều hành
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    libxkbcommon-x11-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Cài đặt các thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Lệnh trảm: Ép xóa sạch OpenCV giao diện do MediaPipe kéo về, chốt bản Headless
RUN pip uninstall -y opencv-python opencv-contrib-python && \
    pip install --no-cache-dir opencv-python-headless opencv-contrib-python-headless

# 5. Copy toàn bộ code của bạn vào máy chủ
COPY . .

# 6. Khởi động giao diện Streamlit
CMD streamlit run src/frontend/app.py --server.port $PORT --server.address 0.0.0.0