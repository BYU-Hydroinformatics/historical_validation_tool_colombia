####################################################################################################
##                                   LIBRARIES AND DEPENDENCIES                                   ##
####################################################################################################

# Tethys platform
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponse
from tethys_sdk.routing import controller
from tethys_sdk.gizmos import PlotlyView, DatePicker

# Postgresql
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
from pandas_geojson import to_geojson

# Geoglows
import io
import math
import geoglows
import requests
import numpy as np
import HydroErr as he
import datetime as dt
import hydrostats as hs
import hydrostats.data as hd
import plotly.graph_objs as go


# Base
import os
from dotenv import load_dotenv

####################################################################################################
##                                       STATUS VARIABLES                                         ##
####################################################################################################


# Import enviromental variables
load_dotenv()
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')


# Generate the conection token
global tokencon
tokencon = "postgresql+psycopg2://{0}:{1}@localhost:5432/{2}".format(DB_USER, DB_PASS, DB_NAME)



####################################################################################################
##                                 UTILS AND AUXILIAR FUNCTIONS                                   ##
####################################################################################################

def get_format_data(sql_statement, conn):
    # Retrieve data from database
    data =  pd.read_sql(sql_statement, conn)
    # Datetime column as dataframe index
    data.index = data.datetime
    data = data.drop(columns=['datetime'])
    # Format the index values
    data.index = pd.to_datetime(data.index)
    data.index = data.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
    data.index = pd.to_datetime(data.index)
    # Return result
    return(data)


def get_bias_corrected_data(sim, obs):
    outdf = geoglows.bias.correct_historical(sim, obs)
    outdf.index = pd.to_datetime(outdf.index)
    outdf.index = outdf.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
    outdf.index = pd.to_datetime(outdf.index)
    return(outdf)


def gumbel_1(std: float, xbar: float, rp: int or float) -> float:
  return -math.log(-math.log(1 - (1 / rp))) * std * .7797 + xbar - (.45 * std)


def get_return_periods(comid, data):
    # Stats
    max_annual_flow = data.groupby(data.index.strftime("%Y")).max()
    mean_value = np.mean(max_annual_flow.iloc[:,0].values)
    std_value = np.std(max_annual_flow.iloc[:,0].values)
    # Return periods
    return_periods = [100, 50, 25, 10, 5, 2]
    return_periods_values = []
    # Compute the corrected return periods
    for rp in return_periods:
      return_periods_values.append(gumbel_1(std_value, mean_value, rp))
    # Parse to list
    d = {'rivid': [comid], 
         'return_period_100': [return_periods_values[0]], 
         'return_period_50': [return_periods_values[1]], 
         'return_period_25': [return_periods_values[2]], 
         'return_period_10': [return_periods_values[3]], 
         'return_period_5': [return_periods_values[4]], 
         'return_period_2': [return_periods_values[5]]}
    # Parse to dataframe
    corrected_rperiods_df = pd.DataFrame(data=d)
    corrected_rperiods_df.set_index('rivid', inplace=True)
    return(corrected_rperiods_df)


def ensemble_quantile(ensemble, quantile, label):
    df = ensemble.quantile(quantile, axis=1).to_frame()
    df.rename(columns = {quantile: label}, inplace = True)
    return(df)


def get_ensemble_stats(ensemble):
    high_res_df = ensemble['ensemble_52_m^3/s'].to_frame()
    ensemble.drop(columns=['ensemble_52_m^3/s'], inplace=True)
    ensemble.dropna(inplace= True)
    high_res_df.dropna(inplace= True)
    high_res_df.rename(columns = {'ensemble_52_m^3/s':'high_res_m^3/s'}, inplace = True)
    stats_df = pd.concat([
        ensemble_quantile(ensemble, 1.00, 'flow_max_m^3/s'),
        ensemble_quantile(ensemble, 0.75, 'flow_75%_m^3/s'),
        ensemble_quantile(ensemble, 0.50, 'flow_avg_m^3/s'),
        ensemble_quantile(ensemble, 0.25, 'flow_25%_m^3/s'),
        ensemble_quantile(ensemble, 0.00, 'flow_min_m^3/s'),
        high_res_df
    ], axis=1)
    return(stats_df)


def __bias_correction_forecast__(sim_hist, fore_nofix, obs_hist):
    '''Correct Bias Forecasts'''

    # Selection of monthly simulated data
    monthly_simulated = sim_hist[sim_hist.index.month == (fore_nofix.index[0]).month].dropna()

    # Obtain Min and max value
    min_simulated = monthly_simulated.min().values[0]
    max_simulated = monthly_simulated.max().values[0]

    min_factor_df   = fore_nofix.copy()
    max_factor_df   = fore_nofix.copy()
    forecast_ens_df = fore_nofix.copy()

    for column in fore_nofix.columns:
        # Min Factor
        tmp_array = np.ones(fore_nofix[column].shape[0])
        tmp_array[fore_nofix[column] < min_simulated] = 0
        min_factor = np.where(tmp_array == 0, fore_nofix[column] / min_simulated, tmp_array)

        # Max factor
        tmp_array = np.ones(fore_nofix[column].shape[0])
        tmp_array[fore_nofix[column] > max_simulated] = 0
        max_factor = np.where(tmp_array == 0, fore_nofix[column] / max_simulated, tmp_array)

        # Replace
        tmp_fore_nofix = fore_nofix[column].copy()
        tmp_fore_nofix.mask(tmp_fore_nofix <= min_simulated, min_simulated, inplace=True)
        tmp_fore_nofix.mask(tmp_fore_nofix >= max_simulated, max_simulated, inplace=True)

        # Save data
        forecast_ens_df.update(pd.DataFrame(tmp_fore_nofix, index=fore_nofix.index, columns=[column]))
        min_factor_df.update(pd.DataFrame(min_factor, index=fore_nofix.index, columns=[column]))
        max_factor_df.update(pd.DataFrame(max_factor, index=fore_nofix.index, columns=[column]))

    # Get  Bias Correction
    corrected_ensembles = geoglows.bias.correct_forecast(forecast_ens_df, sim_hist, obs_hist)
    corrected_ensembles = corrected_ensembles.multiply(min_factor_df, axis=0)
    corrected_ensembles = corrected_ensembles.multiply(max_factor_df, axis=0)

    return corrected_ensembles


def get_corrected_forecast_records(records_df, simulated_df, observed_df):
    ''' Este es el comentario de la doc '''
    date_ini = records_df.index[0]
    month_ini = date_ini.month
    date_end = records_df.index[-1]
    month_end = date_end.month
    meses = np.arange(month_ini, month_end + 1, 1)
    fixed_records = pd.DataFrame()
    for mes in meses:
        values = records_df.loc[records_df.index.month == mes]
        monthly_simulated = simulated_df[simulated_df.index.month == mes].dropna()
        monthly_observed = observed_df[observed_df.index.month == mes].dropna()
        min_simulated = np.min(monthly_simulated.iloc[:, 0].to_list())
        max_simulated = np.max(monthly_simulated.iloc[:, 0].to_list())
        min_factor_records_df = values.copy()
        max_factor_records_df = values.copy()
        fixed_records_df = values.copy()
        column_records = values.columns[0]
        tmp = records_df[column_records].dropna().to_frame()
        min_factor = tmp.copy()
        max_factor = tmp.copy()
        min_factor.loc[min_factor[column_records] >= min_simulated, column_records] = 1
        min_index_value = min_factor[min_factor[column_records] != 1].index.tolist()
        for element in min_index_value:
            min_factor[column_records].loc[min_factor.index == element] = tmp[column_records].loc[tmp.index == element] / min_simulated
        max_factor.loc[max_factor[column_records] <= max_simulated, column_records] = 1
        max_index_value = max_factor[max_factor[column_records] != 1].index.tolist()
        for element in max_index_value:
            max_factor[column_records].loc[max_factor.index == element] = tmp[column_records].loc[tmp.index == element] / max_simulated
        tmp.loc[tmp[column_records] <= min_simulated, column_records] = min_simulated
        tmp.loc[tmp[column_records] >= max_simulated, column_records] = max_simulated
        fixed_records_df.update(pd.DataFrame(tmp[column_records].values, index=tmp.index, columns=[column_records]))
        min_factor_records_df.update(pd.DataFrame(min_factor[column_records].values, index=min_factor.index, columns=[column_records]))
        max_factor_records_df.update(pd.DataFrame(max_factor[column_records].values, index=max_factor.index, columns=[column_records]))
        corrected_values = geoglows.bias.correct_forecast(fixed_records_df, simulated_df, observed_df)
        corrected_values = corrected_values.multiply(min_factor_records_df, axis=0)
        corrected_values = corrected_values.multiply(max_factor_records_df, axis=0)
    
        fixed_records = fixed_records.append(corrected_values)

    fixed_records.sort_index(inplace=True)
    return(fixed_records)


def get_forecast_date(comid, date):
    url = 'https://geoglows.ecmwf.int/api/ForecastEnsembles/?reach_id={0}&date={1}&return_format=csv'.format(comid, date)
    status = False
    while not status:
      try:
        outdf = pd.read_csv(url, index_col=0)
        status = True
      except:
        print("Trying to retrieve data...")
    # Filter and correct data
    outdf[outdf < 0] = 0
    outdf.index = pd.to_datetime(outdf.index)
    outdf.index = outdf.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
    outdf.index = pd.to_datetime(outdf.index)
    return(outdf)


def get_forecast_record_date(comid, date):
    idate = dt.datetime.strptime(date, '%Y%m%d') - dt.timedelta(days=10)
    idate = idate.strftime('%Y%m%d')
    url = 'https://geoglows.ecmwf.int/api/ForecastRecords/?reach_id={0}&start_date={1}&end_date={2}&return_format=csv'.format(comid, idate, date)
    status = False
    while not status:
      try:
        outdf = pd.read_csv(url, index_col=0)
        status = True
      except:
        print("Trying to retrieve data...")
    # Filter and correct data
    outdf[outdf < 0] = 0
    outdf.index = pd.to_datetime(outdf.index)
    outdf.index = outdf.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
    outdf.index = pd.to_datetime(outdf.index)
    return(outdf)


def get_fews_data(station_code):
    # TODO : Change with fews postgres implementation
    url = 'http://fews.ideam.gov.co/colombia/jsonQ/00' + station_code + 'Qobs.json'
    try:
        # Call data
        f = requests.get(url, verify=False)
        data = f.json()
        
        # Extract data
        observedDischarge = (data.get('obs'))
        sensorDischarge = (data.get('sen'))
        observedDischarge = (observedDischarge.get('data'))
        sensorDischarge = (sensorDischarge.get('data'))
        datesObservedDischarge = [row[0] for row in observedDischarge]
        observedDischarge = [row[1] for row in observedDischarge]
        datesSensorDischarge = [row[0] for row in sensorDischarge]
        sensorDischarge = [row[1] for row in sensorDischarge]

        # Build dataframe discharge
        observedDischarge_df = pd.DataFrame(data={'date' : datesObservedDischarge,
                                                'streamflow m3/s' : observedDischarge})
        observedDischarge_df['date'] = pd.to_datetime(observedDischarge_df['date'], format='%Y/%m/%d %H:%M')
        observedDischarge_df['streamflow m3/s'] = observedDischarge_df['streamflow m3/s'].astype(float)
        observedDischarge_df.dropna(inplace=True)
        observedDischarge_df.set_index('date', inplace = True)
        
        # Build dataframe sensor
        sensorDischarge_df   = pd.DataFrame(data={'date' : datesSensorDischarge,
                                                'streamflow m3/s' : sensorDischarge})
        sensorDischarge_df['date'] = pd.to_datetime(sensorDischarge_df['date'], format='%Y/%m/%d %H:%M')
        sensorDischarge_df['streamflow m3/s'] = sensorDischarge_df['streamflow m3/s'].astype(float)
        sensorDischarge_df.dropna(inplace=True)
        sensorDischarge_df.set_index('date', inplace=True)

    except:
        # Build discharge dataframe
        observedDischarge_df = pd.DataFrame(data = {'date' : [pd.NaT],
                                                  'streamflow m3/s' : [np.nan]})
        observedDischarge_df.set_index('date', inplace = True)

        # Build sensor dataframe
        sensorDischarge_df = pd.DataFrame(data = {'date' : [pd.NaT],
                                                  'streamflow m3/s' : [np.nan]})
        sensorDischarge_df.set_index('date', inplace=True)

    return observedDischarge_df, sensorDischarge_df


####################################################################################################
##                                      PLOTTING FUNCTIONS                                        ##
####################################################################################################

# Plotting daily averages values
def get_daily_average_plot(merged_sim, merged_cor, code, name):
    # Generate the average values
    daily_avg_sim = hd.daily_average(merged_sim)
    daily_avg_cor = hd.daily_average(merged_cor)
    # Generate the plots on Ploty
    daily_avg_obs_Q = go.Scatter(x = daily_avg_sim.index, y = daily_avg_sim.iloc[:, 1].values, name = 'Observed', )
    daily_avg_sim_Q = go.Scatter(x = daily_avg_sim.index, y = daily_avg_sim.iloc[:, 0].values, name = 'Simulated', )
    daily_avg_corr_sim_Q = go.Scatter(x = daily_avg_cor.index, y = daily_avg_cor.iloc[:, 0].values, name = 'Corrected Simulated', )
    # PLot Layout
    layout = go.Layout(
        title='Daily Average Streamflow for <br> {0} - {1}'.format(code.upper(), name),
        xaxis=dict(title='Days', ), 
        yaxis=dict(title='Discharge (m<sup>3</sup>/s)', autorange=True),
        showlegend=True)
    # Generate the output
    chart_obj = go.Figure(data=[daily_avg_obs_Q, daily_avg_sim_Q, daily_avg_corr_sim_Q], layout=layout)
    return(chart_obj)


# Plotting monthly averages values
def get_monthly_average_plot(merged_sim, merged_cor, code, name):
    # Generate the average values
    daily_avg_sim = hd.monthly_average(merged_sim)
    daily_avg_cor = hd.monthly_average(merged_cor)
    # Generate the plots on Ploty
    daily_avg_obs_Q = go.Scatter(x = daily_avg_sim.index, y = daily_avg_sim.iloc[:, 1].values, name = 'Observed', )
    daily_avg_sim_Q = go.Scatter(x = daily_avg_sim.index, y = daily_avg_sim.iloc[:, 0].values, name = 'Simulated', )
    daily_avg_corr_sim_Q = go.Scatter(x = daily_avg_cor.index, y = daily_avg_cor.iloc[:, 0].values, name = 'Corrected Simulated', )
    # PLot Layout
    layout = go.Layout(
        title='Monthly Average Streamflow for <br> {0} - {1}'.format(code.upper(), name),
        xaxis=dict(title='Months', ), 
        yaxis=dict(title='Discharge (m<sup>3</sup>/s)', autorange=True),
        showlegend=True)
    # Generate the output
    chart_obj = go.Figure(data=[daily_avg_obs_Q, daily_avg_sim_Q, daily_avg_corr_sim_Q], layout=layout)
    return(chart_obj)


# Scatter plot (Simulated/Corrected vs Observed)
def get_scatter_plot(merged_sim, merged_cor, code, name, log):
    # Generate Scatter (sim vs obs)
    scatter_data = go.Scatter(
        x = merged_sim.iloc[:, 0].values,
        y = merged_sim.iloc[:, 1].values,
        mode='markers',
        name='original',
        marker=dict(color='#ef553b'))
    # Generate Scatter (cor vs obs)
    scatter_data2 = go.Scatter(
        x = merged_cor.iloc[:, 0].values,
        y = merged_cor.iloc[:, 1].values,
        mode='markers',
        name='corrected',
        marker=dict(color='#00cc96'))
    # Get the max and min values
    min_value = min(min(merged_sim.iloc[:, 1].values), min(merged_sim.iloc[:, 0].values))
    max_value = max(max(merged_sim.iloc[:, 1].values), max(merged_sim.iloc[:, 0].values))
    # Construct the line 1:1
    line_45 = go.Scatter(
        x = [min_value, max_value],
        y = [min_value, max_value],
        mode = 'lines',
        name = '45deg line',
        line = dict(color='black'))
    # Plot Layout
    if log == True:
        layout = go.Layout(title = "Scatter Plot (Log Scale) <br> {0} - {1}".format(code.upper(), name),
                       xaxis = dict(title = 'Simulated Discharge (m<sup>3</sup>/s)', type = 'log', ), 
                       yaxis = dict(title = 'Observed Discharge (m<sup>3</sup>/s)', type = 'log', autorange = True), 
                       showlegend=True)
    else:
        layout = go.Layout(title = "Scatter Plot <br> {0} - {1}".format(code.upper(), name),
                       xaxis = dict(title = 'Simulated Discharge (m<sup>3</sup>/s)',  ), 
                       yaxis = dict(title = 'Observed Discharge (m<sup>3</sup>/s)', autorange = True), 
                       showlegend=True)
    # Plotting data
    chart_obj = go.Figure(data=[scatter_data, scatter_data2, line_45], layout=layout)
    return(chart_obj)


# Acumulate volume
def get_acumulated_volume_plot(merged_sim, merged_cor, code, name):
    # Parse dataframe to array
    sim_array = merged_sim.iloc[:, 0].values * 0.0864
    obs_array = merged_sim.iloc[:, 1].values * 0.0864
    cor_array = merged_cor.iloc[:, 0].values * 0.0864
    # Convert from m3/s to Hm3
    sim_volume = sim_array.cumsum()
    obs_volume = obs_array.cumsum()
    cor_volume = cor_array.cumsum()
    # Generate plots
    observed_volume  = go.Scatter(x = merged_sim.index, y = obs_volume, name='Observed', )
    simulated_volume = go.Scatter(x = merged_sim.index, y = sim_volume, name='Simulated', )
    corrected_volume = go.Scatter(x = merged_cor.index, y = cor_volume, name='Corrected Simulated', )
    # Plot layouts
    layout = go.Layout(
                title='Observed & Simulated Volume at<br> {0} - {1}'.format(code.upper(), name),
                xaxis=dict(title='Dates', ), 
                yaxis=dict(title='Volume (Mm<sup>3</sup>)', autorange=True),
                showlegend=True)
    # Integrating the plots
    chart_obj = go.Figure(data=[observed_volume, simulated_volume, corrected_volume], layout=layout)
    return(chart_obj)


# Metrics table
def get_metrics_table(merged_sim, merged_cor, my_metrics):
    # Metrics for simulated data
    table_sim = hs.make_table(merged_sim, my_metrics)
    table_sim = table_sim.rename(index={'Full Time Series': 'Simulated Serie'})
    table_sim = table_sim.transpose()
    # Metrics for corrected simulation data
    table_cor = hs.make_table(merged_cor, my_metrics)
    table_cor = table_cor.rename(index={'Full Time Series': 'Corrected Serie'})
    table_cor = table_cor.transpose()
    # Merging data
    table_final = pd.merge(table_sim, table_cor, right_index=True, left_index=True)
    table_final = table_final.round(decimals=2)
    table_final = table_final.to_html(classes="table table-hover table-striped", table_id="corrected_1")
    table_final = table_final.replace('border="1"', 'border="0"').replace('<tr style="text-align: right;">','<tr style="text-align: left;">')
    return(table_final)


# Forecast plot
def get_forecast_plot(comid, site, stats, rperiods, records, obs_data):

    corrected_stats_df = stats
    corrected_rperiods_df = rperiods
    fixed_records = records
    
    ## Build image
    hydroviewer_figure = geoglows.plots.forecast_stats(stats=corrected_stats_df, titles={'Site': site, 'Reach ID': comid, 'bias_corrected': True})
    x_vals = (corrected_stats_df.index[0], corrected_stats_df.index[len(corrected_stats_df.index) - 1],
              corrected_stats_df.index[len(corrected_stats_df.index) - 1], corrected_stats_df.index[0])
    max_visible = max(corrected_stats_df.max())
    
    ## Bias correction
    corrected_records_plot = fixed_records.loc[fixed_records.index >= pd.to_datetime(corrected_stats_df.index[0] - dt.timedelta(days=8))]
    corrected_records_plot = corrected_records_plot.loc[corrected_records_plot.index <= pd.to_datetime(corrected_stats_df.index[0] + dt.timedelta(days=2))]
    
    ##
    if len(corrected_records_plot.index) > 0:
      hydroviewer_figure.add_trace(go.Scatter(
          name='1st days forecasts',
          x=corrected_records_plot.index,
          y=corrected_records_plot.iloc[:, 0].values,
          line=dict(color='#FFA15A',)
      ))
      x_vals = (corrected_records_plot.index[0], corrected_stats_df.index[len(corrected_stats_df.index) - 1], corrected_stats_df.index[len(corrected_stats_df.index) - 1], corrected_records_plot.index[0])
      max_visible = max(max(corrected_records_plot.max()), max_visible)
    
    ## Getting Return Periods
    r2 = int(corrected_rperiods_df.iloc[0]['return_period_2'])

    ## Colors
    colors = {
        '2 Year': 'rgba(254, 240, 1, .4)',
        '5 Year': 'rgba(253, 154, 1, .4)',
        '10 Year': 'rgba(255, 56, 5, .4)',
        '20 Year': 'rgba(128, 0, 246, .4)',
        '25 Year': 'rgba(255, 0, 0, .4)',
        '50 Year': 'rgba(128, 0, 106, .4)',
        '100 Year': 'rgba(128, 0, 246, .4)',
    }
    
    ##
    if max_visible > r2:
      visible = True
      hydroviewer_figure.for_each_trace(lambda trace: trace.update(visible=True) if trace.name == "Maximum & Minimum Flow" else (), )
    else:
      visible = 'legendonly'
      hydroviewer_figure.for_each_trace(lambda trace: trace.update(visible=True) if trace.name == "Maximum & Minimum Flow" else (), )
    
    ##
    def template(name, y, color, fill='toself'):
      return go.Scatter(
          name=name,
          x=x_vals,
          y=y,
          legendgroup='returnperiods',
          fill=fill,
          visible=visible,
          line=dict(color=color, width=0))
    
    ## Get return periods
    r5 = int(corrected_rperiods_df.iloc[0]['return_period_5'])
    r10 = int(corrected_rperiods_df.iloc[0]['return_period_10'])
    r25 = int(corrected_rperiods_df.iloc[0]['return_period_25'])
    r50 = int(corrected_rperiods_df.iloc[0]['return_period_50'])
    r100 = int(corrected_rperiods_df.iloc[0]['return_period_100'])

    ## Return periods plot
    hydroviewer_figure.add_trace(template('Return Periods', (r100 * 0.05, r100 * 0.05, r100 * 0.05, r100 * 0.05), 'rgba(0,0,0,0)', fill='none'))
    hydroviewer_figure.add_trace(template(f'2 Year: {r2}', (r2, r2, r5, r5), colors['2 Year']))
    hydroviewer_figure.add_trace(template(f'5 Year: {r5}', (r5, r5, r10, r10), colors['5 Year']))
    hydroviewer_figure.add_trace(template(f'10 Year: {r10}', (r10, r10, r25, r25), colors['10 Year']))
    hydroviewer_figure.add_trace(template(f'25 Year: {r25}', (r25, r25, r50, r50), colors['25 Year']))
    hydroviewer_figure.add_trace(template(f'50 Year: {r50}', (r50, r50, r100, r100), colors['50 Year']))
    hydroviewer_figure.add_trace(template(f'100 Year: {r100}', (r100, r100, max(r100 + r100 * 0.05, max_visible), max(r100 + r100 * 0.05, max_visible)), colors['100 Year']))
    
    ## Fix axis in obs data for plot
    obs_data['fix_data'] = [data_i[data_i.index > corrected_records_plot.index[0]] for data_i in obs_data['data']]

    # Add observed data
    for num, data in enumerate(obs_data['fix_data']):
        hydroviewer_figure.add_trace(go.Scatter(
                                        name = obs_data['name'][num],
                                        x    = data.index,
                                        y    = data.iloc[:, 0].values,
                                        line = dict(color=obs_data['color'][num])
                                    ))

    ##
    hydroviewer_figure['layout']['xaxis'].update(autorange=True)
    
    return hydroviewer_figure


####################################################################################################
##                                   CONTROLLERS AND REST APIs                                    ##
#################################################################################################### 

# Initialize the web app
@controller(name='home',url='historical-validation-tool-colombia')
def home(request):
    context = {}
    return render(request, 'historical_validation_tool_colombia/home.html', context)


# Return streamflow stations in geojson format 
@controller(name='get_stations',
            url='historical-validation-tool-colombia/get-stations')
def get_stations(request):
    # Establish connection to database
    db= create_engine(tokencon)
    conn = db.connect()
    # Query to database
    # stations = pd.read_sql("select *, concat(code, ' - ', left(name, 23)) from streamflow_station", conn);
    try:
        stations = pd.read_sql("select * , concat(codigo, ' - ', left(name, 23)) from stations_streamflow", conn)
    finally:
        conn.close()

    stations.rename(columns={"zona_hidrografica" : "basin",
                             "codigo" : "code", 
                             "name" : "name", 
                             "latitude" : "latitude", 
                             "longitude" : "longitude", 
                             "altitud" : "elevation", 
                             "comid" : "comid",
                             "stream_nam" : "river", 
                             "area_operativa" : "loc1",
                             "area_hidrografica" : "loc2",
                             "departamento" : "loc3",
                             "alert" : "alert", 
                             }, inplace=True)
    stations = stations.astype({col : 'str' for col in stations.columns})
    stations = stations.astype({"latitude"  : 'float',
                                "longitude" : 'float'})

    stations = to_geojson(
        df = stations,
        lat = "latitude",
        lon = "longitude",
        properties = ["basin", "code", "name", "latitude", "longitude", "elevation", "comid", "river", 
                      "loc1", "loc2", "loc3", "alert", "concat"]
    )
    return JsonResponse(stations)



# Return streamflow station (in geojson format) 
@controller(name='get_data',
            url='historical-validation-tool-colombia/get-data')
def get_data(request):
    
    # Retrieving GET arguments
    station_code = request.GET['codigo']
    station_comid = request.GET['comid']
    station_name = request.GET['nombre']
    plot_width = float(request.GET['width']) - 12
    plot_width_2 = 0.5*plot_width


    # Establish connection to database
    db = create_engine(tokencon)
    conn = db.connect()
    try:
        # Data series
        observed_data = get_format_data("select datetime, s_{0} from observed_streamflow_data order by datetime;".format(station_code), conn)
        simulated_data = get_format_data("select * from hs_{0};".format(station_comid), conn)
        # TODO : remove whwere geoglows server works
        simulated_data = simulated_data[simulated_data.index < '2022-06-01'].copy()
        corrected_data = get_bias_corrected_data(simulated_data, observed_data)

        # Raw forecast
        ensemble_forecast = get_format_data("select * from f_{0};".format(station_comid), conn)
        forecast_records = get_format_data("select * from fr_{0};".format(station_comid), conn)
    finally:
        # Close conection
        conn.close()

    return_periods = get_return_periods(station_comid, simulated_data)

    # Corrected forecast
    # corrected_ensemble_forecast = get_corrected_forecast(simulated_data, ensemble_forecast, observed_data)
    corrected_ensemble_forecast = __bias_correction_forecast__(simulated_data, ensemble_forecast, observed_data)
    corrected_forecast_records = get_corrected_forecast_records(forecast_records, simulated_data, observed_data)
    corrected_return_periods = get_return_periods(station_comid, corrected_data)
    
    # FEWS data
    obs_fews, sen_fews = get_fews_data(station_code)

    # Stats for raw and corrected forecast
    ensemble_stats = get_ensemble_stats(ensemble_forecast)
    corrected_ensemble_stats = get_ensemble_stats(corrected_ensemble_forecast)


    # Merge data (For plots)
    global merged_sim
    merged_sim = hd.merge_data(sim_df = simulated_data, obs_df = observed_data)
    global merged_cor
    merged_cor = hd.merge_data(sim_df = corrected_data, obs_df = observed_data)


    # Historical data plot
    corrected_data_plot = geoglows.plots.corrected_historical(
                                simulated = simulated_data,
                                corrected = corrected_data,
                                observed = observed_data, 
                                outformat = "plotly", 
                                titles = {'Site': station_name, 'Reach COMID': station_comid})
    # Daily averages plot
    daily_average_plot = get_daily_average_plot(
                                merged_cor = merged_cor,
                                merged_sim = merged_sim,
                                code = station_code,
                                name = station_name)   
    # Monthly averages plot
    monthly_average_plot = get_monthly_average_plot(
                                merged_cor = merged_cor,
                                merged_sim = merged_sim,
                                code = station_code,
                                name = station_name) 
    # Scatter plot
    data_scatter_plot = get_scatter_plot(
                                merged_cor = merged_cor,
                                merged_sim = merged_sim,
                                code = station_code,
                                name = station_name,
                                log = False) 
    # Scatter plot (Log scale)
    log_data_scatter_plot = get_scatter_plot(
                                merged_cor = merged_cor,
                                merged_sim = merged_sim,
                                code = station_code,
                                name = station_name,
                                log = True) 
    # Acumulated volume plot
    acumulated_volume_plot = get_acumulated_volume_plot(
                                merged_cor = merged_cor,
                                merged_sim = merged_sim,
                                code = station_code,
                                name = station_name)
    
    # Metrics table
    metrics_table = get_metrics_table(
                                merged_cor = merged_cor,
                                merged_sim = merged_sim,
                                my_metrics = ["ME", "RMSE", "NRMSE (Mean)", "NSE", "KGE (2009)", "KGE (2012)", "R (Pearson)", "R (Spearman)", "r2"]) 
    
    # Percent of Ensembles that Exceed Return Periods
    forecast_table = geoglows.plots.probabilities_table(
                                stats = ensemble_stats,
                                ensem = ensemble_forecast, 
                                rperiods = return_periods)
    
    corrected_forecast_table = geoglows.plots.probabilities_table(
                                stats = corrected_ensemble_stats,
                                ensem = corrected_ensemble_forecast, 
                                rperiods = corrected_return_periods)


    # obs_fews, sen_fews
    # Ensemble forecast plot
    ensemble_forecast_plot = get_forecast_plot(
                                comid = station_comid, 
                                site = station_name, 
                                stats = ensemble_stats, 
                                rperiods = return_periods, 
                                records = forecast_records,
                                obs_data = {'data'  : [obs_fews, sen_fews],
                                            'color' : ['blue', 'red'],
                                            'name'  : ['Caudal observado', 'Caudal sensor']})
    
    corrected_ensemble_forecast_plot = get_forecast_plot(
                                            comid = station_comid, 
                                            site = station_name, 
                                            stats = corrected_ensemble_stats, 
                                            rperiods = corrected_return_periods, 
                                            records = corrected_forecast_records,
                                            obs_data = {'data'  : [obs_fews, sen_fews],
                                                        'color' : ['blue', 'red'],
                                                        'name'  : ['Caudal observado', 'Caudal sensor']})
    

    #returning
    context = {
        "corrected_data_plot": PlotlyView(corrected_data_plot.update_layout(width = plot_width)),
        "daily_average_plot": PlotlyView(daily_average_plot.update_layout(width = plot_width)),
        "monthly_average_plot": PlotlyView(monthly_average_plot.update_layout(width = plot_width)),
        "data_scatter_plot": PlotlyView(data_scatter_plot.update_layout(width = plot_width_2)),
        "log_data_scatter_plot": PlotlyView(log_data_scatter_plot.update_layout(width = plot_width_2)),
        "acumulated_volume_plot": PlotlyView(acumulated_volume_plot.update_layout(width = plot_width)),
        "ensemble_forecast_plot": PlotlyView(ensemble_forecast_plot.update_layout(width = plot_width)),
        "corrected_ensemble_forecast_plot": PlotlyView(corrected_ensemble_forecast_plot.update_layout(width = plot_width)),
        "metrics_table": metrics_table,
        "forecast_table": forecast_table,
        "corrected_forecast_table": corrected_forecast_table,
    }
    return render(request, 'historical_validation_tool_colombia/panel.html', context)



@controller(name='get_metrics_custom',url='historical-validation-tool-colombia/get-metrics-custom')
def get_metrics_custom(request):
    # Combine metrics
    my_metrics_1 = ["ME", "RMSE", "NRMSE (Mean)", "NSE", "KGE (2009)", "KGE (2012)", "R (Pearson)", "R (Spearman)", "r2"]
    my_metrics_2 = request.GET['metrics'].split(",")
    lista_combinada = my_metrics_1 + my_metrics_2
    elementos_unicos = []
    elementos_vistos = set()
    for elemento in lista_combinada:
        if elemento not in elementos_vistos:
            elementos_unicos.append(elemento)
            elementos_vistos.add(elemento)
    # Compute metrics
    metrics_table = get_metrics_table(
                        merged_cor = merged_cor,
                        merged_sim = merged_sim,
                        my_metrics = elementos_unicos)
    return HttpResponse(metrics_table)



@controller(name='get_raw_forecast_date',url='historical-validation-tool-colombia/get-raw-forecast-date')
def get_raw_forecast_date(request):
    ## Variables
    station_code = request.GET['codigo']
    station_comid = request.GET['comid']
    station_name = request.GET['nombre']
    forecast_date = request.GET['fecha']
    plot_width = float(request.GET['width']) - 12

    # Establish connection to database
    db= create_engine(tokencon)
    conn = db.connect()

    # Data series
    observed_data = get_format_data("select datetime, s_{0} from observed_streamflow_data order by datetime;".format(station_code), conn)
    simulated_data = get_format_data("select * from hs_{0};".format(station_comid), conn)
    # TODO : remove whwere geoglows server works
    simulated_data = simulated_data[simulated_data.index < '2022-06-01'].copy()
    corrected_data = get_bias_corrected_data(simulated_data, observed_data)

    # Raw forecast
    ensemble_forecast = get_forecast_date(station_comid, forecast_date)
    forecast_records = get_forecast_record_date(station_comid, forecast_date)
    return_periods = get_return_periods(station_comid, simulated_data)

    # Corrected forecast
    # corrected_ensemble_forecast = get_corrected_forecast(simulated_data, ensemble_forecast, observed_data)
    corrected_ensemble_forecast = __bias_correction_forecast__(simulated_data, ensemble_forecast, observed_data)
    corrected_forecast_records = get_corrected_forecast_records(forecast_records, simulated_data, observed_data)
    corrected_return_periods = get_return_periods(station_comid, corrected_data)
    
    # Forecast stats
    ensemble_stats = get_ensemble_stats(ensemble_forecast)
    corrected_ensemble_stats = get_ensemble_stats(corrected_ensemble_forecast)
    
    # Close conection
    conn.close()

    # FEWS data
    obs_fews, sen_fews = get_fews_data(station_code)
    
    # Plotting raw forecast
    ensemble_forecast_plot = get_forecast_plot(
                                comid = station_comid, 
                                site = station_name, 
                                stats = ensemble_stats, 
                                rperiods = return_periods, 
                                records = forecast_records,
                                obs_data = {'data'  : [obs_fews, sen_fews],
                                            'color' : ['blue', 'red'],
                                            'name'  : ['Caudal observado', 'Caudal sensor']}).update_layout(width = plot_width).to_html()
    
    # Forecast table
    forecast_table = geoglows.plots.probabilities_table(
                                stats = ensemble_stats,
                                ensem = ensemble_forecast, 
                                rperiods = return_periods)


    # Plotting corrected forecast
    corr_ensemble_forecast_plot = get_forecast_plot(
                                    comid = station_comid, 
                                    site = station_name, 
                                    stats = corrected_ensemble_stats, 
                                    rperiods = corrected_return_periods, 
                                    records = corrected_forecast_records,
                                    obs_data = {'data'  : [obs_fews, sen_fews],
                                                'color' : ['blue', 'red'],
                                                'name'  : ['Caudal observado', 'Caudal sensor']}).update_layout(width = plot_width).to_html()
    # Corrected forecast table
    corr_forecast_table = geoglows.plots.probabilities_table(
                                    stats = corrected_ensemble_stats,
                                    ensem = corrected_ensemble_forecast, 
                                    rperiods = corrected_return_periods)
    
    return JsonResponse({
       'ensemble_forecast_plot': ensemble_forecast_plot,
       'forecast_table': forecast_table,
       'corr_ensemble_forecast_plot': corr_ensemble_forecast_plot,
       'corr_forecast_table': corr_forecast_table
    })
############################################################

# Retrieve observed data
@controller(name='get_observed_data_xlsx',
            url='historical-validation-tool-colombia/get-observed-data-xlsx')
def get_observed_data_xlsx(request):
    
    # Retrieving GET arguments
    station_code = request.GET['codigo']
    station_comid = request.GET['comid']
    forecast_date = request.GET['fecha']
    
    # Establish connection to database
    db= create_engine(tokencon)
    conn = db.connect()
    
    try:
    # Data series
        data = get_format_data("select datetime, s_{0} from observed_streamflow_data order by datetime;".format(station_code), conn)
        data.rename(columns={'s_{0}'.format(station_code): "Historical observation (m3/s)"}, inplace=True)
    finally:
       conn.close()
    
    # Crear el archivo Excel
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    data.to_excel(writer, sheet_name='serie_observada_simulada', index=True)
    writer.save()
    output.seek(0)

    # Configurar la respuesta HTTP para descargar el archivo
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=serie_historica_observada.xlsx'
    response.write(output.getvalue())
    return response


# Retrieve simualted data
@controller(name='get_simulated_data_xlsx',
            url='historical-validation-tool-colombia/get-simulated-data-xlsx')
def get_simulated_data_xlsx(request):

    # Retrieving GET arguments
    station_code = request.GET['codigo']
    station_comid = request.GET['comid']
    forecast_date = request.GET['fecha']
    
    # Establish connection to database
    db= create_engine(tokencon)
    conn = db.connect()
    
    try:
    # Data series
        data = get_format_data("select * from hs_{0};".format(station_comid), conn)
        # TODO : remove whwere geoglows server works
        simulated_data = simulated_data[simulated_data.index < '2022-06-01'].copy()
        data.rename(columns={data.columns[0]: "Historical simulation (m3/s)"}, inplace=True)
    finally:
       conn.close()
    
    # Crear el archivo Excel
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    data.to_excel(writer, sheet_name='serie_historica_simulada', index=True)
    writer.save()
    output.seek(0)

    # Configurar la respuesta HTTP para descargar el archivo
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=serie_historica_simulada.xlsx'
    response.write(output.getvalue())
    return response


# Retrieve simualted corrected data
@controller(name='get_corrected_data_xlsx',
            url='historical-validation-tool-colombia/get-corrected-data-xlsx')
def get_corrected_data_xlsx(request):

    # Retrieving GET arguments
    station_code = request.GET['codigo']
    station_comid = request.GET['comid']
    forecast_date = request.GET['fecha']
    
    # Establish connection to database
    db= create_engine(tokencon)
    conn = db.connect()
    
    try:
        # Data series
        observed_data  = get_format_data("select datetime, s_{0} from observed_streamflow_data order by datetime;".format(station_code), conn)
        simulated_data = get_format_data("select * from hs_{0};".format(station_comid), conn)
        # TODO : remove whwere geoglows server works
        simulated_data = simulated_data[simulated_data.index < '2022-06-01'].copy()
    finally:
       conn.close()

    # Fix data
    data = get_bias_corrected_data(simulated_data, observed_data)
    data.rename(columns={"Corrected Simulated Streamflow" : "Corrected Simulated Streamflow (m3/s)"}, 
                inplace = True)
    
    # Crear el archivo Excel
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    data.to_excel(writer, sheet_name='serie_historica_corregida', index=True)
    writer.save()
    output.seek(0)

    # Configurar la respuesta HTTP para descargar el archivo
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=serie_historica_corregida.xlsx'
    response.write(output.getvalue())
    return response


# Retrieve xlsx data
@controller(name='get_forecast_xlsx',url='historical-validation-tool-colombia/get-forecast-xlsx')
def get_forecast_xlsx(request):

    # Retrieving GET arguments
    station_code = request.GET['codigo']
    station_comid = request.GET['comid']
    forecast_date = request.GET['fecha']

    db= create_engine(tokencon)
    conn = db.connect()

    try:
        forecast_records = get_format_data("select * from fr_{0};".format(station_comid), conn)
    finally:
        conn.close()

    # Raw forecast
    ensemble_forecast = get_forecast_date(station_comid, forecast_date)
    ensemble_stats = get_ensemble_stats(ensemble_forecast)

    # Crear el archivo Excel
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    ensemble_stats.to_excel(writer, sheet_name='ensemble_stats', index=True)
    ensemble_forecast.to_excel(writer, sheet_name='ensemble_forecast', index=True)
    forecast_records.to_excel(writer, sheet_name='forecast_records', index=True)
    writer.save()
    output.seek(0)

    # Configurar la respuesta HTTP para descargar el archivo
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=ensemble_forecast.xlsx'
    response.write(output.getvalue())

    return response


@controller(name='get_corrected_forecast_xlsx',url='historical-validation-tool-colombia/get-corrected-forecast-xlsx')
def get_corrected_forecast_xlsx(request):
    # Retrieving GET arguments
    station_code = request.GET['codigo']
    station_comid = request.GET['comid']
    forecast_date = request.GET['fecha']

    # Establish connection to database
    db= create_engine(tokencon)
    conn = db.connect()
    try:
        # Data series
        observed_data  = get_format_data("select datetime, s_{0} from observed_streamflow_data order by datetime;".format(station_code), conn)
        simulated_data = get_format_data("select * from hs_{0};".format(station_comid), conn)
        # TODO : remove whwere geoglows server works
        simulated_data = simulated_data[simulated_data.index < '2022-06-01'].copy()
        forecast_records = get_format_data("select * from fr_{0};".format(station_comid), conn)
    finally:
        conn.close()

    # Raw forecast
    ensemble_forecast = get_forecast_date(station_comid, forecast_date)
    
    # Corrected forecast
    corrected_ensemble_forecast = __bias_correction_forecast__(simulated_data, ensemble_forecast, observed_data)
    
    # Forecast stats
    corrected_ensemble_stats = get_ensemble_stats(corrected_ensemble_forecast)

    # Forecast record correctes
    corrected_forecast_records = get_corrected_forecast_records(forecast_records, simulated_data, observed_data)
    
    # Crear el archivo Excel
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    corrected_ensemble_stats.to_excel(writer, sheet_name='corrected_ensemble_stats', index=True)
    corrected_ensemble_forecast.to_excel(writer, sheet_name='corrected_ensemble_forecast', index=True)
    corrected_forecast_records.to_excel(writer, sheet_name='corrected_forecast_records', index=True)
    writer.save()
    output.seek(0)

    # Configurar la respuesta HTTP para descargar el archivo
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=corrected_ensemble_forecast.xlsx'
    response.write(output.getvalue())
    return response

############################################################
@controller(name = "user_manual",
            url  = "historical-validation-tool-colombia/user_manual")
def user_manual(request):
    context = {}
    return render(request, 'historical_validation_tool_colombia/user_manual.html', context)


@controller(name = "technical_manual",
            url  = "historical-validation-tool-colombia/technical_manual")
def technical_manual(request):
    context = {}
    return render(request, 'historical_validation_tool_colombia/technical_manual.html', context)


############################################################
#                          SERVICES                        #
############################################################ 
@controller(name='get_image',
            url='historical-validation-tool-colombia/get-image')
def down_load_img(request):
    # Retrieving GET arguments
    station_code  = request.GET['codigo']
    type_graph = request.GET['typeGraph']

    # Establish connection to database
    db= create_engine(tokencon)
    conn = db.connect()

    try:
        # Stations dataframe
        stations = pd.read_sql("select codigo, nombre, comid from stations_waterlevel order by codigo", conn)
        # Read input data
        input_df = stations[stations['codigo'] == station_code].dropna().reset_index(drop=True)
        # Extrac data
        station_comid = str(int(input_df['comid'].values[0]))
        station_name  = input_df['nombre'].values[0]

        # Data series
        observed_data = get_format_data("select datetime, s_{0} from observed_streamflow_data order by datetime;".format(station_code), conn)
        simulated_data = get_format_data("select * from hs_{0};".format(station_comid), conn)
        # TODO : remove whwere geoglows server works
        simulated_data = simulated_data[simulated_data.index < '2022-06-01'].copy()
        corrected_data = get_bias_corrected_data(simulated_data, observed_data)

        # Raw forecast
        ensemble_forecast = get_format_data("select * from f_{0};".format(station_comid), conn)
        forecast_records = get_format_data("select * from fr_{0};".format(station_comid), conn)

    finally:
        # Close conection
        conn.close()

    # return_periods = get_return_periods(station_comid, simulated_data)

    # Corrected forecast
    # corrected_ensemble_forecast = get_corrected_forecast(simulated_data, ensemble_forecast, observed_data)
    corrected_ensemble_forecast = __bias_correction_forecast__(simulated_data, ensemble_forecast, observed_data)
    corrected_forecast_records = get_corrected_forecast_records(forecast_records, simulated_data, observed_data)
    corrected_return_periods = get_return_periods(station_comid, corrected_data)
    
    # FEWS data
    obs_fews, sen_fews = get_fews_data(station_code)

    # Stats for raw and corrected forecast
    # ensemble_stats = get_ensemble_stats(ensemble_forecast)
    corrected_ensemble_stats = get_ensemble_stats(corrected_ensemble_forecast)

    # Merge data (For plots)
    global merged_sim
    merged_sim = hd.merge_data(sim_df = simulated_data, obs_df = observed_data)
    global merged_cor
    merged_cor = hd.merge_data(sim_df = corrected_data, obs_df = observed_data)

    if 'historical' == type_graph:
        fig = geoglows.plots.corrected_historical(
                            simulated = simulated_data,
                            corrected = corrected_data,
                            observed = observed_data, 
                            outformat = "plotly", 
                            titles = {'Site': station_name, 'Reach COMID': station_comid})
        name_file = 'historical'
    elif 'forecast' == type_graph:
        fig = get_forecast_plot(
                                comid = station_comid, 
                                site = station_name, 
                                stats = corrected_ensemble_stats, 
                                rperiods = corrected_return_periods, 
                                records = corrected_forecast_records,
                                obs_data = {'data'  : [obs_fews, sen_fews],
                                            'color' : ['blue', 'red'],
                                            'name'  : ['Caudal observado', 'Caudal sensor']})
        name_file = 'corrected_forecast'
    
    # Build image bytes
    img_bytes = fig.to_image(format="png")

    # Configurar la respuesta HTTP para descargar el archivo
    response = HttpResponse(content_type="image/jpeg")
    response['Content-Disposition'] = 'attachment; filename={0}_{1}_Q.png'.format(name_file, station_comid)
    response.write(img_bytes)

    return response
