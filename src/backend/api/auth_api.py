from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import bcrypt  # SỬ DỤNG BCRYPT TRỰC TIẾP (Thay vì dùng passlib)
from jose import jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from database.db_config import get_db
from database.models import User

# --- 1. CẤU HÌNH BẢO MẬT ---
SECRET_KEY = "khoa-bao-mat-sieu-cap-cua-do-an-rag" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 

# --- 2. CẤU TRÚC DỮ LIỆU ĐẦU VÀO ---
class UserCreate(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

router = APIRouter()

# --- 3. API ĐĂNG KÝ (TẠO TÀI KHOẢN) ---
@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký!")
    
    # Băm mật khẩu bằng bcrypt trực tiếp
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), salt).decode('utf-8')
    
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"status": "success", "message": f"Tài khoản {new_user.email} đã được tạo thành công!"}

# --- 4. API ĐĂNG NHẬP (CẤP VÉ JWT) ---
@router.post("/login", response_model=TokenResponse)
def login_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    
    # Kiểm tra mật khẩu bằng bcrypt trực tiếp
    is_password_correct = False
    if db_user:
        is_password_correct = bcrypt.checkpw(
            user.password.encode('utf-8'), 
            db_user.hashed_password.encode('utf-8')
        )
        
    if not db_user or not is_password_correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Tạo vé thông hành (JWT Token)
    expire_time = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {"sub": db_user.email, "exp": expire_time}
    encoded_jwt = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": encoded_jwt, "token_type": "bearer"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Hàm kiểm tra vé và lấy ra thông tin User đang gọi API
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin vé (Token không hợp lệ)!",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Giải mã cái vé JWT xem bên trong chứa email gì
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Đối chiếu email với cơ sở dữ liệu
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
        
    return user