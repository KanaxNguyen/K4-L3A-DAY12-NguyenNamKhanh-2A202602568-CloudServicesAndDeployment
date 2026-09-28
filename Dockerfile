# ===================================================================
# Stage 1: Builder - Cài đặt dependencies
# ===================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ===================================================================
# Stage 2: Runtime - Image siêu nhẹ, bảo mật non-root
# ===================================================================
FROM python:3.11-slim

WORKDIR /app

# Cài đặt curl cho healthcheck & dọn dẹp cache apt
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy thư viện đã build từ stage builder
COPY --from=builder /install /usr/local

# Tạo user không có đặc quyền (non-root user)
RUN useradd -m -u 1000 appuser

# Copy source code sau khi đã cài xong dependencies (tận dụng cache layer)
COPY . .

# Phân quyền cho appuser
RUN chown -R appuser:appuser /app

# Chuyển sang non-root user
USER appuser

ENV PORT=8000 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Healthcheck định kỳ qua endpoint /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Khởi động app với biến PORT động
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
