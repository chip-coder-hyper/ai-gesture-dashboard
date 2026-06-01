from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Đây là file CSDL sẽ tự động được tạo ra trong ổ cứng của bạn
SQLALCHEMY_DATABASE_URL = "sqlite:///./gesture_rag_system.db"

# Khởi tạo động cơ (engine) kết nối với SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Tạo xưởng sản xuất phiên làm việc (session) với CSDL
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Hàm ra lệnh tạo toàn bộ bảng nếu chưa có
def init_db():
    Base.metadata.create_all(bind=engine)

# Hàm cung cấp kết nối (dependency) cho FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()