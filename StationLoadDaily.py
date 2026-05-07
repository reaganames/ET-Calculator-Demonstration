import pandas as pd
import datetime
import pyfao56
from pyfao56 import refet, Weather
import statistics
from statistics import mean
import math

class WeatherLoad:
    def __init__(self):
        self.params = {}
    def stationload(self, date, station):
        #Defining dataframe column names
        self.weather_list = ['Station','Date','Max Temp','Min Temp',
                             'RH Max','RH Min','Vapor Pressure',
                             'Liquid Precip','Wind Run','Solar Rad']
        # Define a dictionary to map station codes to their respective parameters
        self.station_params = {
            'GLY04': {'station': 'gly04', 'rfcrp': 'T', 'wndht': 2.000, 'z': 1427.378, 'lat': 40.4487, 'lon': -104.6380, 'stationstart': datetime.datetime(2008, 6, 5)},
            'ALT01': {'station': 'alt01', 'rfcrp': 'T', 'wndht': 2.000, 'z': 1496.568, 'lat': 40.5690, 'lon': -104.7200, 'stationstart': datetime.datetime(1992, 3, 17)},
            'LCN01': {'station': 'lcn01', 'rfcrp': 'T', 'wndht': 2.000, 'z': 1447.8, 'lat': 40.4756, 'lon': -104.7070, 'stationstart': datetime.datetime(1992, 3, 4)}
        }
        # Get the parameters for the specified station
        self.params = self.station_params.get(station)
        if self.params is None:
            raise ValueError(f"Invalid station code: {station}")
        
        self.station = self.params['station']
        self.startdate = self.params['stationstart']
        self.startdate_str = self.startdate.strftime('%Y-%m-%d')
        
        self.todaydate = date.strftime('%Y-%m-%d')
        self.yestdate = (date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        
        station_url = f'https://coagmet.colostate.edu/data/daily_raw/{self.station}.csv?header=yes&from={self.startdate_str}&to={self.yestdate}&units=m&fields=tMax,tMin,rhMax,rhMin,vp,precip,windRun,solarRad'
        station_df = pd.read_csv(station_url)
        station_df = station_df.iloc[1:]
        station_df.columns = self.weather_list
        dtypes = {'Date': 'datetime64',
                  'Max Temp': 'float64',
                  'Min Temp': 'float64',
                  'RH Max': 'float64',
                  'RH Min': 'float64',
                  'Vapor Pressure': 'float64',
                  'Liquid Precip': 'float64',
                  'Wind Run': 'float64',
                  'Solar Rad': 'float64'}
        station_df = station_df.astype(dtypes)
        
        #Filtering based on a single day and cutting down dataframe
        month = date.month
        day = date.day
        station_df = station_df[(station_df['Date'].dt.month == month) & (station_df['Date'].dt.day == day)]
        station_df['Date'] = station_df['Date'].dt.date

        #Converting Srad from (w/m2) to (MJ/m2-day)
        convert_srad = lambda X: X * 0.0864
        station_df['Solar Rad'] = station_df['Solar Rad'].apply(convert_srad)

        #Converting RH to percent
        convert_rh = lambda X: X * 100
        station_df['RH Max'] = station_df['RH Max'].apply(convert_rh)
        station_df['RH Min'] = station_df['RH Min'].apply(convert_rh)

        #Converting Wind Run from (km/day) to (m/s), finding average windspeed
        #First converting to (m) traveled
        convert_wr = lambda X: X * 1000
        station_df['Wind Run'] = station_df['Wind Run'].apply(convert_wr)
        #Finding average windspeed for the day (86400 seconds in a day)
        convert_wr2 = lambda X: X/86400
        station_df['Wind Speed'] = station_df['Wind Run'].apply(convert_wr2)

        #Dropping any NaN values or -999
        station_df = station_df[station_df != -999].dropna()

        #Dropping date and station column to be left with only the weather parameters
        station_df = station_df.drop(columns=['Date', 'Station'])

        #Averaging each date to end up with a single value for each parameter
        agg_values = station_df.agg(['mean'])
        print(agg_values)

        #Making lists out of dataframe columns that hold variable values
        self.solar_rad = agg_values['Solar Rad'].values[0]
        self.max_temp = agg_values['Max Temp'].values[0]
        self.min_temp = agg_values['Min Temp'].values[0]
        self.rh_max = agg_values['RH Max'].values[0]
        self.rh_min = agg_values['RH Min'].values[0]
        self.vp = agg_values['Vapor Pressure'].values[0]
        self.precip = agg_values['Liquid Precip'].values[0]
        self.wind_speed = agg_values['Wind Speed'].values[0]

        #Converting each to float and renaming to fit pyFAO56
        self.israd = float(self.solar_rad)
        self.tmax = float(self.max_temp)
        self.tmin = float(self.min_temp)
        self.rhmax = float(self.rh_max)
        self.rhmin = float(self.rh_min)
        self.vapr = float(self.vp)
        self.precip = float(self.precip)
        self.wndsp = float(self.wind_speed)
        

        #Defining doy 
        self.doy = date.strftime('%j')
        self.doy = int(self.doy)

        return self.wndsp, self.tmax, self.tmin, self.rhmax, self.rhmin
    def rso_calc(self):
        #Finding clear sky solar radiation (MJ/m^-2 day^-1)
        #First, finding extraterrestrial radiation (ra) (MJ/m^-2 day^-1)
        latrad = self.params.get('lat', None)
        if latrad is None:
            raise ValueError("Latitude not found for station")
        latrad = self.params['lat']*math.pi/180.0
        dr = 1.0+0.033*math.cos(2.0*math.pi/365.0*self.doy)
        ldelta = 0.409*math.sin(2.0*math.pi/365.0*self.doy-1.39)
        ws = math.acos(-1.0*math.tan(latrad)*math.tan(ldelta))
        ra1 = ws*math.sin(latrad)*math.sin(ldelta)
        ra2 = math.cos(latrad)*math.cos(ldelta)*math.sin(ws)
        ra = 24.0/math.pi*4.92*dr*(ra1+ra2)
        print('The extraterrestrial radiation is (MJ/m^-2 day^-1): ', ra)
        #Then, finding clear sky solar radiation (rs) (MJ/m^-2 day^-1)
        self.rso = (0.75+2e-5*self.params['z'])*ra
        print('The clear sky solar radiation is (MJ/m^-2 day^-1): ', self.rso)
        return self.rso
    
    
    def ascedaily(self, rfcrp, z, lat, doy, israd, tmax, tmin, rhmax, rhmin, wndsp, wndht):
        #tavg (float) : Mean daily air temperature (deg C)
        #ASCE (2005) Eq. 2
        tavg = (tmax+tmin)/2.0

        #patm (float) : Mean atmospheric pressure at weather station (kPa)
        #ASCE (2005) Eq. 3
        patm = 101.3*((293.0-0.0065*z)/293.0)**5.26

        #psycon (float) : Psychrometric constant (kPa (deg C)^-1)
        #ASCE (2005) Eq. 4
        psycon = 0.000665*patm

        #Udelta (float) : Slope of the saturation vapor pressure
        #temperature curve (kPa (deg C)^-1)
        #ASCE (2005) Eq. 5
        Udelta = 2503.0*math.exp(17.27*tavg/(tavg+237.3))
        Udelta = Udelta/((tavg+237.3)**2.0)

        #es (float) : Saturation vapor pressure (kPa)
        #ASCE (2005) Eqs. 6 and 7
        emax = 0.6108*math.exp((17.27*tmax)/(tmax+237.3))
        emin = 0.6108*math.exp((17.27*tmin)/(tmin+237.3))
        es = (emax+emin)/2.0

        #ea (float): Actual vapor pressure (kPa) ASCE (2005) Table 3
        if not math.isnan(rhmax) and not math.isnan(rhmin):
            #ASCE (2005) Eq. 11
            ea = (emin*rhmax/100. + emax*rhmin/100.)/2.0
        elif not math.isnan(rhmax):
            #ASCE (2005) Eq. 12
            ea = emin*rhmax/100.
        elif not math.isnan(rhmin):
            #ASCE (2005) Eq. 13
            ea = emax*rhmin/100.
        else:
            #ASCE (2005) Appendix E
            tdew = tmin - 2.0
            ea = 0.6108*math.exp((17.27*tdew)/(tdew+237.3))

        #rns (float) : Net shortwave radiation (MJ m^-2 d^-1)
        #ASCE (2005) Eq. 16
        albedo = 0.23
        rns = (1.0-albedo)*israd

        #ra (float) : Extraterrestrial radiation (MJ m^-2 d^-1)
        #ASCE (2005) Eqs. 21-27
        latrad = lat*math.pi/180.0 #Eq. 22
        dr = 1.0+0.033*math.cos(2.0*math.pi/365.0*doy) #Eq. 23
        ldelta = 0.409*math.sin(2.0*math.pi/365.0*doy-1.39) #Eq. 24
        ws = math.acos(-1.0*math.tan(latrad)*math.tan(ldelta)) #Eq. 27
        ra1 = ws*math.sin(latrad)*math.sin(ldelta) #Eq. 21
        ra2 = math.cos(latrad)*math.cos(ldelta)*math.sin(ws) #Eq. 21
        ra = 24.0/math.pi*4.92*dr*(ra1+ra2) #Eq. 21

        #rso (float) : Clear sky solar radiation (MJ m^-2 d^-1)
        #ASCE (2005) Eq. 19
        rso = (0.75+2e-5*z)*ra

        #rnl (float) : Net longwave radiation (MJ m^-2 d^-1)
        #ASCE (2005) Eqs. 17 and 18
        ratio = sorted([0.3,israd/rso,1.0])[1]
        fcd = sorted([0.05,1.35*ratio-0.35,1.0])[1] #Eq. 18
        tk4 = ((tmax+273.16)**4.0+(tmin+273.16)**4.0)/2.0 #Eq. 17
        rnl = 4.901e-9*fcd*(0.34-0.14*math.sqrt(ea))*tk4 #Eq. 17

        #rn (float) : Net radiation (MJ m^-2 d^-1)
        #ASCE (2005) Eq. 15
        rn = rns-rnl

        #g (float) : Soil heat flux (MJ m^-2 d^-1)
        #ASCE (2005) Eq. 30
        g = 0.0

        #u2 (float) : Wind profile relationship (m s^-1)
        #ASCE (2005) Eq. 33 and Appendix E
        if math.isnan(wndsp): wndsp = 2.0
        u2 = wndsp * (4.87/math.log(67.8*wndht-5.42))

        #Aerodynamic roughness and surface resistance constants
        #ASCE (2005) Table 1
        if rfcrp == 'S': #Short reference crop (0.12-m grass)
            Cn = 900.0  #K mm s^3 Mg^-1 d^-1
            Cd = 0.34   #s m^-1
        elif rfcrp == 'T': #Tall reference crop (0.50-m alfalfa)
            Cn = 1600.0 #K mm s^3 Mg^-1 d^-1
            Cd = 0.38   #s m^-1

        #etsz (float) : Standardized daily reference crop ET (mm d^-1)
        #ASCE (2005) Eq. 1
        etsz = 0.408*Udelta*(rn-g)+psycon*(Cn/(tavg+273.0))*u2*(es-ea)
        etsz = etsz/(Udelta+psycon*(1.0+Cd*u2))

        return etsz