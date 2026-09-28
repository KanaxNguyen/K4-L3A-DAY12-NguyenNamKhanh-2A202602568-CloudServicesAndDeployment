# Minh Chứng CP5

Ảnh chụp thực tế ngày 28/09/2026:

- [dashboard.png](dashboard.png): bản deploy mới nhất thành công; Uvicorn
  chạy trên `0.0.0.0:10000` và các request `/health` trả HTTP 200.
- [health.png](health.png): ảnh chụp vùng log `/health` trả `200 OK` trên
  Render. Đây là log server, chưa phải ảnh response trực tiếp từ curl/trình duyệt.

[Service công khai](https://day12-agent-dhvl.onrender.com) ·
[Health](https://day12-agent-dhvl.onrender.com/health) ·
[Báo cáo kiểm tra](../DEPLOYMENT.md)

![Render Dashboard](dashboard.png)

![Log health trên Render](health.png)
