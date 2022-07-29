import datetime as dt
import io
import traceback
from csv import writer as csv_writer

import geoglows
import math
import hydrostats as hs
import hydrostats.data as hd
import pandas as pd
import numpy as np
import requests
import os
import json
import sys
import plotly.graph_objs as go
import scipy.stats as sp
from HydroErr.HydroErr import metric_names, metric_abbr

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from scipy import integrate
from tethys_sdk.gizmos import *
from tethys_sdk.routing import controller

import time
from hs_restclient import HydroShare, HydroShareAuthBasic
from .app import HistoricalValidationToolColombia as app


@controller(
    name='home',
    url='historical-validation-tool-colombia',
)
def home(request):
    """
    Controller for the app home page.
    """

    # List of Metrics to include in context
    metric_loop_list = list(zip(metric_names, metric_abbr))

    # Retrieve a geoserver engine and geoserver credentials.
    geoserver_engine = app.get_spatial_dataset_service(
        name='main_geoserver', as_engine=True)

    geos_username = geoserver_engine.username
    geos_password = geoserver_engine.password
    my_geoserver = geoserver_engine.endpoint.replace('rest', '')

    geoserver_base_url = my_geoserver
    geoserver_workspace = app.get_custom_setting('workspace')
    region = app.get_custom_setting('region')
    geoserver_endpoint = TextInput(display_text='',
                                   initial=json.dumps([geoserver_base_url, geoserver_workspace, region]),
                                   name='geoserver_endpoint',
                                   disabled=True)

    # Available Forecast Dates
    res = requests.get('https://geoglows.ecmwf.int/api/AvailableDates/?region=central_america-geoglows', verify=False)
    data = res.json()
    dates_array = (data.get('available_dates'))

    dates = []

    for date in dates_array:
        if len(date) == 10:
            date_mod = date + '000'
            date_f = dt.datetime.strptime(date_mod, '%Y%m%d.%H%M').strftime('%Y-%m-%d %H:%M')
        else:
            date_f = dt.datetime.strptime(date, '%Y%m%d.%H%M').strftime('%Y-%m-%d')
            date = date[:-3]
        dates.append([date_f, date])
        dates = sorted(dates)

    dates.append(['Select Date', dates[-1][1]])
    dates.reverse()

    # Date Picker Options
    date_picker = DatePicker(name='datesSelect',
                             display_text='Date',
                             autoclose=True,
                             format='yyyy-mm-dd',
                             start_date=dates[-1][0],
                             end_date=dates[1][0],
                             start_view='month',
                             today_button=True,
                             initial='')

    region_index = json.load(open(os.path.join(os.path.dirname(__file__), 'public', 'geojson', 'index.json')))
    regions = SelectInput(
        display_text='Zoom to a Region:',
        name='regions',
        multiple=False,
        original=True,
        options=[(region_index[opt]['name'], opt) for opt in region_index]
    )

    context = {
        "metric_loop_list": metric_loop_list,
        "geoserver_endpoint": geoserver_endpoint,
        "date_picker": date_picker,
        "regions": regions
    }

    return render(request, 'historical_validation_tool_colombia/home.html', context)

@controller(
    name='get_popup_response',
    url='get-request-data',
    app_workspace=True,
)
def get_popup_response(request, app_workspace):
    """
    get station attributes
    """

    start_time = time.time()

    observed_data_path_file = os.path.join(app_workspace.path, 'observed_data.json')
    simulated_data_path_file = os.path.join(app_workspace.path, 'simulated_data.json')
    corrected_data_path_file = os.path.join(app_workspace.path, 'corrected_data.json')
    forecast_data_path_file = os.path.join(app_workspace.path, 'forecast_data.json')

    f = open(observed_data_path_file, 'w')
    f.close()
    f2 = open(simulated_data_path_file, 'w')
    f2.close()
    f3 = open(corrected_data_path_file, 'w')
    f3.close()
    f4 = open(forecast_data_path_file, 'w')
    f4.close()

    return_obj = {}

    try:
        get_data = request.GET
        #get station attributes
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        '''Get Observed Data'''
        auth = HydroShareAuthBasic(username=app.get_custom_setting('username'), password=app.get_custom_setting('password'))
        hs = HydroShare(auth=auth)
        resource_id = app.get_custom_setting('hydroshare_resource_id')
        hs.setAccessRules(resource_id, public=True)

        url = 'https://www.hydroshare.org/resource/{0}/data/contents/Discharge_Data/{1}.csv'.format(resource_id, codEstacion)
        s = requests.get(url, verify=False).content
        df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
        df.index = pd.to_datetime(df.index)

        datesDischarge = df.index.tolist()
        dataDischarge = df.iloc[:, 0].values
        dataDischarge.tolist()

        if isinstance(dataDischarge[0], str):
            dataDischarge = map(float, dataDischarge)

        observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

        observed_data_file_path = os.path.join(app_workspace.path, 'observed_data.json')
        observed_df.reset_index(level=0, inplace=True)
        observed_df['index'] = observed_df['index'].dt.strftime('%Y-%m-%d')
        observed_df.set_index('index', inplace=True)
        observed_df.index = pd.to_datetime(observed_df.index)
        observed_df.index.name = 'datetime'
        observed_df.to_json(observed_data_file_path, orient='columns')

        '''Get Simulated Data'''
        simulated_df = geoglows.streamflow.historic_simulation(comid, forcing='era_5', return_format='csv')
        # Removing Negative Values
        simulated_df[simulated_df < 0] = 0
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.index = simulated_df.index.to_series().dt.strftime("%Y-%m-%d")
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df = pd.DataFrame(data=simulated_df.iloc[:, 0].values, index=simulated_df.index, columns=['Simulated Streamflow'])

        simulated_data_file_path = os.path.join(app_workspace.path, 'simulated_data.json')
        simulated_df.reset_index(level=0, inplace=True)
        simulated_df['datetime'] = simulated_df['datetime'].dt.strftime('%Y-%m-%d')
        simulated_df.set_index('datetime', inplace=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.index.name = 'Datetime'
        simulated_df.to_json(simulated_data_file_path)

        print("finished get_popup_response")

        print("--- %s seconds getpopup ---" % (time.time() - start_time))

        return JsonResponse({})


    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })


@controller(
    name='get_hydrographs',
    url='get-hydrographs',
    app_workspace=True
)
def get_hydrographs(request, app_workspace):
    """
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """

    start_time = time.time()

    try:

        get_data = request.GET
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        '''Get Observed Data'''
        observed_data_file_path = os.path.join(app_workspace.path, 'observed_data.json')
        observed_df = pd.read_json(observed_data_file_path,convert_dates=True)
        observed_df.index = pd.to_datetime(observed_df.index, unit='ms')
        observed_df.sort_index(inplace=True, ascending=True)

        '''Get Simulated Data'''
        simulated_data_file_path = os.path.join(app_workspace.path, 'simulated_data.json')
        simulated_df = pd.read_json(simulated_data_file_path, convert_dates=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.sort_index(inplace=True, ascending=True)

        '''Correct the Bias in Sumulation'''
        corrected_df = geoglows.bias.correct_historical(simulated_df, observed_df)
        corrected_data_file_path = os.path.join(app_workspace.path, 'corrected_data.json')
        corrected_df.reset_index(level=0, inplace=True)
        corrected_df['index'] = corrected_df['index'].dt.strftime('%Y-%m-%d')
        corrected_df.set_index('index', inplace=True)
        corrected_df.index = pd.to_datetime(corrected_df.index)
        corrected_df.index.name = 'Datetime'
        corrected_df.to_json(corrected_data_file_path)

        '''Plotting Data'''
        observed_Q = go.Scatter(x=observed_df.index, y=observed_df.iloc[:, 0].values, name='Observed', )
        simulated_Q = go.Scatter(x=simulated_df.index, y=simulated_df.iloc[:, 0].values, name='Simulated', )
        corrected_Q = go.Scatter(x=corrected_df.index, y=corrected_df.iloc[:, 0].values, name='Corrected Simulated', )

        layout = go.Layout(
            title='Observed & Simulated Streamflow at <br> {0} - {1}'.format(codEstacion, nomEstacion),
            xaxis=dict(title='Dates', ), yaxis=dict(title='Discharge (m<sup>3</sup>/s)', autorange=True),
            showlegend=True)

        chart_obj = PlotlyView(go.Figure(data=[observed_Q, simulated_Q, corrected_Q], layout=layout))

        context = {
            'gizmo_object': chart_obj,
        }

        print("--- %s seconds hydrographs ---" % (time.time() - start_time))

        return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })


@controller(
    name='get_dailyAverages',
    url='get-dailyAverages',
    app_workspace=True
)
def get_dailyAverages(request, app_workspace):
    """
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """

    start_time = time.time()

    try:
        get_data = request.GET
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        '''Get Observed Data'''
        observed_data_file_path = os.path.join(app_workspace.path, 'observed_data.json')
        observed_df = pd.read_json(observed_data_file_path,convert_dates=True)
        observed_df.index = pd.to_datetime(observed_df.index, unit='ms')
        observed_df.sort_index(inplace=True, ascending=True)

        '''Get Simulated Data'''
        simulated_data_file_path = os.path.join(app_workspace.path, 'simulated_data.json')
        simulated_df = pd.read_json(simulated_data_file_path, convert_dates=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.sort_index(inplace=True, ascending=True)

        '''Get Bias Corrected Data'''
        corrected_data_file_path = os.path.join(app_workspace.path, 'corrected_data.json')
        corrected_df = pd.read_json(corrected_data_file_path,convert_dates=True)
        corrected_df.index = pd.to_datetime(corrected_df.index)
        corrected_df.sort_index(inplace=True, ascending=True)

        '''Merge Data'''

        merged_df = hd.merge_data(sim_df=simulated_df, obs_df=observed_df)

        merged_df2 = hd.merge_data(sim_df=corrected_df, obs_df=observed_df)

        '''Plotting Data'''

        daily_avg = hd.daily_average(merged_df)

        daily_avg2 = hd.daily_average(merged_df2)

        daily_avg_obs_Q = go.Scatter(x=daily_avg.index, y=daily_avg.iloc[:, 1].values, name='Observed', )

        daily_avg_sim_Q = go.Scatter(x=daily_avg.index, y=daily_avg.iloc[:, 0].values, name='Simulated', )

        daily_avg_corr_sim_Q = go.Scatter(x=daily_avg2.index, y=daily_avg2.iloc[:, 0].values,
                                          name='Corrected Simulated', )

        layout = go.Layout(
            title='Daily Average Streamflow for <br> {0} - {1}'.format(codEstacion, nomEstacion),
            xaxis=dict(title='Days', ), yaxis=dict(title='Discharge (m<sup>3</sup>/s)', autorange=True),
            showlegend=True)

        chart_obj = PlotlyView(go.Figure(data=[daily_avg_obs_Q, daily_avg_sim_Q, daily_avg_corr_sim_Q], layout=layout))

        context = {
            'gizmo_object': chart_obj,
        }

        print("--- %s seconds dailyAverages ---" % (time.time() - start_time))

        return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)


    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })


@controller(
    name='get_monthlyAverages',
    url='get-monthlyAverages',
    app_workspace=True,
)
def get_monthlyAverages(request, app_workspace):
    """
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """

    start_time = time.time()

    try:
        get_data = request.GET
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        '''Get Observed Data'''
        observed_data_file_path = os.path.join(app_workspace.path, 'observed_data.json')
        observed_df = pd.read_json(observed_data_file_path,convert_dates=True)
        observed_df.index = pd.to_datetime(observed_df.index, unit='ms')
        observed_df.sort_index(inplace=True, ascending=True)

        '''Get Simulated Data'''
        simulated_data_file_path = os.path.join(app_workspace.path, 'simulated_data.json')
        simulated_df = pd.read_json(simulated_data_file_path, convert_dates=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.sort_index(inplace=True, ascending=True)

        '''Get Bias Corrected Data'''
        corrected_data_file_path = os.path.join(app_workspace.path, 'corrected_data.json')
        corrected_df = pd.read_json(corrected_data_file_path,convert_dates=True)
        corrected_df.index = pd.to_datetime(corrected_df.index)
        corrected_df.sort_index(inplace=True, ascending=True)

        '''Merge Data'''

        merged_df = hd.merge_data(sim_df=simulated_df, obs_df=observed_df)

        merged_df2 = hd.merge_data(sim_df=corrected_df, obs_df=observed_df)

        '''Plotting Data'''

        monthly_avg = hd.monthly_average(merged_df)

        monthly_avg2 = hd.monthly_average(merged_df2)

        monthly_avg_obs_Q = go.Scatter(x=monthly_avg.index, y=monthly_avg.iloc[:, 1].values, name='Observed', )

        monthly_avg_sim_Q = go.Scatter(x=monthly_avg.index, y=monthly_avg.iloc[:, 0].values, name='Simulated', )

        monthly_avg_corr_sim_Q = go.Scatter(x=monthly_avg2.index, y=monthly_avg2.iloc[:, 0].values,
                                            name='Corrected Simulated', )

        layout = go.Layout(
            title='Monthly Average Streamflow for <br> {0} - {1}'.format(codEstacion, nomEstacion),
            xaxis=dict(title='Months', ), yaxis=dict(title='Discharge (m<sup>3</sup>/s)', autorange=True),
            showlegend=True)

        chart_obj = PlotlyView(
            go.Figure(data=[monthly_avg_obs_Q, monthly_avg_sim_Q, monthly_avg_corr_sim_Q], layout=layout))

        context = {
            'gizmo_object': chart_obj,
        }

        print("--- %s seconds monthlyAverages ---" % (time.time() - start_time))

        return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })


@controller(
    name='get_scatterPlot',
    url='get-scatterPlot',
    app_workspace=True
)
def get_scatterPlot(request, app_workspace):
    """
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """

    start_time = time.time()

    try:
        get_data = request.GET
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        '''Get Observed Data'''
        observed_data_file_path = os.path.join(app_workspace.path, 'observed_data.json')
        observed_df = pd.read_json(observed_data_file_path,convert_dates=True)
        observed_df.index = pd.to_datetime(observed_df.index, unit='ms')
        observed_df.sort_index(inplace=True, ascending=True)

        '''Get Simulated Data'''
        simulated_data_file_path = os.path.join(app_workspace.path, 'simulated_data.json')
        simulated_df = pd.read_json(simulated_data_file_path, convert_dates=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.sort_index(inplace=True, ascending=True)

        '''Get Bias Corrected Data'''
        corrected_data_file_path = os.path.join(app_workspace.path, 'corrected_data.json')
        corrected_df = pd.read_json(corrected_data_file_path,convert_dates=True)
        corrected_df.index = pd.to_datetime(corrected_df.index)
        corrected_df.sort_index(inplace=True, ascending=True)

        '''Merge Data'''

        merged_df = hd.merge_data(sim_df=simulated_df, obs_df=observed_df)

        merged_df2 = hd.merge_data(sim_df=corrected_df, obs_df=observed_df)

        '''Plotting Data'''

        scatter_data = go.Scatter(
            x=merged_df.iloc[:, 0].values,
            y=merged_df.iloc[:, 1].values,
            mode='markers',
            name='original',
            marker=dict(color='#ef553b')
        )

        scatter_data2 = go.Scatter(
            x=merged_df2.iloc[:, 0].values,
            y=merged_df2.iloc[:, 1].values,
            mode='markers',
            name='corrected',
            marker=dict(color='#00cc96')
        )

        min_value = min(min(merged_df.iloc[:, 1].values), min(merged_df.iloc[:, 0].values))
        max_value = max(max(merged_df.iloc[:, 1].values), max(merged_df.iloc[:, 0].values))

        min_value2 = min(min(merged_df2.iloc[:, 1].values), min(merged_df2.iloc[:, 0].values))
        max_value2 = max(max(merged_df2.iloc[:, 1].values), max(merged_df2.iloc[:, 0].values))

        line_45 = go.Scatter(
            x=[min_value, max_value],
            y=[min_value, max_value],
            mode='lines',
            name='45deg line',
            line=dict(color='black')
        )

        slope, intercept, r_value, p_value, std_err = sp.linregress(merged_df.iloc[:, 0].values,
                                                                    merged_df.iloc[:, 1].values)

        slope2, intercept2, r_value2, p_value2, std_err2 = sp.linregress(merged_df2.iloc[:, 0].values,
                                                                         merged_df2.iloc[:, 1].values)

        line_adjusted = go.Scatter(
            x=[min_value, max_value],
            y=[slope * min_value + intercept, slope * max_value + intercept],
            mode='lines',
            name='{0}x + {1} (Original)'.format(str(round(slope, 2)), str(round(intercept, 2))),
            line=dict(color='red')
        )

        line_adjusted2 = go.Scatter(
            x=[min_value, max_value],
            y=[slope2 * min_value + intercept2, slope2 * max_value + intercept2],
            mode='lines',
            name='{0}x + {1} (Corrected)'.format(str(round(slope2, 2)), str(round(intercept2, 2))),
            line=dict(color='green')
        )

        layout = go.Layout(title="Scatter Plot for {0} - {1}".format(codEstacion, nomEstacion),
                           xaxis=dict(title='Simulated', ), yaxis=dict(title='Observed', autorange=True),
                           showlegend=True)

        chart_obj = PlotlyView(
            go.Figure(data=[scatter_data, scatter_data2, line_45, line_adjusted, line_adjusted2], layout=layout))

        context = {
            'gizmo_object': chart_obj,
        }

        print("--- %s seconds scatterPlot ---" % (time.time() - start_time))

        return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })


@controller(
    name='get_scatterPlotLogScale',
    url='get-scatterPlotLogScale',
    app_workspace=True
)
def get_scatterPlotLogScale(request):
    """
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """

    start_time = time.time()

    try:
        get_data = request.GET
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        '''Get Observed Data'''
        observed_data_file_path = os.path.join(app_workspace.path, 'observed_data.json')
        observed_df = pd.read_json(observed_data_file_path,convert_dates=True)
        observed_df.index = pd.to_datetime(observed_df.index, unit='ms')
        observed_df.sort_index(inplace=True, ascending=True)

        '''Get Simulated Data'''
        simulated_data_file_path = os.path.join(app_workspace.path, 'simulated_data.json')
        simulated_df = pd.read_json(simulated_data_file_path, convert_dates=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.sort_index(inplace=True, ascending=True)

        '''Get Bias Corrected Data'''
        corrected_data_file_path = os.path.join(app_workspace.path, 'corrected_data.json')
        corrected_df = pd.read_json(corrected_data_file_path,convert_dates=True)
        corrected_df.index = pd.to_datetime(corrected_df.index)
        corrected_df.sort_index(inplace=True, ascending=True)

        '''Merge Data'''

        merged_df = hd.merge_data(sim_df=simulated_df, obs_df=observed_df)

        merged_df2 = hd.merge_data(sim_df=corrected_df, obs_df=observed_df)

        '''Plotting Data'''

        scatter_data = go.Scatter(
            x=merged_df.iloc[:, 0].values,
            y=merged_df.iloc[:, 1].values,
            mode='markers',
            name='original',
            marker=dict(color='#ef553b')
        )

        scatter_data2 = go.Scatter(
            x=merged_df2.iloc[:, 0].values,
            y=merged_df2.iloc[:, 1].values,
            mode='markers',
            name='corrected',
            marker=dict(color='#00cc96')
        )

        min_value = min(min(merged_df.iloc[:, 1].values), min(merged_df.iloc[:, 0].values))
        max_value = max(max(merged_df.iloc[:, 1].values), max(merged_df.iloc[:, 0].values))

        line_45 = go.Scatter(
            x=[min_value, max_value],
            y=[min_value, max_value],
            mode='lines',
            name='45deg line',
            line=dict(color='black')
        )

        layout = go.Layout(title="Scatter Plot for {0} - {1} (Log Scale)".format(codEstacion, nomEstacion),
                           xaxis=dict(title='Simulated', type='log', ), yaxis=dict(title='Observed', type='log',
                                                                                   autorange=True), showlegend=True)

        chart_obj = PlotlyView(go.Figure(data=[scatter_data, scatter_data2, line_45], layout=layout))

        context = {
            'gizmo_object': chart_obj,
        }

        print("--- %s seconds scatterPlot_log ---" % (time.time() - start_time))

        return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })

@controller(
    name='get_volumeAnalysis',
    url='get-volumeAnalysis',
    app_workspace=True,
)
def get_volumeAnalysis(request):
    """
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """

    start_time = time.time()

    try:
        get_data = request.GET
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        '''Get Observed Data'''
        observed_data_file_path = os.path.join(app_workspace.path, 'observed_data.json')
        observed_df = pd.read_json(observed_data_file_path,convert_dates=True)
        observed_df.index = pd.to_datetime(observed_df.index, unit='ms')
        observed_df.sort_index(inplace=True, ascending=True)

        '''Get Simulated Data'''
        simulated_data_file_path = os.path.join(app_workspace.path, 'simulated_data.json')
        simulated_df = pd.read_json(simulated_data_file_path, convert_dates=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.sort_index(inplace=True, ascending=True)

        '''Get Bias Corrected Data'''
        corrected_data_file_path = os.path.join(app_workspace.path, 'corrected_data.json')
        corrected_df = pd.read_json(corrected_data_file_path,convert_dates=True)
        corrected_df.index = pd.to_datetime(corrected_df.index)
        corrected_df.sort_index(inplace=True, ascending=True)

        '''Merge Data'''

        merged_df = hd.merge_data(sim_df=simulated_df, obs_df=observed_df)

        merged_df2 = hd.merge_data(sim_df=corrected_df, obs_df=observed_df)

        '''Plotting Data'''

        sim_array = merged_df.iloc[:, 0].values
        obs_array = merged_df.iloc[:, 1].values
        corr_array = merged_df2.iloc[:, 0].values

        sim_volume_dt = sim_array * 0.0864
        obs_volume_dt = obs_array * 0.0864
        corr_volume_dt = corr_array * 0.0864

        sim_volume_cum = []
        obs_volume_cum = []
        corr_volume_cum = []
        sum_sim = 0
        sum_obs = 0
        sum_corr = 0

        for i in sim_volume_dt:
            sum_sim = sum_sim + i
            sim_volume_cum.append(sum_sim)

        for j in obs_volume_dt:
            sum_obs = sum_obs + j
            obs_volume_cum.append(sum_obs)

        for k in corr_volume_dt:
            sum_corr = sum_corr + k
            corr_volume_cum.append(sum_corr)

        observed_volume = go.Scatter(x=merged_df.index, y=obs_volume_cum, name='Observed', )

        simulated_volume = go.Scatter(x=merged_df.index, y=sim_volume_cum, name='Simulated', )

        corrected_volume = go.Scatter(x=merged_df2.index, y=corr_volume_cum, name='Corrected Simulated', )

        layout = go.Layout(
            title='Observed & Simulated Volume at<br> {0} - {1}'.format(codEstacion, nomEstacion),
            xaxis=dict(title='Dates', ), yaxis=dict(title='Volume (Mm<sup>3</sup>)', autorange=True),
            showlegend=True)

        chart_obj = PlotlyView(go.Figure(data=[observed_volume, simulated_volume, corrected_volume], layout=layout))

        print("--- %s seconds volumeAnalysis ---" % (time.time() - start_time))

        context = {
            'gizmo_object': chart_obj,
        }

        return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })


@controller(
    name='volume_table_ajax',
    url='volume-table-ajax',
    app_workspace=True,
)
def volume_table_ajax(request, app_workspace):
    """Calculates the volumes of the simulated and
    observed streamflow"""

    start_time = time.time()

    try:
        get_data = request.GET
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        '''Get Observed Data'''
        observed_data_file_path = os.path.join(app_workspace.path, 'observed_data.json')
        observed_df = pd.read_json(observed_data_file_path, convert_dates=True)
        observed_df.index = pd.to_datetime(observed_df.index, unit='ms')
        observed_df.sort_index(inplace=True, ascending=True)

        '''Get Simulated Data'''
        simulated_data_file_path = os.path.join(app_workspace.path, 'simulated_data.json')
        simulated_df = pd.read_json(simulated_data_file_path, convert_dates=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.sort_index(inplace=True, ascending=True)

        '''Get Bias Corrected Data'''
        corrected_data_file_path = os.path.join(app_workspace.path, 'corrected_data.json')
        corrected_df = pd.read_json(corrected_data_file_path, convert_dates=True)
        corrected_df.index = pd.to_datetime(corrected_df.index)
        corrected_df.sort_index(inplace=True, ascending=True)

        '''Merge Data'''

        merged_df = hd.merge_data(sim_df=simulated_df, obs_df=observed_df)

        merged_df2 = hd.merge_data(sim_df=corrected_df, obs_df=observed_df)

        '''Plotting Data'''

        sim_array = merged_df.iloc[:, 0].values
        obs_array = merged_df.iloc[:, 1].values
        corr_array = merged_df2.iloc[:, 0].values

        sim_volume = round((integrate.simps(sim_array)) * 0.0864, 3)
        obs_volume = round((integrate.simps(obs_array)) * 0.0864, 3)
        corr_volume = round((integrate.simps(corr_array)) * 0.0864, 3)

        resp = {
            "sim_volume": sim_volume,
            "obs_volume": obs_volume,
            "corr_volume": corr_volume,
        }

        print("--- %s seconds volumeAnalysis_table ---" % (time.time() - start_time))

        return JsonResponse(resp)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })


@controller(
    name='make_table_ajax',
    url='make-table-ajax',
    app_workspace=True,
)
def make_table_ajax(request, app_workspace):

    start_time = time.time()

    try:
        get_data = request.GET
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        # Indexing the metrics to get the abbreviations
        selected_metric_abbr = get_data.getlist("metrics[]", None)

        # Retrive additional parameters if they exist
        # Retrieving the extra optional parameters
        extra_param_dict = {}

        if request.GET.get('mase_m', None) is not None:
            mase_m = float(request.GET.get('mase_m', None))
            extra_param_dict['mase_m'] = mase_m
        else:
            mase_m = 1
            extra_param_dict['mase_m'] = mase_m

        if request.GET.get('dmod_j', None) is not None:
            dmod_j = float(request.GET.get('dmod_j', None))
            extra_param_dict['dmod_j'] = dmod_j
        else:
            dmod_j = 1
            extra_param_dict['dmod_j'] = dmod_j

        if request.GET.get('nse_mod_j', None) is not None:
            nse_mod_j = float(request.GET.get('nse_mod_j', None))
            extra_param_dict['nse_mod_j'] = nse_mod_j
        else:
            nse_mod_j = 1
            extra_param_dict['nse_mod_j'] = nse_mod_j

        if request.GET.get('h6_k_MHE', None) is not None:
            h6_mhe_k = float(request.GET.get('h6_k_MHE', None))
            extra_param_dict['h6_mhe_k'] = h6_mhe_k
        else:
            h6_mhe_k = 1
            extra_param_dict['h6_mhe_k'] = h6_mhe_k

        if request.GET.get('h6_k_AHE', None) is not None:
            h6_ahe_k = float(request.GET.get('h6_k_AHE', None))
            extra_param_dict['h6_ahe_k'] = h6_ahe_k
        else:
            h6_ahe_k = 1
            extra_param_dict['h6_ahe_k'] = h6_ahe_k

        if request.GET.get('h6_k_RMSHE', None) is not None:
            h6_rmshe_k = float(request.GET.get('h6_k_RMSHE', None))
            extra_param_dict['h6_rmshe_k'] = h6_rmshe_k
        else:
            h6_rmshe_k = 1
            extra_param_dict['h6_rmshe_k'] = h6_rmshe_k

        if float(request.GET.get('lm_x_bar', None)) != 1:
            lm_x_bar_p = float(request.GET.get('lm_x_bar', None))
            extra_param_dict['lm_x_bar_p'] = lm_x_bar_p
        else:
            lm_x_bar_p = None
            extra_param_dict['lm_x_bar_p'] = lm_x_bar_p

        if float(request.GET.get('d1_p_x_bar', None)) != 1:
            d1_p_x_bar_p = float(request.GET.get('d1_p_x_bar', None))
            extra_param_dict['d1_p_x_bar_p'] = d1_p_x_bar_p
        else:
            d1_p_x_bar_p = None
            extra_param_dict['d1_p_x_bar_p'] = d1_p_x_bar_p

        '''Get Observed Data'''
        observed_data_file_path = os.path.join(app_workspace.path, 'observed_data.json')
        observed_df = pd.read_json(observed_data_file_path,convert_dates=True)
        observed_df.index = pd.to_datetime(observed_df.index, unit='ms')
        observed_df.sort_index(inplace=True, ascending=True)

        '''Get Simulated Data'''
        simulated_data_file_path = os.path.join(app_workspace.path, 'simulated_data.json')
        simulated_df = pd.read_json(simulated_data_file_path, convert_dates=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.sort_index(inplace=True, ascending=True)

        '''Get Bias Corrected Data'''
        corrected_data_file_path = os.path.join(app_workspace.path, 'corrected_data.json')
        corrected_df = pd.read_json(corrected_data_file_path,convert_dates=True)
        corrected_df.index = pd.to_datetime(corrected_df.index)
        corrected_df.sort_index(inplace=True, ascending=True)

        '''Merge Data'''
        merged_df = hd.merge_data(sim_df=simulated_df, obs_df=observed_df)
        merged_df2 = hd.merge_data(sim_df=corrected_df, obs_df=observed_df)

        '''Plotting Data'''

        # Creating the Table Based on User Input
        table = hs.make_table(
            merged_dataframe = merged_df,
            metrics = selected_metric_abbr,
            # remove_neg=remove_neg,
            # remove_zero=remove_zero,
            mase_m =  extra_param_dict['mase_m'],
            dmod_j = extra_param_dict['dmod_j'],
            nse_mod_j = extra_param_dict['nse_mod_j'],
            h6_mhe_k = extra_param_dict['h6_mhe_k'],
            h6_ahe_k = extra_param_dict['h6_ahe_k'],
            h6_rmshe_k= extra_param_dict['h6_rmshe_k'],
            d1_p_obs_bar_p= extra_param_dict['d1_p_x_bar_p'],
            lm_x_obs_bar_p= extra_param_dict['lm_x_bar_p'],
            # seasonal_periods=all_date_range_list
        )
        table = table.round(decimals=2)
        table_html = table.transpose()
        table_html = table_html.to_html(classes="table table-hover table-striped").replace('border="1"', 'border="0"')

        # Creating the Table Based on User Input
        table2 = hs.make_table(
            merged_dataframe = merged_df2,
            metrics= selected_metric_abbr,
            # remove_neg=remove_neg,
            # remove_zero=remove_zero,
            mase_m= extra_param_dict['mase_m'],
            dmod_j= extra_param_dict['dmod_j'],
            nse_mod_j= extra_param_dict['nse_mod_j'],
            h6_mhe_k= extra_param_dict['h6_mhe_k'],
            h6_ahe_k= extra_param_dict['h6_ahe_k'],
            h6_rmshe_k= extra_param_dict['h6_rmshe_k'],
            d1_p_obs_bar_p= extra_param_dict['d1_p_x_bar_p'],
            lm_x_obs_bar_p= extra_param_dict['lm_x_bar_p'],
            # seasonal_periods=all_date_range_list
        )
        table2 = table2.round(decimals=2)
        table_html2 = table2.transpose()
        table_html2 = table_html2.to_html(classes="table table-hover table-striped").replace('border="1"', 'border="0"')

        table2 = table2.rename(index={'Full Time Series': 'Corrected Full Time Series'})
        table = table.rename(index={'Full Time Series': 'Original Full Time Series'})
        table_html2 = table2.transpose()
        table_html1 = table.transpose()

        table_final = pd.merge(table_html1, table_html2, right_index=True, left_index=True)

        table_final_html = table_final.to_html(classes="table table-hover table-striped",
                                               table_id="corrected_1").replace('border="1"', 'border="0"')

        print("--- %s seconds metrics_table ---" % (time.time() - start_time))

        return HttpResponse(table_final_html)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })


def get_units_title(unit_type):
    """
    Get the title for units
    """
    units_title = "m"
    if unit_type == 'english':
        units_title = "ft"
    return units_title


@controller(
    name='get-time-series',
    url='get-time-series',
    app_workspace=True,
)
def get_time_series(request, app_workspace):

    start_time = time.time()

    try:
        get_data = request.GET
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']
        startdate = get_data['startdate']

        '''Getting Forecast Stats'''
        if startdate != '':
            res = requests.get('https://geoglows.ecmwf.int/api/ForecastStats/?reach_id=' + comid + '&date=' + startdate + '&return_format=csv', verify=False).content
        else:
            res = requests.get('https://geoglows.ecmwf.int/api/ForecastStats/?reach_id=' + comid + '&return_format=csv', verify=False).content

        '''Get Forecasts'''
        forecast_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)
        forecast_df.index = pd.to_datetime(forecast_df.index)
        forecast_df[forecast_df < 0] = 0
        forecast_df.index = forecast_df.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
        forecast_df.index = pd.to_datetime(forecast_df.index)

        forecast_data_file_path = os.path.join(app_workspace.path, 'forecast_data.json')
        forecast_df.index.name = 'Datetime'
        forecast_df.to_json(forecast_data_file_path)

        hydroviewer_figure = geoglows.plots.forecast_stats(stats=forecast_df, titles={'Station': nomEstacion + '-' + str(codEstacion), 'Reach ID': comid})

        x_vals = (forecast_df.index[0], forecast_df.index[len(forecast_df.index) - 1], forecast_df.index[len(forecast_df.index) - 1], forecast_df.index[0])
        max_visible = max(forecast_df.max())

        '''Getting forecast record'''

        forecast_record = geoglows.streamflow.forecast_records(comid)
        forecast_record[forecast_record < 0] = 0
        forecast_record.index = forecast_record.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
        forecast_record.index = pd.to_datetime(forecast_record.index)

        record_plot = forecast_record.copy()
        record_plot = record_plot.loc[record_plot.index >= pd.to_datetime(forecast_df.index[0] - dt.timedelta(days=8))]
        record_plot = record_plot.loc[record_plot.index <= pd.to_datetime(forecast_df.index[0] + dt.timedelta(days=2))]

        if len(record_plot.index) > 0:
            hydroviewer_figure.add_trace(go.Scatter(
                name='1st days forecasts',
                x=record_plot.index,
                y=record_plot.iloc[:, 0].values,
                line=dict(
                    color='#FFA15A',
                )
            ))

            x_vals = (record_plot.index[0], forecast_df.index[len(forecast_df.index) - 1], forecast_df.index[len(forecast_df.index) - 1], record_plot.index[0])
            max_visible = max(record_plot.max().values[0], max_visible)

        '''Getting real time observed data'''
        url_rt = 'http://fews.ideam.gov.co/colombia/jsonQ/00' + codEstacion + 'Qobs.json'
        f = requests.get(url_rt, verify=False)

        if f.status_code == 200:
            data = f.json()

            observedDischarge = (data.get('obs'))
            sensorDischarge = (data.get('sen'))

            observedDischarge = (observedDischarge.get('data'))
            sensorDischarge = (sensorDischarge.get('data'))

            datesObservedDischarge = [row[0] for row in observedDischarge]
            observedDischarge = [row[1] for row in observedDischarge]

            datesSensorDischarge = [row[0] for row in sensorDischarge]
            sensorDischarge = [row[1] for row in sensorDischarge]

            dates = []
            discharge = []

            for i in range(0, len(datesObservedDischarge) - 1):
                year = int(datesObservedDischarge[i][0:4])
                month = int(datesObservedDischarge[i][5:7])
                day = int(datesObservedDischarge[i][8:10])
                hh = int(datesObservedDischarge[i][11:13])
                mm = int(datesObservedDischarge[i][14:16])
                dates.append(dt.datetime(year, month, day, hh, mm))
                discharge.append(observedDischarge[i])

            datesObservedDischarge = dates
            observedDischarge = discharge

            dates = []
            discharge = []

            for i in range(0, len(datesSensorDischarge) - 1):
                year = int(datesSensorDischarge[i][0:4])
                month = int(datesSensorDischarge[i][5:7])
                day = int(datesSensorDischarge[i][8:10])
                hh = int(datesSensorDischarge[i][11:13])
                mm = int(datesSensorDischarge[i][14:16])
                dates.append(dt.datetime(year, month, day, hh, mm))
                discharge.append(sensorDischarge[i])

            datesSensorDischarge = dates
            sensorDischarge = discharge

            try:
                # convert request into pandas DF
                pairs = [list(a) for a in zip(datesObservedDischarge, observedDischarge)]
                observed_rt = pd.DataFrame(pairs, columns=['Datetime', 'Observed (m3/s)'])
                observed_rt.set_index('Datetime', inplace=True)
                observed_rt = observed_rt.dropna()
                #observed_rt = observed_rt.groupby(observed_rt.index.strftime("%Y/%m/%d")).mean()
                observed_rt.index = pd.to_datetime(observed_rt.index)
                #observed_rt.index = observed_rt.index.tz_localize('UTC')
                observed_rt = observed_rt.dropna()

                observed_rt_plot = observed_rt.copy()
                observed_rt_plot = observed_rt_plot.loc[observed_rt_plot.index >= pd.to_datetime(forecast_df.index[0] - dt.timedelta(days=8))]
                observed_rt_plot = observed_rt_plot.loc[observed_rt_plot.index <= pd.to_datetime(forecast_df.index[0] + dt.timedelta(days=2))]

                if len(observed_rt_plot.index) > 0:
                    hydroviewer_figure.add_trace(go.Scatter(
                        name='Observed Streamflow',
                        x=observed_rt_plot.index,
                        y=observed_rt_plot.iloc[:, 0].values,
                        line=dict(
                            color='green',
                        )
                    ))

                    #x_vals = (observed_rt_plot.index[0], forecast_df.index[len(forecast_df.index) - 1], forecast_df.index[len(forecast_df.index) - 1], observed_rt_plot.index[0])
                    max_visible = max(observed_rt_plot.max().values[0], max_visible)

            except Exception as e:
                print(str(e))

            try:
                # convert request into pandas DF
                pairs = [list(a) for a in zip(datesSensorDischarge, sensorDischarge)]
                sensor_rt = pd.DataFrame(pairs, columns=['Datetime', 'Sensor (m3/s)'])
                sensor_rt.set_index('Datetime', inplace=True)
                sensor_rt = sensor_rt.dropna()
                #sensor_rt = sensor_rt.groupby(sensor_rt.index.strftime("%Y/%m/%d")).mean()
                sensor_rt.index = pd.to_datetime(sensor_rt.index)
                #sensor_rt.index = sensor_rt.index.tz_localize('UTC')
                sensor_rt = sensor_rt.dropna()

                sensor_rt_plot = sensor_rt.copy()
                sensor_rt_plot = sensor_rt_plot.loc[sensor_rt_plot.index >= pd.to_datetime(forecast_df.index[0] - dt.timedelta(days=8))]
                sensor_rt_plot = sensor_rt_plot.loc[sensor_rt_plot.index <= pd.to_datetime(forecast_df.index[0] + dt.timedelta(days=2))]

                if len(sensor_rt_plot.index) > 0:
                    hydroviewer_figure.add_trace(go.Scatter(
                        name='Sensor Streamflow',
                        x=sensor_rt_plot.index,
                        y=sensor_rt_plot.iloc[:, 0].values,
                        line=dict(
                            color='yellow',
                        )
                    ))

                    #x_vals = (sensor_rt_plot.index[0], forecast_df.index[len(forecast_df.index) - 1], forecast_df.index[len(forecast_df.index) - 1], sensor_rt_plot.index[0])
                    max_visible = max(sensor_rt_plot.max().values[0], max_visible)

            except Exception as e:
                print(str(e))

        '''Getting Return Periods'''

        try:
            rperiods = geoglows.streamflow.return_periods(comid)

            r2 = int(rperiods.iloc[0]['return_period_2'])

            colors = {
                '2 Year': 'rgba(254, 240, 1, .4)',
                '5 Year': 'rgba(253, 154, 1, .4)',
                '10 Year': 'rgba(255, 56, 5, .4)',
                '20 Year': 'rgba(128, 0, 246, .4)',
                '25 Year': 'rgba(255, 0, 0, .4)',
                '50 Year': 'rgba(128, 0, 106, .4)',
                '100 Year': 'rgba(128, 0, 246, .4)',
            }

            if max_visible > r2:
                visible = True
                hydroviewer_figure.for_each_trace(
                    lambda trace: trace.update(visible=True) if trace.name == "Maximum & Minimum Flow" else (),
                )
            else:
                visible = 'legendonly'
                hydroviewer_figure.for_each_trace(
                    lambda trace: trace.update(visible=True) if trace.name == "Maximum & Minimum Flow" else (),
                )

            def template(name, y, color, fill='toself'):
                return go.Scatter(
                    name=name,
                    x=x_vals,
                    y=y,
                    legendgroup='returnperiods',
                    fill=fill,
                    visible=visible,
                    line=dict(color=color, width=0))

            r5 = int(rperiods.iloc[0]['return_period_5'])
            r10 = int(rperiods.iloc[0]['return_period_10'])
            r25 = int(rperiods.iloc[0]['return_period_25'])
            r50 = int(rperiods.iloc[0]['return_period_50'])
            r100 = int(rperiods.iloc[0]['return_period_100'])

            hydroviewer_figure.add_trace(template('Return Periods', (r100 * 0.05, r100 * 0.05, r100 * 0.05, r100 * 0.05), 'rgba(0,0,0,0)', fill='none'))
            hydroviewer_figure.add_trace(template(f'2 Year: {r2}', (r2, r2, r5, r5), colors['2 Year']))
            hydroviewer_figure.add_trace(template(f'5 Year: {r5}', (r5, r5, r10, r10), colors['5 Year']))
            hydroviewer_figure.add_trace(template(f'10 Year: {r10}', (r10, r10, r25, r25), colors['10 Year']))
            hydroviewer_figure.add_trace(template(f'25 Year: {r25}', (r25, r25, r50, r50), colors['25 Year']))
            hydroviewer_figure.add_trace(template(f'50 Year: {r50}', (r50, r50, r100, r100), colors['50 Year']))
            hydroviewer_figure.add_trace(template(f'100 Year: {r100}', (r100, r100, max(r100 + r100 * 0.05, max_visible), max(r100 + r100 * 0.05, max_visible)),colors['100 Year']))


        except Exception as e:
            print(str(e))

        chart_obj = PlotlyView(hydroviewer_figure)

        context = {
            'gizmo_object': chart_obj,
        }

        print("--- %s seconds forecasts ---" % (time.time() - start_time))

        return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })


@controller(
    name='get-time-series-bc',
    url='get-time-series-bc',
    app_workspace=True,
)
def get_time_series_bc(request, app_workspace):

    start_time = time.time()

    try:

        get_data = request.GET
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']
        startdate = get_data['startdate']

        '''Get Observed Data'''
        observed_data_file_path = os.path.join(app_workspace.path, 'observed_data.json')
        observed_df = pd.read_json(observed_data_file_path, convert_dates=True)
        observed_df.index = pd.to_datetime(observed_df.index, unit='ms')
        observed_df.sort_index(inplace=True, ascending=True)

        '''Get Simulated Data'''
        simulated_data_file_path = os.path.join(app_workspace.path, 'simulated_data.json')
        simulated_df = pd.read_json(simulated_data_file_path, convert_dates=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.sort_index(inplace=True, ascending=True)

        '''Get Bias Corrected Data'''
        corrected_data_file_path = os.path.join(app_workspace.path, 'corrected_data.json')
        corrected_df = pd.read_json(corrected_data_file_path, convert_dates=True)
        corrected_df.index = pd.to_datetime(corrected_df.index)
        corrected_df.sort_index(inplace=True, ascending=True)

        '''Getting Forecast Stats'''
        if startdate != '':
            res = requests.get('https://geoglows.ecmwf.int/api/ForecastEnsembles/?reach_id=' + comid + '&date=' + startdate + '&return_format=csv', verify=False).content
        else:
            res = requests.get('https://geoglows.ecmwf.int/api/ForecastEnsembles/?reach_id=' + comid + '&return_format=csv', verify=False).content

        '''Get Forecasts'''
        forecast_ens = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)
        forecast_ens.index = pd.to_datetime(forecast_ens.index)
        forecast_ens[forecast_ens < 0] = 0
        forecast_ens.index = forecast_ens.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
        forecast_ens.index = pd.to_datetime(forecast_ens.index)

        forecast_ens_file_path = os.path.join(app_workspace.path, 'forecast_ens.json')
        forecast_ens.index.name = 'Datetime'
        forecast_ens.to_json(forecast_ens_file_path)

        '''Get Forecasts Records'''
        forecast_record = geoglows.streamflow.forecast_records(comid)
        forecast_record[forecast_record < 0] = 0
        forecast_record.index = forecast_record.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
        forecast_record.index = pd.to_datetime(forecast_record.index)

        '''Correct Bias Forecasts'''
        monthly_simulated = simulated_df[simulated_df.index.month == (forecast_ens.index[0]).month].dropna()
        monthly_observed = observed_df[observed_df.index.month == (forecast_ens.index[0]).month].dropna()

        min_simulated = np.min(monthly_simulated.iloc[:, 0].to_list())
        max_simulated = np.max(monthly_simulated.iloc[:, 0].to_list())

        min_factor_df = forecast_ens.copy()
        max_factor_df = forecast_ens.copy()
        forecast_ens_df = forecast_ens.copy()

        for column in forecast_ens.columns:
            tmp = forecast_ens[column].dropna().to_frame()
            min_factor = tmp.copy()
            max_factor = tmp.copy()
            min_factor.loc[min_factor[column] >= min_simulated, column] = 1
            min_index_value = min_factor[min_factor[column] != 1].index.tolist()

            for element in min_index_value:
                min_factor[column].loc[min_factor.index == element] = tmp[column].loc[tmp.index == element] / min_simulated

            max_factor.loc[max_factor[column] <= max_simulated, column] = 1
            max_index_value = max_factor[max_factor[column] != 1].index.tolist()

            for element in max_index_value:
                max_factor[column].loc[max_factor.index == element] = tmp[column].loc[tmp.index == element] / max_simulated

            tmp.loc[tmp[column] <= min_simulated, column] = min_simulated
            tmp.loc[tmp[column] >= max_simulated, column] = max_simulated
            forecast_ens_df.update(pd.DataFrame(tmp[column].values, index=tmp.index, columns=[column]))
            min_factor_df.update(pd.DataFrame(min_factor[column].values, index=min_factor.index, columns=[column]))
            max_factor_df.update(pd.DataFrame(max_factor[column].values, index=max_factor.index, columns=[column]))

        corrected_ensembles = geoglows.bias.correct_forecast(forecast_ens_df, simulated_df, observed_df)
        corrected_ensembles = corrected_ensembles.multiply(min_factor_df, axis=0)
        corrected_ensembles = corrected_ensembles.multiply(max_factor_df, axis=0)

        forecast_ens_bc_file_path = os.path.join(app_workspace.path, 'forecast_ens_bc.json')
        corrected_ensembles.index.name = 'Datetime'
        corrected_ensembles.to_json(forecast_ens_bc_file_path)

        ensemble = corrected_ensembles.copy()
        high_res_df = ensemble['ensemble_52_m^3/s'].to_frame()
        ensemble.drop(columns=['ensemble_52_m^3/s'], inplace=True)
        ensemble.dropna(inplace=True)
        high_res_df.dropna(inplace=True)

        max_df = ensemble.quantile(1.0, axis=1).to_frame()
        max_df.rename(columns={1.0: 'flow_max_m^3/s'}, inplace=True)

        p75_df = ensemble.quantile(0.75, axis=1).to_frame()
        p75_df.rename(columns={0.75: 'flow_75%_m^3/s'}, inplace=True)

        p25_df = ensemble.quantile(0.25, axis=1).to_frame()
        p25_df.rename(columns={0.25: 'flow_25%_m^3/s'}, inplace=True)

        min_df = ensemble.quantile(0, axis=1).to_frame()
        min_df.rename(columns={0.0: 'flow_min_m^3/s'}, inplace=True)

        mean_df = ensemble.mean(axis=1).to_frame()
        mean_df.rename(columns={0: 'flow_avg_m^3/s'}, inplace=True)

        high_res_df.rename(columns={'ensemble_52_m^3/s': 'high_res_m^3/s'}, inplace=True)

        fixed_stats = pd.concat([max_df, p75_df, mean_df, p25_df, min_df, high_res_df], axis=1)

        forecast_data_bc_file_path = os.path.join(app_workspace.path, 'forecast_data_bc.json')
        fixed_stats.index.name = 'Datetime'
        fixed_stats.to_json(forecast_data_bc_file_path)

        hydroviewer_figure = geoglows.plots.forecast_stats(stats=fixed_stats, titles={'Station': nomEstacion + '-' + str(codEstacion), 'Reach ID': comid, 'bias_corrected': True})

        x_vals = (fixed_stats.index[0], fixed_stats.index[len(fixed_stats.index) - 1], fixed_stats.index[len(fixed_stats.index) - 1], fixed_stats.index[0])
        max_visible = max(fixed_stats.max())

        '''Correct Bias Forecasts Records'''

        date_ini = forecast_record.index[0]
        month_ini = date_ini.month

        date_end = forecast_record.index[-1]
        month_end = date_end.month

        meses = np.arange(month_ini, month_end + 1, 1)

        fixed_records = pd.DataFrame()

        for mes in meses:
            values = forecast_record.loc[forecast_record.index.month == mes]

            monthly_simulated = simulated_df[simulated_df.index.month == mes].dropna()
            monthly_observed = observed_df[observed_df.index.month == mes].dropna()

            min_simulated = np.min(monthly_simulated.iloc[:, 0].to_list())
            max_simulated = np.max(monthly_simulated.iloc[:, 0].to_list())

            min_factor_records_df = values.copy()
            max_factor_records_df = values.copy()
            fixed_records_df = values.copy()

            column_records = values.columns[0]
            tmp = forecast_record[column_records].dropna().to_frame()
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

        record_plot = fixed_records.copy()
        record_plot = record_plot.loc[record_plot.index >= pd.to_datetime(fixed_stats.index[0] - dt.timedelta(days=8))]
        record_plot = record_plot.loc[record_plot.index <= pd.to_datetime(fixed_stats.index[0] + dt.timedelta(days=2))]

        if len(record_plot.index) > 0:
            hydroviewer_figure.add_trace(go.Scatter(
                name='1st days forecasts',
                x=record_plot.index,
                y=record_plot.iloc[:, 0].values,
                line=dict(
                    color='#FFA15A',
                )
            ))

            x_vals = (record_plot.index[0], fixed_stats.index[len(fixed_stats.index) - 1], fixed_stats.index[len(fixed_stats.index) - 1], record_plot.index[0])
            max_visible = max(record_plot.max().values[0], max_visible)

        '''Getting real time observed data'''
        url_rt = 'http://fews.ideam.gov.co/colombia/jsonQ/00' + codEstacion + 'Qobs.json'
        f = requests.get(url_rt, verify=False)

        if f.status_code == 200:
            data = f.json()

            observedDischarge = (data.get('obs'))
            sensorDischarge = (data.get('sen'))

            observedDischarge = (observedDischarge.get('data'))
            sensorDischarge = (sensorDischarge.get('data'))

            datesObservedDischarge = [row[0] for row in observedDischarge]
            observedDischarge = [row[1] for row in observedDischarge]

            datesSensorDischarge = [row[0] for row in sensorDischarge]
            sensorDischarge = [row[1] for row in sensorDischarge]

            dates = []
            discharge = []

            for i in range(0, len(datesObservedDischarge) - 1):
                year = int(datesObservedDischarge[i][0:4])
                month = int(datesObservedDischarge[i][5:7])
                day = int(datesObservedDischarge[i][8:10])
                hh = int(datesObservedDischarge[i][11:13])
                mm = int(datesObservedDischarge[i][14:16])
                dates.append(dt.datetime(year, month, day, hh, mm))
                discharge.append(observedDischarge[i])

            datesObservedDischarge = dates
            observedDischarge = discharge

            dates = []
            discharge = []

            for i in range(0, len(datesSensorDischarge) - 1):
                year = int(datesSensorDischarge[i][0:4])
                month = int(datesSensorDischarge[i][5:7])
                day = int(datesSensorDischarge[i][8:10])
                hh = int(datesSensorDischarge[i][11:13])
                mm = int(datesSensorDischarge[i][14:16])
                dates.append(dt.datetime(year, month, day, hh, mm))
                discharge.append(sensorDischarge[i])

            datesSensorDischarge = dates
            sensorDischarge = discharge

            try:
                # convert request into pandas DF
                pairs = [list(a) for a in zip(datesObservedDischarge, observedDischarge)]
                observed_rt = pd.DataFrame(pairs, columns=['Datetime', 'Observed (m3/s)'])
                observed_rt.set_index('Datetime', inplace=True)
                observed_rt = observed_rt.dropna()
                #observed_rt = observed_rt.groupby(observed_rt.index.strftime("%Y/%m/%d")).mean()
                observed_rt.index = pd.to_datetime(observed_rt.index)
                #observed_rt.index = observed_rt.index.tz_localize('UTC')
                observed_rt = observed_rt.dropna()

                observed_rt_plot = observed_rt.copy()
                observed_rt_plot = observed_rt_plot.loc[observed_rt_plot.index >= pd.to_datetime(forecast_ens.index[0] - dt.timedelta(days=8))]
                observed_rt_plot = observed_rt_plot.loc[observed_rt_plot.index <= pd.to_datetime(forecast_ens.index[0] + dt.timedelta(days=2))]

                if len(observed_rt_plot.index) > 0:
                    hydroviewer_figure.add_trace(go.Scatter(
                        name='Observed Streamflow',
                        x=observed_rt_plot.index,
                        y=observed_rt_plot.iloc[:, 0].values,
                        line=dict(
                            color='green',
                        )
                    ))

                    x_vals = (observed_rt_plot.index[0], forecast_ens.index[len(forecast_ens.index) - 1], forecast_ens.index[len(forecast_ens.index) - 1], observed_rt_plot.index[0])
                    max_visible = max(observed_rt_plot.max().values[0], max_visible)

            except Exception as e:
                print(str(e))

            try:
                # convert request into pandas DF
                pairs = [list(a) for a in zip(datesSensorDischarge, sensorDischarge)]
                sensor_rt = pd.DataFrame(pairs, columns=['Datetime', 'Sensor (m3/s)'])
                sensor_rt.set_index('Datetime', inplace=True)
                sensor_rt = sensor_rt.dropna()
                #sensor_rt = sensor_rt.groupby(sensor_rt.index.strftime("%Y/%m/%d")).mean()
                sensor_rt.index = pd.to_datetime(sensor_rt.index)
                #sensor_rt.index = sensor_rt.index.tz_localize('UTC')
                sensor_rt = sensor_rt.dropna()

                sensor_rt_plot = sensor_rt.copy()
                sensor_rt_plot = sensor_rt_plot.loc[sensor_rt_plot.index >= pd.to_datetime(forecast_ens.index[0] - dt.timedelta(days=8))]
                sensor_rt_plot = sensor_rt_plot.loc[sensor_rt_plot.index <= pd.to_datetime(forecast_ens.index[0] + dt.timedelta(days=2))]

                if len(sensor_rt_plot.index) > 0:
                    hydroviewer_figure.add_trace(go.Scatter(
                        name='Sensor Streamflow',
                        x=sensor_rt_plot.index,
                        y=sensor_rt_plot.iloc[:, 0].values,
                        line=dict(
                            color='yellow',
                        )
                    ))

                    x_vals = (sensor_rt_plot.index[0], forecast_ens.index[len(forecast_ens.index) - 1], forecast_ens.index[len(forecast_ens.index) - 1], sensor_rt_plot.index[0])
                    max_visible = max(sensor_rt_plot.max().values[0], max_visible)

            except Exception as e:
                print(str(e))

        '''Getting Corrected Return Periods'''
        max_annual_flow = corrected_df.groupby(corrected_df.index.strftime("%Y")).max()
        mean_value = np.mean(max_annual_flow.iloc[:,0].values)
        std_value = np.std(max_annual_flow.iloc[:,0].values)

        return_periods = [100, 50, 25, 10, 5, 2]

        def gumbel_1(std: float, xbar: float, rp: int or float) -> float:
            """
            Solves the Gumbel Type I probability distribution function (pdf) = exp(-exp(-b)) where b is the covariate. Provide
            the standard deviation and mean of the list of annual maximum flows. Compare scipy.stats.gumbel_r
            Args:
                std (float): the standard deviation of the series
                xbar (float): the mean of the series
                rp (int or float): the return period in years
            Returns:
                float, the flow corresponding to the return period specified
            """
            # xbar = statistics.mean(year_max_flow_list)
            # std = statistics.stdev(year_max_flow_list, xbar=xbar)
            return -math.log(-math.log(1 - (1 / rp))) * std * .7797 + xbar - (.45 * std)

        return_periods_values = []

        for rp in return_periods:
            return_periods_values.append(gumbel_1(std_value, mean_value, rp))

        d = {'rivid': [comid], 'return_period_100': [return_periods_values[0]], 'return_period_50': [return_periods_values[1]], 'return_period_25': [return_periods_values[2]], 'return_period_10': [return_periods_values[3]], 'return_period_5': [return_periods_values[4]], 'return_period_2': [return_periods_values[5]]}
        rperiods = pd.DataFrame(data=d)
        rperiods.set_index('rivid', inplace=True)

        r2 = int(rperiods.iloc[0]['return_period_2'])

        colors = {
            '2 Year': 'rgba(254, 240, 1, .4)',
            '5 Year': 'rgba(253, 154, 1, .4)',
            '10 Year': 'rgba(255, 56, 5, .4)',
            '20 Year': 'rgba(128, 0, 246, .4)',
            '25 Year': 'rgba(255, 0, 0, .4)',
            '50 Year': 'rgba(128, 0, 106, .4)',
            '100 Year': 'rgba(128, 0, 246, .4)',
        }

        if max_visible > r2:
            visible = True
            hydroviewer_figure.for_each_trace(
                lambda trace: trace.update(visible=True) if trace.name == "Maximum & Minimum Flow" else (),
            )
        else:
            visible = 'legendonly'
            hydroviewer_figure.for_each_trace(
                lambda trace: trace.update(visible=True) if trace.name == "Maximum & Minimum Flow" else (),
            )

        def template(name, y, color, fill='toself'):
            return go.Scatter(
                name=name,
                x=x_vals,
                y=y,
                legendgroup='returnperiods',
                fill=fill,
                visible=visible,
                line=dict(color=color, width=0))

        r5 = int(rperiods.iloc[0]['return_period_5'])
        r10 = int(rperiods.iloc[0]['return_period_10'])
        r25 = int(rperiods.iloc[0]['return_period_25'])
        r50 = int(rperiods.iloc[0]['return_period_50'])
        r100 = int(rperiods.iloc[0]['return_period_100'])

        hydroviewer_figure.add_trace(template('Return Periods', (r100 * 0.05, r100 * 0.05, r100 * 0.05, r100 * 0.05), 'rgba(0,0,0,0)', fill='none'))
        hydroviewer_figure.add_trace(template(f'2 Year: {r2}', (r2, r2, r5, r5), colors['2 Year']))
        hydroviewer_figure.add_trace(template(f'5 Year: {r5}', (r5, r5, r10, r10), colors['5 Year']))
        hydroviewer_figure.add_trace(template(f'10 Year: {r10}', (r10, r10, r25, r25), colors['10 Year']))
        hydroviewer_figure.add_trace(template(f'25 Year: {r25}', (r25, r25, r50, r50), colors['25 Year']))
        hydroviewer_figure.add_trace(template(f'50 Year: {r50}', (r50, r50, r100, r100), colors['50 Year']))
        hydroviewer_figure.add_trace(template(f'100 Year: {r100}', (r100, r100, max(r100 + r100 * 0.05, max_visible), max(r100 + r100 * 0.05, max_visible)), colors['100 Year']))

        chart_obj = PlotlyView(hydroviewer_figure)

        context = {
            'gizmo_object': chart_obj,
        }

        print("--- %s seconds forecasts_bc ---" % (time.time() - start_time))

        return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)


    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })


@controller(
    name='get-available-dates',
    url='ecmwf-rapid/get-available-dates',
)
def get_available_dates(request):

    get_data = request.GET
    watershed = get_data['watershed']
    subbasin = get_data['subbasin']
    comid = get_data['streamcomid']

    res = requests.get('https://geoglows.ecmwf.int/api/AvailableDates/?region=' + watershed + '-' + subbasin, verify=False)

    data = res.json()

    dates_array = (data.get('available_dates'))

    dates = []

    for date in dates_array:
        if len(date) == 10:
            date_mod = date + '000'
            date_f = dt.datetime.strptime(date_mod, '%Y%m%d.%H%M').strftime('%Y-%m-%d %H:%M')
        else:
            date_f = dt.datetime.strptime(date, '%Y%m%d.%H%M').strftime('%Y-%m-%d')
            date = date[:-3]
        dates.append([date_f, date, watershed, subbasin, comid])

    dates.append(['Select Date', dates[-1][1]])
    dates.reverse()

    return JsonResponse({
        "success": "Data analysis complete!",
        "available_dates": json.dumps(dates)
    })


@controller(
    name='get_observed_discharge_csv',
    url='get-observed-discharge-csv',
    app_workspace=True,
)
def get_observed_discharge_csv(request, app_workspace):
    """
    Get observed data from csv files in Hydroshare
    """

    try:
        get_data = request.GET
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        '''Get Observed Data'''
        observed_data_file_path = os.path.join(app_workspace.path, 'observed_data.json')
        observed_df = pd.read_json(observed_data_file_path, convert_dates=True)
        observed_df.index = pd.to_datetime(observed_df.index, unit='ms')
        observed_df.sort_index(inplace=True, ascending=True)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=observed_discharge_{0}.csv'.format(codEstacion)

        observed_df.to_csv(encoding='utf-8', header=True, path_or_buf=response)

        return response

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })
  
@controller(
    name='get_simulated_discharge_csv',
    url='get-simulated-discharge-csv',
    app_workspace=True,
)
def get_simulated_discharge_csv(request, app_workspace):
    """
    Get historic simulations from ERA Interim
    """

    try:
        get_data = request.GET
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        '''Get Simulated Data'''
        simulated_data_file_path = os.path.join(app_workspace.path, 'simulated_data.json')
        simulated_df = pd.read_json(simulated_data_file_path, convert_dates=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.sort_index(inplace=True, ascending=True)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=simulated_discharge_{0}.csv'.format(codEstacion)

        simulated_df.to_csv(encoding='utf-8', header=True, path_or_buf=response)

        return response

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })


@controller(
    name='get_simulated_bc_discharge_csv',
    url='get-simulated-bc-discharge-csv',
    app_workspace=True,
)
def get_simulated_bc_discharge_csv(request, app_workspace):
    """
    Get historic simulations from ERA Interim
    """

    try:

        get_data = request.GET
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        '''Get Bias Corrected Data'''
        corrected_data_file_path = os.path.join(app_workspace.path, 'corrected_data.json')
        corrected_df = pd.read_json(corrected_data_file_path, convert_dates=True)
        corrected_df.index = pd.to_datetime(corrected_df.index)
        corrected_df.sort_index(inplace=True, ascending=True)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=corrected_simulated_discharge_{0}.csv'.format(codEstacion)

        corrected_df.to_csv(encoding='utf-8', header=True, path_or_buf=response)

        return response

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })


@controller(
    name='get_forecast_data_csv',
    url='get-forecast-data-csv',
    app_workspace=True,
)
def get_forecast_data_csv(request):
    """""
    Returns Forecast data as csv
    """""

    try:
        get_data = request.GET
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        startdate = get_data['startdate']

        '''Get Forecast Data'''
        forecast_data_file_path = os.path.join(app_workspace.path, 'forecast_data.json')
        forecast_df = pd.read_json(forecast_data_file_path, convert_dates=True)
        forecast_df.index = pd.to_datetime(forecast_df.index)
        forecast_df.sort_index(inplace=True, ascending=True)

        # Writing CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=streamflow_forecast_{0}_{1}_{2}_{3}.csv'.format(watershed, subbasin, comid, startdate)

        forecast_df.to_csv(encoding='utf-8', header=True, path_or_buf=response)

        return response

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })


@controller(
    name='get_forecast_ensemble_data_csv',
    url='get-forecast-ensemble-data-csv',
    app_workspace=True,
)
def get_forecast_ensemble_data_csv(request, app_workspace):
    """""
    Returns Forecast data as csv
    """""

    get_data = request.GET

    try:
        #get station attributes
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        startdate = get_data['startdate']

        '''Get Forecast Ensemble Data'''
        forecast_ens_file_path = os.path.join(app_workspace.path, 'forecast_ens.json')
        forecast_ens = pd.read_json(forecast_ens_file_path, convert_dates=True)
        forecast_ens.index = pd.to_datetime(forecast_ens.index)
        forecast_ens.sort_index(inplace=True, ascending=True)

        # Writing CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=streamflow_ensemble_forecast_{0}_{1}_{2}_{3}.csv'.format(watershed, subbasin, comid, startdate)

        forecast_ens.to_csv(encoding='utf-8', header=True, path_or_buf=response)

        return response

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
                'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })


@controller(
    name='get_forecast_bc_data_csv',
    url='get-forecast-bc-data-csv',
    app_workspace=True,
)
def get_forecast_bc_data_csv(request, app_workspace):
    """""
    Returns Forecast data as csv
    """""

    try:

        get_data = request.GET
        # get station attributes
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        startdate = get_data['startdate']

        '''Get Bias-Corrected Forecast Data'''
        forecast_data_bc_file_path = os.path.join(app_workspace.path, 'forecast_data_bc.json')
        fixed_stats = pd.read_json(forecast_data_bc_file_path, convert_dates=True)
        fixed_stats.index = pd.to_datetime(fixed_stats.index)
        fixed_stats.sort_index(inplace=True, ascending=True)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=corrected_streamflow_forecast_{0}_{1}_{2}_{3}.csv'.format(watershed, subbasin, comid, startdate)

        fixed_stats.to_csv(encoding='utf-8', header=True, path_or_buf=response)

        return response


    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))
        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })


@controller(
    name='get_forecast_ensemble_bc_data_csv',
    url='get-forecast-ensemble-bc-data-csv',
    app_workspace=True,
)
def get_forecast_ensemble_bc_data_csv(request, app_workspace):
    """""
    Returns Forecast data as csv
    """""

    get_data = request.GET

    try:
        # get station attributes
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['streamcomid']
        startdate = get_data['startdate']

        '''Get Forecast Ensemble Data'''
        forecast_ens_bc_file_path = os.path.join(app_workspace.path, 'forecast_ens_bc.json')
        corrected_ensembles = pd.read_json(forecast_ens_bc_file_path, convert_dates=True)
        corrected_ensembles.index = pd.to_datetime(corrected_ensembles.index)
        corrected_ensembles.sort_index(inplace=True, ascending=True)

        # Writing CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=corrected_streamflow_ensemble_forecast_{0}_{1}_{2}_{3}.csv'.format(watershed, subbasin, comid, startdate)

        corrected_ensembles.to_csv(encoding='utf-8', header=True, path_or_buf=response)

        return response

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("error: " + str(e))
        print("line: " + str(exc_tb.tb_lineno))

        return JsonResponse({
            'error': f'{"error: " + str(e), "line: " + str(exc_tb.tb_lineno)}',
        })