import streamlit as st
import pandas as pd
import hashlib
import os
from PIL import Image
from io import BytesIO
from datetime import datetime

USER_CSV_PATH = "users.csv"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_user_csv():
    if not os.path.exists(USER_CSV_PATH):
        df = pd.DataFrame(columns=["username", "password", "is_approved"])
        df.to_csv(USER_CSV_PATH, index=False)

def register_user(username, password):
    df = pd.read_csv(USER_CSV_PATH)
    if username in df.username.values:
        return False, "이미 존재하는 사용자입니다."
    hashed_pw = hash_password(password)
    new_user = pd.DataFrame([[username, hashed_pw, False]], columns=df.columns)
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv(USER_CSV_PATH, index=False)
    return True, "회원가입 완료. 관리자 승인 후 로그인 가능"

def check_login(username, password):
    df = pd.read_csv(USER_CSV_PATH)
    hashed_pw = hash_password(password)
    row = df[(df["username"] == username) & (df["password"] == hashed_pw)]
    if not row.empty and row.iloc[0]["is_approved"]:
        return True
    return False

def create_image_grid(uploaded_images, grid_size=3, image_size=300):
    images = []
    for file in uploaded_images[:grid_size*grid_size]:
        img = Image.open(file).convert("RGB")
        img = img.resize((image_size, image_size))
        images.append(img)
    grid = Image.new("RGB", (image_size*grid_size, image_size*grid_size), (255,255,255))
    for idx, img in enumerate(images):
        x = (idx % grid_size) * image_size
        y = (idx // grid_size) * image_size
        grid.paste(img, (x, y))
    return grid

# ✅ 초기 설정
st.set_page_config(page_title="기린 로그인 시스템", page_icon="🔐")
init_user_csv()

# ✅ 세션 상태
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = ""

# ✅ 로그인 화면
st.sidebar.header("🔐 로그인")
user = st.sidebar.text_input("아이디")
pw = st.sidebar.text_input("비밀번호", type="password")
if st.sidebar.button("로그인"):
    if check_login(user, pw):
        st.session_state.logged_in = True
        st.session_state.user_id = user
        st.sidebar.success("로그인 성공!")
    else:
        st.sidebar.error("로그인 실패 또는 승인되지 않은 사용자")

# ✅ 회원가입
st.sidebar.markdown("---")
st.sidebar.header("📥 회원가입")
new_user = st.sidebar.text_input("신규 아이디")
new_pw = st.sidebar.text_input("신규 비밀번호", type="password")
if st.sidebar.button("회원가입 요청"):
    ok, msg = register_user(new_user, new_pw)
    if ok:
        st.sidebar.success(msg)
    else:
        st.sidebar.error(msg)

# ✅ 로그인된 사용자 화면
if st.session_state.logged_in:
    st.success(f"{st.session_state.user_id}님 환영합니다 🎉")
    st.markdown("---")
    st.header("🖼 목록 이미지 만들기")

    grid_col = st.selectbox("이미지를 몇 개씩 나열할까요? (한 줄에)", [1, 2, 3, 4, 5], index=2)
    image_size = st.selectbox("완성 이미지 크기를 선택하세요 (정사각형 한 변 기준)", [300, 500, 800, 1000], index=0)

    uploaded = st.file_uploader("이미지를 여러 장 업로드하세요 (최대 9장)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if uploaded:
        st.markdown("#### ✅ 체크할 이미지 파일을 선택하세요:")
        checked_files = []
        for file in uploaded:
            if st.checkbox(file.name, value=True):
                checked_files.append(file)

        if checked_files:
            st.markdown("#### ✅ 선택된 파일명:")
            for file in checked_files:
                st.write(f"- {file.name}")

            img_result = create_image_grid(checked_files, grid_size=grid_col, image_size=image_size)
            st.image(img_result, caption="목록 이미지 결과", use_column_width=False)
            buffer = BytesIO()
            img_result.save(buffer, format="JPEG")
            st.download_button("🧾 목록 이미지 다운로드", data=buffer.getvalue(), file_name="목록이미지.jpg", mime="image/jpeg")

    # ✅ GIF 만들기
    st.markdown("---")
    st.subheader("🎞 GIF 만들기")
    gif_speed = st.slider("GIF 전환 속도 (초)", min_value=0.1, max_value=3.0, step=0.1, value=1.0)
    if uploaded:
        if st.button("🎬 GIF 생성하기"):
            gif_images = []
            for file in checked_files:
                img = Image.open(file).convert("RGB")
                gif_images.append(img)

            gif_path = "girin_output.gif"
            gif_images[0].save(gif_path, save_all=True, append_images=gif_images[1:], duration=int(gif_speed*1000), loop=0)
            with open(gif_path, "rb") as f:
                gif_bytes = f.read()
                st.image(gif_bytes, caption="생성된 GIF", use_column_width=False)
                st.download_button("📥 GIF 다운로드", data=gif_bytes, file_name="목록이미지.gif", mime="image/gif")
