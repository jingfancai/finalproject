from datetime import date
import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import date
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import folium
from streamlit_folium import st_folium

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
    scopes=['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scopes)
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

default_location = [37.5665, 126.9780]
st.markdown("**위치를 지도에서 클릭하고 민원내용을 입력하세요.**")
m = folium.Map(location=default_location, zoom_start=12)
map_data = st_folium(m, height=600, width=1000)
lat, lon = None, None

if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"선택한 위치：위도 {lat:.6f}, 경도 {lon:.6f}")

if lat and lon:
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
@st.cache_data(ttl=60) 
def get_sheet_data():
    sheet = get_or_create_sheet()
    return sheet.get_all_records()
data = get_sheet_data()
df = pd.DataFrame(data)

if df.empty:
    st.warning("Google Sheet에서 데이터를 불러오지 못했습니다.")
else:
    df = df.rename(columns={"위도": "lat", "경도": "lon" ,"날짜": "date","작성자": "author","내용": "content"})
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])
    st.map(df)
    for _, row in df.iterrows():
        st.text(f"{row['date']} | {row['author']} | {row['content']} ({row['lat']}, {row['lon']})")
sheet_url = "https://docs.google.com/spreadsheets/d/1NE0CYC_FgkSN6ankt9-x3uRzBSXWC52kHYc9qIZIp5Q/edit"
st.markdown(f"[👉 Google Sheet 바로가기]({sheet_url})")
st.subheader("작성자별 민원 조회")
search_author = st.text_input("작성자 이름을 입력하세요:")
if st.button("조회"):
    filtered = df[df["author"] == search_author]
    st.write(filtered)
st.subheader("날짜별 민원 수")
if not df.empty:
    count_by_date = df["date"].value_counts().sort_index()
    st.bar_chart(count_by_date)
