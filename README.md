# AI-Gesture-QA-Dashboard

## 1. Project Overview
AI-Gesture-QA-Dashboard là một hệ thống tương tác thông minh cho phép người dùng giao tiếp với trí tuệ nhân tạo thông qua cử chỉ tay. Hệ thống phân tích tài liệu văn bản, tạo bộ câu hỏi gợi ý và cho phép người dùng chọn câu hỏi bằng cách sử dụng các cử chỉ tay (nhận diện qua camera) mà không cần chạm vào thiết bị.

## 2. System Architecture
Dự án được xây dựng theo mô hình Client-Server:
- **Backend (FastAPI)**: Đảm nhận xử lý logic, quản lý tài khoản, lưu trữ tài liệu, tích hợp LLM để xử lý câu hỏi và câu trả lời.
- **Frontend (Streamlit)**: Giao diện người dùng web, sử dụng `streamlit-webrtc` để xử lý video stream thời gian thực và `MediaPipe` để phát hiện cử chỉ tay.

## 3. Project Structure
```text
AI-Gesture-QA-Dashboard/
├── src/
│   ├── backend/             # Server chính
│   │   ├── api/             # Các endpoint API (auth, gesture, document)
│   │   └── main.py          # Entry point của FastAPI
│   └── frontend/            # Client chính
│       ├── utils/           # Logic xử lý (camera, hand_tracker, api_client)
│       ├── views/           # Các màn hình hiển thị (dashboard, chat)
│       └── app.py           # Entry point của Streamlit
└── README.md                # Tài liệu dự án
```

## 4. Key Features
- **Authentication**: Đăng ký/Đăng nhập khách (guest access).
- **Document Analysis**: Upload tài liệu và trích xuất câu hỏi từ nội dung.
- **Gesture Control**: 
  - Nhận diện cử chỉ tay thông qua MediaPipe.
  - Xử lý lock tín hiệu (giữ 2 giây) để chọn câu hỏi.
- **Interactive UI**: Dashboard trực quan hiển thị luồng chat và camera feed.

## 5. Core Workflow
1. **Khởi tạo**: Người dùng truy cập hệ thống và được tự động đăng nhập với tài khoản khách.
2. **Upload**: Tải tài liệu lên backend để LLM phân tích và tạo ra 3 câu hỏi gợi ý.
3. **Detection**: Camera (thông qua `camera_processor.py`) bắt đầu nhận diện tay.
4. **Trigger**: Khi phát hiện ngón tay (ví dụ: 1 ngón, 2 ngón), hệ thống kiểm tra ngưỡng thời gian (2s) để xác nhận tín hiệu.
5. **QA Flow**: Backend tiếp nhận lệnh cử chỉ, trả về câu trả lời tương ứng với câu hỏi đã chọn.

## 6. Technical Stack
- **Languages**: Python 3.10+
- **Backend**: FastAPI, SQLAlchemy, Uvicorn
- **Frontend**: Streamlit, streamlit-webrtc
- **AI/CV**: MediaPipe, PyTorch/Transformers (LLM)
- **API Communication**: Requests, REST API

## 7. Installation & Setup
1. **Clone project**: 
   `git clone <repository_url>`
2. **Environment Setup**: 
   `pip install -r requirements.txt`
3. **Run Backend**:
   `cd src/backend && uvicorn main:app --reload`
4. **Run Frontend**:
   `cd src/frontend && streamlit run app.py`

---
*Tài liệu này được tạo bởi Tôm - Trợ lý AI.*
