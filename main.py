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
