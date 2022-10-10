import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import requests, os
from gwpy.timeseries import TimeSeries
from gwosc.locate import get_urls
from gwosc import datasets
from gwosc.api import fetch_event_json
import matplotlib as mpl
import boto3
import io

aws_access_key_id = 'AKIAWYPL22X6A3VXRWX2' # Better not to directly expose in source code
aws_secret_access_key = '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'
s3 = boto3.resource(
                "s3",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
bucket = s3.Bucket('sentinel-s2-l1c')

from copy import deepcopy
import base64

from helper import make_audio_file

# Use the non-interactive Agg backend, which is recommended as a
# thread-safe backend.
# See https://matplotlib.org/3.3.2/faq/howto_faq.html#working-with-threads.

mpl.use("agg")

##############################################################################
# Workaround for the limited multi-threading support in matplotlib.
# Per the docs, we will avoid using `matplotlib.pyplot` for figures:
# https://matplotlib.org/3.3.2/faq/howto_faq.html#how-to-use-matplotlib-in-a-web-application-server.
# Moreover, we will guard all operations on the figure instances by the
# class-level lock in the Agg backend.
##############################################################################
from matplotlib.backends.backend_agg import RendererAgg
_lock = RendererAgg.lock


# -- Set page config
apptitle = 'GW Quickview'

st.set_page_config(page_title=apptitle, page_icon=":eyeglasses:")

# -- Default detector list
detectorlist = ['H1','L1', 'V1']

# Title the app
st.title('Patient View')

st.markdown("""
 * Use the menu at left to select data and set plot parameters
 * Your plots will appear below
""")

# @st.cache(ttl=3600, max_entries=10)   #-- Magic command to cache data
# def load_gw(t0, detector, fs=4096):
#     strain = TimeSeries.fetch_open_data(detector, t0-14, t0+14, sample_rate = fs, cache=False)
#     return strain
#
# @st.cache(ttl=3600, max_entries=10)   #-- Magic command to cache data
# def get_eventlist():
#     allevents = datasets.find_datasets(type='events')
#     eventset = set()
#     for ev in allevents:
#         name = fetch_event_json(ev)['events'][ev]['commonName']
#         if name[0:2] == 'GW':
#             eventset.add(name)
#     eventlist = list(eventset)
#     eventlist.sort()
#     return eventlist
    
st.sidebar.markdown("## Select Data Time and Detector")

# # -- Get list of events
# eventlist = get_eventlist()

#-- Set time by GPS or event
# select_event = st.sidebar.selectbox('How do you want to find data?',
#                                     ['By event name', 'By GPS'])
patient_id = st.number_input('Insert patient')
url = 'https://czp2w6uy37.execute-api.us-east-1.amazonaws.com/test/get_patient'
# get_table_test = "https://czp2w6uy37.execute-api.us-east-1.amazonaws.com/test/Table?questionnaire = ('MADRS')"
url_get = f"{url}?patient ='{patient_id}'"
patient_response = requests.get(url_get).json()

df_questionnaire = pd.DataFrame(columns= ['questionnaire_name', 'encounter_date','score'])
questionnaire_list = []

for i in patient_response['questionnaire_response'][0]:
    # if i['questionnaire_name'] not in questionnaire_list:
    #     questionnaire_list.append( i['questionnaire_name'])
    df_questionnaire = df_questionnaire.append({'questionnaire_name': i['questionnaire_name'], 'encounter_date': i['encounter_date'],'score': i['score']}, ignore_index=True)
chosen_questionnaire = st.sidebar.selectbox('Select Questionnaire', list(df_questionnaire['questionnaire_name'].unique()))


url_eeg = 'https://czp2w6uy37.execute-api.us-east-1.amazonaws.com/test/get_patient_eeg'
url_get_eeg = f"{url}?patient='{patient_id}'"
eeg_patient_response = requests.get(url_get_eeg).json()

score_list = []
df_scores = pd.DataFrame(columns= ['score', 'plot_url'])
for i in patient_response['plot_urls']:
    df_scores = df_scores.append({'score':i['score'], 'plot_url':i['plot_url']},ignore_index= True)
    # if i['score'] not in score_list:
    #     score_list.append( i['score'])
score = st.sidebar.selectbox('EEG_Parameter', list(df_scores))
score_url = df_scores.loc[df_scores['score']==score,'plot_url'].values[0]

# t0 = datasets.event_gps(chosen_questionnaire)
# detectorlist = list(datasets.event_detectors(chosen_event))
# detectorlist.sort()
# st.subheader(chosen_event)
# st.write('GPS:', t0)
# if select_event == 'By GPS':
#     # -- Set a GPS time:
#     str_t0 = st.sidebar.text_input('GPS Time', '1126259462.4')    # -- GW150914
#     t0 = float(str_t0)
#
#     st.sidebar.markdown("""
#     Example times in the H1 detector:
#     * 1126259462.4    (GW150914)
#     * 1187008882.4    (GW170817)
#     * 1128667463.0    (hardware injection)
#     * 1132401286.33   (Koi Fish Glitch)
#     """)
#
# else:
#     chosen_event = st.sidebar.selectbox('Select Event', eventlist)
#     t0 = datasets.event_gps(chosen_event)
#     detectorlist = list(datasets.event_detectors(chosen_event))
#     detectorlist.sort()
#     st.subheader(chosen_event)
#     st.write('GPS:', t0)
#
#     # -- Experiment to display masses
#     try:
#         jsoninfo = fetch_event_json(chosen_event)
#         for name, nameinfo in jsoninfo['events'].items():
#             st.write('Mass 1:', nameinfo['mass_1_source'], 'M$_{\odot}$')
#             st.write('Mass 2:', nameinfo['mass_2_source'], 'M$_{\odot}$')
#             st.write('Network SNR:', int(nameinfo['network_matched_filter_snr']))
#             eventurl = 'https://gw-osc.org/eventapi/html/event/{}'.format(chosen_event)
#             st.markdown('Event page: {}'.format(eventurl))
#             st.write('\n')
#     except:
#         pass

    
#-- Choose detector as H1, L1, or V1




#-- Make a time series plot


st.subheader('Raw data')
# center = int(t0)
# strain = deepcopy(strain_data)

with _lock:
    df_questionnaire_new = df_questionnaire[df_questionnaire['questionnaire_name'] == chosen_questionnaire].copy()
    df_questionnaire_new["encounter_date"] = df_questionnaire_new["encounter_date"].astype("datetime64")

    # Setting the Date as index

    df_questionnaire_new = df_questionnaire_new.set_index("encounter_date")
    fig, ax = plt.subplots()
    ax.plot(df_questionnaire_new["score"], marker='o')

    st.pyplot(fig)

    # Labelling

    plt.xlabel("Date")
    plt.ylabel("Temp in Faherenheit")
    plt.title("Pandas Time Series Plot")
    object = bucket.Object(score_url)

    file_stream = io.StringIO()
    object.download_fileobj(file_stream)
    img = mpimg.imread(file_stream)
    # st.image(img)
    # fig1 = strain.crop(cropstart, cropend).plot()
    # #fig1 = cropped.plot()
    # st.pyplot(fig1, clear_figure=True)



with _lock:
#     fig3 = bp_cropped.plot()
    file_stream = io.StringIO()
    object.download_fileobj(file_stream)
    img = mpimg.imread(file_stream)
    st.image(img)

