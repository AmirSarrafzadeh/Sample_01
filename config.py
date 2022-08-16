import os
import shutil
import folium
import geojson
import logging
import os.path
import zipfile
import smtplib
import requests
import pycountry
import numpy as np
import pandas as pd
import plotly.io as pio
import geopandas as gpd
from geojson import dump
from email import encoders
import plotly.express as px
from os.path import basename
import imageio.v2 as imageio
import plotly.graph_objs as go
from email.header import Header
import matplotlib.pyplot as plt
import country_converter as coco
from email.utils import formatdate
from email.utils import formataddr
pd.set_option('display.width', 1000)
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from configparser import ConfigParser
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# This function checks all subfiles and subfolders and extract them in a separate folder
def extract_zip(path, file_name):
    for root, folders, files in os.walk(path):
        zip_name = root + os.sep + file_name
        if file_name in files:
            with zipfile.ZipFile(zip_name, 'r') as file:
                file.extractall()

# This function checks the given row, and change all numeric types to float
def check_is_number(row):
    row = row[1:]
    for value in row:
        try:
            float(value)
        except ValueError:
            return False
    return True

# This function download geojson of all countries of the world and save in a geojson file
def download_geojson(url):
    response = requests.get(url)
    geojson = response.json()
    with open('countries.geojson', 'w') as f:
        dump(geojson, f)