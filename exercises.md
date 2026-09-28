# Phiếu Phản Ánh — K4 Level 3A, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Các câu trả lời dựa trên mã nguồn và phép kiểm tra thực tế ngày 28/09/2026.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Nguyễn Nam Khánh — Mã học viên: 2A202602568

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Một tình huống cụ thể là deploy lên Render nhưng quên cấu hình
`AGENT_API_KEY`. Nếu mặc định là `changeme`, ứng dụng vẫn nhận request và
người biết khóa mẫu có thể gọi `/ask`, sử dụng tài nguyên hoặc làm phát sinh
chi phí LLM. Trường bắt buộc khiến `Settings` báo lỗi `Field required`, buộc
tôi bổ sung secret trên dashboard trước khi sử dụng API.

Tôi đã gặp lỗi thiếu biến này trên Render. Tuy nhiên, mã hiện tại đọc
`Settings` khi cần, chưa gọi `get_settings()` trong `lifespan`, nên service
vẫn khởi động và `/health` vẫn trả 200; `/ready` và `/ask` mới trả 500.
Không có giá trị mặc định giúp phát hiện thiếu cấu hình khi tạo `Settings`;
muốn thật sự dừng ngay lúc khởi động thì cần kiểm tra cấu hình trong
`lifespan` trước khi nhận request.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

Dòng sau lấy từ `docker compose logs --no-color agent` của stack kiểm tra
cục bộ sau khi gọi `/ask` với user `exercises-scale`:

```json
{"event": "ask_completed", "level": "info", "timestamp": "2026-09-28T10:04:48.964394+00:00", "user_id": "exercises-scale", "tokens_in": 114, "tokens_out": 50, "cost_usd": 4.71e-05}
```

Từ log này tôi có thể:

1. Lọc theo `event`, `user_id` và `timestamp` để tìm các request của một
   user trong khoảng thời gian xảy ra sự cố.
2. Cộng `cost_usd`, `tokens_in`, `tokens_out` theo user hoặc ngày để theo
   dõi chi phí và phát hiện mức sử dụng tăng bất thường.

Chuỗi `print("đã trả lời xong")` không cung cấp thời điểm, user hay số liệu
để làm hai việc này. Mỗi dòng log của tôi là một JSON object, có thể đưa
vào công cụ phân tích mà không phải tách một câu văn tự do.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f evidence/exercises/Dockerfile.single -t day12-agent:exercise-single .
docker build -t day12-agent:exercise-multi .
docker image inspect day12-agent:exercise-single day12-agent:exercise-multi \
  --format '{{index .RepoTags 0}} {{.Size}}'
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản dựng để so sánh) | 332,83 MB — 332.826.019 byte |
| Multi-stage (`Dockerfile` hiện tại) | 316,29 MB — 316.289.156 byte |

Giải thích: phần dung lượng chênh lệch đó là những gì?

Đây là số đo thật bằng Docker Desktop trên `linux/arm64`; MB trong bảng
được tính bằng byte chia cho 1.000.000. Hai bản cùng dùng `python:3.11-slim`,
cùng source, curl và non-root user. Tôi đã đối chiếu `pip freeze`: phiên bản
dependency giống nhau. Bản một stage là bản dựng để so sánh, không phải số
đo lịch sử của một image trước đây chưa được lưu lại.

Multi-stage nhỏ hơn khoảng 16,54 MB, tức khoảng 4,97%. `docker history`
cho thấy layer cài pip của bản một stage khoảng 78,4 MB, còn layer copy
`/install` sang runtime khoảng 65,9 MB. Kiểm tra filesystem cho thấy
bản một stage có khoảng 5,50 MB bytecode `.pyc` nhiều hơn. Cách cài đặt và
nội dung các layer tạo ra chênh lệch; không thể quy toàn bộ số đó cho compiler,
vì hai Dockerfile này không cài compiler.

Nguyên tắc của multi-stage là chỉ chuyển artifact cần chạy sang image cuối;
công cụ build, cache và file trung gian của builder không cần đưa theo.
Lợi ích thực tế phụ thuộc những gì builder chứa, nên không mặc định rằng
cứ có hai stage là image sẽ nhỏ hơn rất nhiều.
[Tham khảo Docker](https://docs.docker.com/build/building/multi-stage/).

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

Tôi thử thêm một ký tự xuống dòng vào `app/main.py` trong một bản sao của
build context rồi build lại bằng đúng Dockerfile hiện tại. Log build ghi
`CACHED` ở các bước `WORKDIR`, copy `requirements.txt`, `pip install` của
builder, cài curl, copy thư viện từ builder và tạo `appuser`. Hai bước
`COPY . .` và `RUN chown -R appuser:appuser /app` chạy lại vì nội dung source
đã thay đổi.

Nếu đặt `COPY . .` trước `RUN pip install` trong cùng stage, mỗi lần sửa code
sẽ làm mất cache của bước copy và những bước sau nó, nên phải chạy lại pip
dù `requirements.txt` không đổi. Dockerfile hiện tại tách copy dependency
khỏi copy source, nên thay đổi logic ứng dụng không bắt cài lại thư viện.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

Ví dụ một endpoint xử lý dữ liệu không an toàn làm kẻ tấn công thực thi được
lệnh trong process Python. Nếu process chạy root, họ có quyền root trong
container và có thể sửa nhiều file hoặc truy cập tài nguyên được cấp cho
container. Nếu còn có lỗ hổng escape trong kernel/runtime, mount nhạy cảm
hay Docker socket được đưa vào container, quyền này có thể trở thành bước
đệm để chiếm quyền cao trên host.

`USER appuser` trong Dockerfile khiến ứng dụng chạy UID 1000. Lệnh mà kẻ
tấn công thực thi qua process cũng chỉ có quyền của user này, giảm khả năng
sửa file hệ thống hoặc thực hiện thao tác cần root ngay từ bước đầu.
Root trong container không tự động đồng nghĩa root trên host; vẫn cần một
đường vượt ranh giới cách ly. Non-root giảm thiệt hại nhưng không thay thế
việc vá lỗ hổng và cấu hình quyền, mount, capability an toàn.
[Tham khảo bảo mật Docker](https://docs.docker.com/engine/security/).

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

Với fixed window reset ở giây 00, user có thể gửi 20 request trong hai giây
quanh ranh giới phút: 10 request lúc 10:00:59 và 10 request lúc 10:01:00.
Mỗi phút riêng vẫn chỉ có 10 request, nhưng thực tế có một đợt dồn 20 request.

Sliding window của tôi đếm mọi request trong 60 giây gần nhất bằng Redis
sorted set. Khi user gửi tiếp ở đầu phút mới, 10 request vừa gửi cuối phút
trước vẫn nằm trong cửa sổ, nên request tiếp theo bị chặn với HTTP 429.
Timestamp làm score; UUID trong member tránh ghi đè khi các request có
cùng timestamp.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

Rate limit giới hạn tốc độ gửi request trong 60 giây gần nhất, còn cost
guard giới hạn tổng tiền đã dùng theo user và tháng. Hai cơ chế bảo vệ hai
loại tài nguyên khác nhau, nên cần dùng cùng nhau.

- Rate limit cho qua nhưng cost guard chặn: user mới gửi một request trong
  phút, nhưng đã tiêu 10,01 USD trong tháng với ngân sách 10 USD. Request
  không quá nhanh, nhưng cost guard trả HTTP 402.
- Cost guard vẫn cho phép nhưng rate limit chặn: user chỉ mới tiêu 0,01 USD
  trong tháng, nhưng đã gửi đủ 10 request trong 60 giây. Request thứ 11 bị
  chặn với HTTP 429 dù còn nhiều tiền.

Trong `/ask`, tôi kiểm tra rate limit rồi cost guard trước khi gọi LLM.
`guard.check(user_id)` hiện chưa truyền dự toán chi phí request mới, nên
vẫn có thể vượt ngân sách thêm chi phí của một request. Nếu cần giới hạn
ngân sách chặt hơn, phải truyền `estimated_cost` hoặc dành trước ngân sách
cho request trước khi gọi LLM.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

Nếu endpoint dùng chung kiểm tra Redis, thứ tự xảy ra là:

1. Redis mất kết nối; cả ba container còn chạy nhưng probe gọi Redis thất bại.
2. Khi đủ ngưỡng thất bại, bộ điều phối hoặc load balancer dùng readiness
   coi các instance là chưa sẵn sàng và ngừng gửi traffic đến chúng.
3. Nếu cùng probe đó còn được dùng làm liveness với chính sách restart,
   các process khỏe cũng có thể bị khởi động lại. Restart không khắc phục
   Redis đang mất kết nối, nên có thể làm hệ thống gián đoạn thêm.
4. Khi Redis hoạt động trở lại sau 30 giây, những instance còn chạy hoặc
   đã khởi động xong mới trả probe thành công và được nhận traffic lại.

Không phải cứ Redis mất 30 giây là chắc chắn cả ba container bị restart:
điều đó còn phụ thuộc chu kỳ, số lần retry và chính sách của platform.
Docker Compose với `HEALTHCHECK` đơn thuần đánh dấu `unhealthy`, không tự
restart chỉ vì trạng thái này. Compose hiện tại kiểm tra mỗi 10 giây và
cho 5 lần retry, nên khoảng mất kết nối 30 giây có thể chưa đủ ngưỡng.

Tách endpoint giúp `/health` chỉ báo process còn sống, còn `/ready` trả
503 khi không nối được Redis. Khi dependency tạm lỗi, hệ thống có thể
ngừng gửi traffic mà không cần restart process đang khỏe.
[Tham khảo HEALTHCHECK](https://docs.docker.com/reference/dockerfile/#healthcheck).

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

Tôi chạy ba agent dùng chung một Redis trong Compose project riêng
`day12-exercises`, rồi gửi tuần tự bốn request cùng `X-User-Id` là
`exercises-scale` qua instance 1, 2, 3, 1. Kết quả thật:

| Lượt hỏi | Instance nhận request | `history_length` |
|---|---|---|
| 1 | 1 | 0 |
| 2 | 2 | 2 |
| 3 | 3 | 4 |
| 4 | 1 | 6 |

Mỗi lượt thêm hai message: câu hỏi của user và câu trả lời của assistant.
Response trả độ dài lịch sử trước khi thêm lượt mới, nên lần đầu bằng 0.
Instance 2 và 3 thấy dữ liệu do instance trước ghi vì lịch sử nằm trong Redis.

Nếu thay Redis bằng dict riêng trong mỗi process, với cùng thứ tự gọi trên,
tôi dự đoán độ dài là 0, 0, 0, 2: mỗi instance bắt đầu với lịch sử riêng;
khi quay lại instance 1 mới thấy hai message ở lần hỏi đầu. Khi request được
phân phối giữa các instance, số này có thể tăng rồi giảm, làm hội thoại mất
ngữ cảnh. Đây là suy luận cho phương án dict, không phải số đo của stack Redis.

Code hiện tại giới hạn 20 message và TTL 7 ngày, nên lịch sử không tăng vô
hạn. Tôi dùng [Compose kiểm tra](evidence/exercises/compose.yaml) không publish
cổng host vì Compose gốc cố định `8000:8000`, sẽ xung đột nếu scale trực tiếp
ba agent. Request được gửi vào từng container qua `docker compose exec`.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

Khi kiểm tra bản deploy trên Render ngày 28/09/2026, `/health` trả 200
nhưng `/ready` và `/ask` trả 500. Log báo `ValidationError` cho `Settings`,
trường `agent_api_key` có lỗi `Field required`. Kiểm tra trang Environment
cho thấy chưa có biến `AGENT_API_KEY`. File `.env` trên máy không được đưa
vào Docker image, nên khóa cục bộ không tự có trên cloud.

Cách khắc phục là thêm `AGENT_API_KEY` trong Render Environment, lưu và
deploy lại, rồi chạy `pytest tests/test_cp5.py -v --tb=short`. Khóa dùng cho
test được lưu riêng trong `DEPLOY_API_KEY` ở `.env`, không đưa vào Git.
Sau khi thêm tên biến nhưng để Value trống, lỗi 500 hết nhưng request có
khóa vẫn nhận 401. Cần nhập khóa thật giống khóa kiểm thử cục bộ, lưu và
deploy lại.

Kiểm tra mới nhất ngày 28/09/2026 bằng
`.venv/bin/python -m pytest tests/test_cp5.py -v --tb=short` đã đạt
**9 passed, 4 skipped in 2.18s**. `/health` và `/ready` trả 200, `/ask` không
có khóa trả 401, `/ask` có khóa đúng trả 200 và có câu trả lời. Bốn test
skipped thuộc phương án local fallback, không phải lỗi cloud. Liên kết
service và log nằm trong [DEPLOYMENT.md](DEPLOYMENT.md).
