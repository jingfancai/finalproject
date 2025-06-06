from datetime import date
import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import date
import gspread
from google_auth_oauthlib.flow import InstalledAppFlow

class Complaint:
    def __init__(self, author, content, latitude, longitude, complaint_date=None):
        self.author = author
        self.content = content
        self.latitude = latitude
        self.longitude = longitude
        self.complaint_date = complaint_date or date.today()

    def __str__(self):
        return f"[{self.complaint_date}] {self.author}：{self.content} (위치: {self.latitude}, {self.longitude})"

st.set_page_config(page_title="동네 민원 신고 플랫폼", layout="wide")
st.title("동네 민원/불편사항 신고 플랫폼")

@st.cache_resource
def get_gsheet_client():
    flow = InstalledAppFlow.from_client_secrets_file(
    'credentials1.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets'])
    creds = flow.run_local_server(port=8080)
    client = gspread.authorize(creds)
    return client

def get_or_create_sheet():
    client = get_gsheet_client()
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1NE0CYC_FgkSN6ankt9-x3uRzBSXWC52kHYc9qIZIp5Q/edit").sheet1
    if sheet.row_count == 0 or sheet.get_all_values() == []:
        sheet.append_row(["작성자", "내용", "위도", "경도", "날짜"])
    elif sheet.row_values(1) != ["작성자", "내용", "위도", "경도", "날짜"]:
        sheet.insert_row(["작성자", "내용", "위도", "경도", "날짜"], 1)
    return sheet
    
st.subheader("민원 등록")

default_lat = 37.5665
default_lon = 126.9780

st.markdown("**위치를 지도에서 클릭하는 대신, 위도와 경도를 직접 입력하세요.**")
lat = st.number_input("위도 (Latitude)", value=default_lat, format="%.6f")
lon = st.number_input("경도 (Longitude)", value=default_lon, format="%.6f")

layer = pdk.Layer(
    'ScatterplotLayer',
    data=pd.DataFrame([{"lat": lat, "lon": lon}]),
    get_position='[lon, lat]',
    get_color='[255, 0, 0, 160]',
    get_radius=100,
)
st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/streets-v11',
    initial_view_state=pdk.ViewState(
        latitude=lat,
        longitude=lon,
        zoom=12,
        pitch=50,
    ),
    layers=[layer],
))

with st.form("complaint_form"):
    author = st.text_input("작성자")
    content = st.text_area("불편 사항 내용")
    complaint_date = st.date_input("작성일", value=date.today())
    submitted = st.form_submit_button("민원 등록")

    if submitted:
        complaint = Complaint(author, content, lat, lon, complaint_date)
        
        st.success("민원이 등록되었습니다!")
        st.write("민원 내용:")
        st.code(str(complaint), language="markdown")
        get_or_create_sheet().append_row([author, content, lat, lon, str(complaint_date)])

        if "complaints" not in st.session_state:
            st.session_state["complaints"] = []
        st.session_state["complaints"].append(complaint)

st.subheader("모든 민원 보기")
sheet1 = get_or_create_sheet()
data = sheet1.get_all_records()
df = pd.DataFrame(data)
