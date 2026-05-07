import pandas as pd
import streamlit as st
import datetime
from StationLoadDaily import WeatherLoad


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<Page Setup>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#Creating Title on GUI page
st.title('ET Estimation Tool')

#Creating explaination for tool
st.write('Welcome to the ET Estimation Tool! This page allows you to ' \
'calculate an estimate of reference evapotranspiration (ET) for a given day '
'and site using historical weather data.')

#Creating Subtitle on GUI page
st.subheader('Please select the following parameters to calculate the reference ET for the day:')

#Creating a Station Selector Dropdown 
station = st.selectbox('Select Station', ('GLY04', 'ALT01', 'LCN01'), index = 0, placeholder = 'Station')

#Creating a Date Selector
date = st.date_input('Select Date', datetime.date(2025, 5, 1), min_value = datetime.date(2025, 1, 1), max_value = datetime.date(2025, 12, 31))

#Creating further explaination for sliders
st.divider()
st.write('Reference ET is calculated by using many different weather parameters, ' \
'but largely relies on relative humidity, air temperature, wind speed, and solar radiation.')

st.write('The sliders below allow you to alter inputs of the reference ET calculation ' \
'to demonstrate their relative importance to the end estimate. The starting values for each'\
' slider are the historical average of each parameter for the selected station and day.'\
' Feel free to play around with the values to see how ET is calculated!')
st.divider()
#<<<<<<<<<<<<<<<<<<<<<<<<<<Optional Displays>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#Creating checkbox to display 
explain = st.checkbox('Explain Slider Bounds')

if explain:
    st.divider()
    st.write('Relative Humidity: The bounds are expressed as percentages showing both minimum and maximum relative humidity throughout the day. When relative humidity is 100%, the air is fully saturated. Relative humidity cannot be over 100% or under 0%.')
    st.divider()
    st.write('Temperature: The bounds are expressed in degrees Fahrenheit showing both minimum and maximum temperatures throughout the day. The bounds of this slider are determined by realistic temperatures based on historical weather data.')
    st.divider()
    st.write('Wind Speed: The bounds of this slider are determined by wind speeds that are allowed within the model parameters. The minimum bound is placed at 0.5m/s to account for boundary effects of the atmosphere. The maximum bound is determined by the highest observed wind speed from historical data.')
    st.divider()
    st.write('Solar Radiation: The minimum possible solar radiaition for the day is zero, and the maximum bound is determined by calculating clear sky solar radiation. This parameter is based on the day of the year and the latitude of the station.')
    st.divider()

#<<<<<<<<<<<<<<<<<<<<<<<<<<Creating Sliders>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#Loading in StationLoadDaily parameters
load = WeatherLoad()
stationload = load.stationload(date, station)

#Creating Slider for RH
#Creating bounds for slider
min_bound_rh = 0.0
max_bound_rh = 100.0
#Loading in historical average relative humidity from StationLoadDaily
hist_avg_rhmax = load.rhmax
hist_avg_rhmin = load.rhmin
#Creating the slider and filling in bounds
RH = st.slider('Minimum and Maximum Relative Humidity (%)', min_bound_rh,max_bound_rh,(hist_avg_rhmin, hist_avg_rhmax))
RH1 = RH[0]
RH2 = RH[1]

#Creating Slider for Temperature
#Creating bounds for slider
min_bound_temp = -25.0
max_bound_temp = 110.0
#Loading in historical average temperature from StationLoadDaily
hist_avg_tempmax = load.tmax
hist_avg_tempmin = load.tmin
#Converting the historical average temperature to fahrenheit
hist_avg_tempmax = hist_avg_tempmax * 1.8 + 32
hist_avg_tempmin = hist_avg_tempmin * 1.8 + 32
#Creating the slider and filling in bounds
T = st.slider('Minimum and Maximum Air Temperature(°F)', min_bound_temp,max_bound_temp,(hist_avg_tempmin, hist_avg_tempmax))
#Pulling the slider values and converting them back to celsius
T1 = (T[0]-32)*(5/9)
T2 = (T[1]-32)*(5/9) 

#Creating Slider for Wind Speed
#Minimum Wind Speed set to 0.5 to consider boundary effects
min_wndsp = 0.5
max_wndsp = 10.0
#Loading historical average wind speed from StationLoadDaily
hist_avg_wndsp = load.wndsp
#Creating the slider and filling in bounds
WS = st.slider('Average Wind Speed(m/s)', min_wndsp, max_wndsp, hist_avg_wndsp)


#Creating Slider for Rs
#Gathering clear sky solar radiation from StationLoadDaily
rso_long = load.rso_calc()
#Formatting rso to match slider requirements
rso = round(rso_long, 2)
#Adding other bounds for slider as variables so that type error does not occur
#Minimum Solar Radiaiton set to zero
min_srad = 0.0
#Slider start value as historical average
#Loading historical average solar radiation from StationLoadDaily
hist_avg__srad = load.israd
#Finally creating the slider with bounds defined above
RS = st.slider('Total Solar Radiation(MJ/m^2)', min_srad, rso, hist_avg__srad)

#Creating Columns
col1, col2 = st.columns(2, gap = 'large', vertical_alignment='top')
with col1:


    asce1 = st.button('Calculate Reference ET with Historical Values')
    if asce1: 
        df = load.stationload(date, station)
        ET = load.ascedaily(rfcrp = load.params['rfcrp'], z = load.params['z'], 
                            lat = load.params['lat'], doy = load.doy, israd = load.israd,
                            tmax = load.tmax, tmin = load.tmin, rhmax = load.rhmax,
                            rhmin = load.rhmin, wndsp = load.wndsp,
                            wndht = load.params['wndht'])
        ET = round(ET, 2)
        st.write('<big>The estimated reference ET for the day is (mm):  </big>', unsafe_allow_html=True)
        st.write(f'<big>{ET} </big>', unsafe_allow_html=True)

with col2:
    rounded_RH1 = round(RH1, 2)
    rounded_RH2 = round(RH2, 2)
    rounded_T1 = round(T[0], 2)
    rounded_T2 = round(T[1], 2)
    rounded_WS = round(WS, 2)
    rounded_RS = round(RS, 2)
    asce2 = st.button('Calculate Reference ET with Slider Values')
    if asce2: 
        df = load.stationload(date, station)
        ET = load.ascedaily(rfcrp = load.params['rfcrp'], z = load.params['z'], 
                            lat = load.params['lat'], doy = load.doy, israd = RS, 
                            tmax = T2, tmin = T1, rhmax = RH2,
                            rhmin = RH1, wndsp = WS,
                            wndht = load.params['wndht'])
        ET = round(ET, 2)
        st.write('<big>The estimated reference ET for the day is (mm):  </big>', unsafe_allow_html=True)
        st.write(f'<big>{ET} </big>', unsafe_allow_html=True)
   
with st.sidebar:
    #Creating clicker box to show historical input values
    hist_button = st.checkbox('Show Historical Input Values')
    hist_avg_rhmax = round(hist_avg_rhmax, 2)
    hist_avg_rhmin = round(hist_avg_rhmin, 2)
    hist_avg_tempmax = round(hist_avg_tempmax, 2)
    hist_avg_tempmin = round(hist_avg_tempmin, 2)
    hist_avg_wndsp = round(hist_avg_wndsp, 2)
    hist_avg__srad = round(hist_avg__srad, 2)
    if hist_button:
        st.write('Relative Humidity: ', hist_avg_rhmin, '% to ', hist_avg_rhmax, '%')
        st.write('Temperature: ', hist_avg_tempmin, '°F to ', hist_avg_tempmax, '°F')
        st.write('Wind Speed: ', hist_avg_wndsp, 'm/s')
        st.write('Solar Radiation: ', hist_avg__srad, 'MJ/m^2')
    st.divider()
    show_button = st.checkbox('Show Slider Input Values')
    if show_button:
        st.write('Relative Humidity: ', rounded_RH1, '% to ', rounded_RH2, '%')
        st.write('Temperature: ', rounded_T1, '°F to ', rounded_T2, '°F')
        st.write('Wind Speed: ', rounded_WS, 'm/s')
        st.write('Solar Radiation: ', rounded_RS, 'MJ/m^2')