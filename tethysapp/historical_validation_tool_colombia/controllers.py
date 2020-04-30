from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import PlotlyView
from django.http import HttpResponse, JsonResponse

import pandas as pd
import io
import math
import requests
import json
import numpy as np
import datetime as dt
import plotly.graph_objs as go
import hydrostats as hs
import hydrostats.data as hd
from HydroErr.HydroErr import metric_names, metric_abbr
import scipy.stats as sp
from scipy import integrate
from scipy import interpolate
from functools import reduce
import traceback
from csv import writer as csv_writer


def home(request):
	"""
    Controller for the app home page.
    """

	# List of Metrics to include in context
	metric_loop_list = list(zip(metric_names, metric_abbr))

	context = {
		"metric_loop_list": metric_loop_list
	}

	return render(request, 'historical_validation_tool_colombia/home.html', context)


def get_discharge_data(request):
	"""
    Get observed data from csv files in Hydroshare
    """

	get_data = request.GET

	try:

		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(
			codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_Q = go.Scatter(
			x=datesDischarge,
			y=dataDischarge,
			name='Observed Discharge',
			line=dict(color='#636efa')
		)

		layout = go.Layout(title='Observed Streamflow {0}-{1}'.format(nomEstacion, codEstacion),
		                   xaxis=dict(title='Dates', ), yaxis=dict(title='Discharge (m<sup>3</sup>/s)',
		                                                           autorange=True), showlegend=False)

		chart_obj = PlotlyView(go.Figure(data=[observed_Q], layout=layout))

		context = {
			'gizmo_object': chart_obj,
		}

		return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No observed data found for the selected station.'})


def get_simulated_data(request):
	"""
    Get simulated data from api
    """

	try:
		get_data = request.GET
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		# ----------------------------------------------
		# Chart Section
		# ----------------------------------------------

		simulated_Q = go.Scatter(
			name='Simulated Discharge',
			x=era_dates,
			y=era_values,
			line=dict(color='#ef553b')
		)

		layout = go.Layout(
			title="Simulated Streamflow at <br> {0}".format(nomEstacion),
			xaxis=dict(title='Date', ), yaxis=dict(title='Discharge (m<sup>3</sup>/s)'),
		)

		chart_obj = PlotlyView(go.Figure(data=[simulated_Q], layout=layout))

		context = {
			'gizmo_object': chart_obj,
		}

		return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No simulated data found for the selected station.'})


def get_simulated_bc_data(request):
	"""
    Calculate corrected simulated data
    """
	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(
			codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

		# ----------------------------------------------
		# Chart Section
		# ----------------------------------------------

		corrected_Q = go.Scatter(
			name='Corrected Simulated Discharge',
			x=dates,
			y=values,
			line=dict(color='#00cc96')
		)

		layout = go.Layout(
			title="Corrected Simulated Streamflow at <br> {0}".format(nomEstacion),
			xaxis=dict(title='Date', ), yaxis=dict(title='Discharge (m<sup>3</sup>/s)'),
		)

		chart_obj = PlotlyView(go.Figure(data=[corrected_Q], layout=layout))

		context = {
			'gizmo_object': chart_obj,
		}

		return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No simulated data found for the selected station.'})


def get_hydrographs(request):
	"""
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """
	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(
			codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

		'''Merge Data'''

		merged_df = hd.merge_data(sim_df=simulated_df, obs_df=observed_df)

		merged_df2 = hd.merge_data(sim_df=corrected_df, obs_df=observed_df)

		'''Plotting Data'''

		observed_Q = go.Scatter(x=merged_df.index, y=merged_df.iloc[:, 1].values, name='Observed', )

		simulated_Q = go.Scatter(x=merged_df.index, y=merged_df.iloc[:, 0].values, name='Simulated', )

		corrected_Q = go.Scatter(x=merged_df2.index, y=merged_df2.iloc[:, 0].values, name='Corrected Simulated', )

		layout = go.Layout(
			title='Observed & Simulated Streamflow at <br> {0} - {1}'.format(codEstacion, nomEstacion),
			xaxis=dict(title='Dates', ), yaxis=dict(title='Discharge (m<sup>3</sup>/s)', autorange=True),
			showlegend=True)

		chart_obj = PlotlyView(go.Figure(data=[observed_Q, simulated_Q, corrected_Q], layout=layout))

		context = {
			'gizmo_object': chart_obj,
		}

		return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No data found for the selected station.'})

def get_hydro_stats(request):
    print("entered the get_hydro_stats function")
    ## daily Average ##
    chart_obj_DA = get_dailyAverages2(request)
    # print(chart_obj_DA)
    chart_obj_MA = get_monthlyAverages2(request)
    # print(chart_obj_MA)
    chart_obj_SP = get_scatterPlot2(request)
    chart_obj_VA = get_volumeAnalysis2(request)
    ## Monthly Average ##
    ## Scatter Plot ##

    new_context={
        'gizmo_object_daily_average': chart_obj_DA,
        'gizmo_object_monthly_average': chart_obj_MA,
        'gizmo_object_scatterplot': chart_obj_SP,
		'gizmo_volume_analysis': chart_obj_VA
    }
    # new_context={
    #     'hola': "holass"
    # }
    # context  ={}
    # print(" printing context of get_hydrotest .....")
    # print(context)
    return JsonResponse(new_context)
    # return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)


def get_dailyAverages2(request):
	"""
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """
	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(
			codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

		'''Merge Data'''

		merged_df = hd.merge_data(sim_df=simulated_df, obs_df=observed_df)

		merged_df2 = hd.merge_data(sim_df=corrected_df, obs_df=observed_df)

		'''Plotting Data'''

		daily_avg = hd.daily_average(merged_df)

		daily_avg2 = hd.daily_average(merged_df2)
		print(type(daily_avg.iloc[:, 1].values))
        #
		# daily_avg_obs_Q = go.Scatter(x=daily_avg.index, y=daily_avg.iloc[:, 1].values, name='Observed', )
		# daily_avg_sim_Q = go.Scatter(x=daily_avg.index, y=daily_avg.iloc[:, 0].values, name='Simulated', )
		# daily_avg_corr_sim_Q = go.Scatter(x=daily_avg2.index, y=daily_avg2.iloc[:, 0].values,
		#                                   name='Corrected Simulated', )
		# layout = go.Layout(
		# 	title='Daily Average Streamflow for <br> {0} - {1}'.format(codEstacion, nomEstacion),
		# 	xaxis=dict(title='Days', ), yaxis=dict(title='Discharge (m<sup>3</sup>/s)', autorange=True),
		# 	showlegend=True)
        #

		daily_avg_obs_Q = {
            "x": daily_avg.index.tolist(),
            "y":daily_avg.iloc[:, 1].values.tolist(),
            "name":'Observed'
        }
		daily_avg_sim_Q = {
            "x": daily_avg.index.tolist(),
            "y":daily_avg.iloc[:, 0].values.tolist(),
            "name":'Simulated'
        }
		daily_avg_corr_sim_Q = {
            "x": daily_avg2.index.tolist(),
            "y":daily_avg2.iloc[:, 0].values.tolist(),
            "name":'Corrected Simulated'
        }
		layout = {
            "title": "Daily Average Streamflow",
            "codEstacion" : codEstacion,
            "nomEstacion" : nomEstacion,
            "xaxis":"Days",
            "yaxis":'Discharge (m<sup>3</sup>/s)',
            "autorange":"true"
        }
		chart_obj = {
            "data": [daily_avg_obs_Q, daily_avg_sim_Q, daily_avg_corr_sim_Q],
            # "data": daily_avg_obs_Q,
            "layout":layout
        }


		# chart_obj = PlotlyView(go.Figure(data=[daily_avg_obs_Q, daily_avg_sim_Q, daily_avg_corr_sim_Q], layout=layout))

		return chart_obj

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No data found for the selected station.'})

def get_dailyAverages(request):
	"""
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """
	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(
			codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

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

		return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No data found for the selected station.'})

def get_monthlyAverages2(request):
	"""
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """
	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(
			codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

		'''Merge Data'''

		merged_df = hd.merge_data(sim_df=simulated_df, obs_df=observed_df)

		merged_df2 = hd.merge_data(sim_df=corrected_df, obs_df=observed_df)

		'''Plotting Data'''

		monthly_avg = hd.monthly_average(merged_df)

		monthly_avg2 = hd.monthly_average(merged_df2)

		# monthly_avg_obs_Q = go.Scatter(x=monthly_avg.index, y=monthly_avg.iloc[:, 1].values, name='Observed', )
        #
		# monthly_avg_sim_Q = go.Scatter(x=monthly_avg.index, y=monthly_avg.iloc[:, 0].values, name='Simulated', )
        #
		# monthly_avg_corr_sim_Q = go.Scatter(x=monthly_avg2.index, y=monthly_avg2.iloc[:, 0].values,
		#                                     name='Corrected Simulated', )
        #
		# layout = go.Layout(
		# 	title='Monthly Average Streamflow for <br> {0} - {1}'.format(codEstacion, nomEstacion),
		# 	xaxis=dict(title='Months', ), yaxis=dict(title='Discharge (m<sup>3</sup>/s)', autorange=True),
		# 	showlegend=True)

		monthly_avg_obs_Q = {
            "x": monthly_avg.index.tolist(),
            "y":monthly_avg.iloc[:, 1].values.tolist(),
            "name":'Observed'
        }
		monthly_avg_sim_Q = {
            "x": monthly_avg.index.tolist(),
            "y":monthly_avg.iloc[:, 0].values.tolist(),
            "name":'Simulated'
        }
		monthly_avg_corr_sim_Q = {
            "x": monthly_avg2.index.tolist(),
            "y":monthly_avg2.iloc[:, 0].values.tolist(),
            "name":'Corrected Simulated'
        }
		layout = {
            "title": "monthly Average Streamflow",
            "codEstacion" : codEstacion,
            "nomEstacion" : nomEstacion,
            "xaxis":"Days",
            "yaxis":'Discharge (m<sup>3</sup>/s)',
            "autorange":"true"
        }

		chart_obj = {
            "data": [monthly_avg_obs_Q, monthly_avg_sim_Q, monthly_avg_corr_sim_Q],
            # "data": daily_avg_obs_Q,
            "layout":layout
        }

		# chart_obj = PlotlyView(
		# 	go.Figure(data=[monthly_avg_obs_Q, monthly_avg_sim_Q, monthly_avg_corr_sim_Q], layout=layout))

		return chart_obj

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No data found for the selected station.'})

def get_monthlyAverages(request):
	"""
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """
	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(
			codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

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

		return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No data found for the selected station.'})

def get_scatterPlot2(request):
	"""
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """
	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(
			codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

		'''Merge Data'''

		merged_df = hd.merge_data(sim_df=simulated_df, obs_df=observed_df)

		merged_df2 = hd.merge_data(sim_df=corrected_df, obs_df=observed_df)

		'''Plotting Data'''

		# scatter_data = go.Scatter(
		# 	x=merged_df.iloc[:, 0].values,
		# 	y=merged_df.iloc[:, 1].values,
		# 	mode='markers',
		# 	name='original',
		# 	marker=dict(color='#ef553b')
		# )
		scatter_data = {
			"x" : merged_df.iloc[:, 0].values.tolist(),
			"y" :merged_df.iloc[:, 1].values.tolist(),
			"mode" : 'markers',
			"name" :'original',
			"marker" : dict(color='#ef553b')
		}

		# scatter_data2 = go.Scatter(
		# 	x=merged_df2.iloc[:, 0].values,
		# 	y=merged_df2.iloc[:, 1].values,
		# 	mode='markers',
		# 	name='corrected',
		# 	marker=dict(color='#00cc96')
		# )
		scatter_data2 = {
			"x" : merged_df2.iloc[:, 0].values.tolist(),
			"y" :merged_df2.iloc[:, 1].values.tolist(),
			"mode" : 'markers',
			"name" :'corrected',
			"marker" : dict(color='#00cc96')
		}

		min_value = min(min(merged_df.iloc[:, 1].values), min(merged_df.iloc[:, 0].values))
		max_value = max(max(merged_df.iloc[:, 1].values), max(merged_df.iloc[:, 0].values))

		min_value2 = min(min(merged_df2.iloc[:, 1].values), min(merged_df2.iloc[:, 0].values))
		max_value2 = max(max(merged_df2.iloc[:, 1].values), max(merged_df2.iloc[:, 0].values))

		# line_45 = go.Scatter(
		# 	x=[min_value, max_value],
		# 	y=[min_value, max_value],
		# 	mode='lines',
		# 	name='45deg line',
		# 	line=dict(color='black')
		# )
		line_45 = {
			"x": [np.float(min_value), np.float(max_value)],
			"y": [np.float(min_value), np.float(max_value)],
			"mode":'lines',
			"name" :'45deg line',
			"line" : dict(color='black')
		}

		slope, intercept, r_value, p_value, std_err = sp.linregress(merged_df.iloc[:, 0].values,
		                                                            merged_df.iloc[:, 1].values)

		slope2, intercept2, r_value2, p_value2, std_err2 = sp.linregress(merged_df2.iloc[:, 0].values,
		                                                                 merged_df2.iloc[:, 1].values)

		# line_adjusted = go.Scatter(
		# 	x=[min_value, max_value],
		# 	y=[slope * min_value + intercept, slope * max_value + intercept],
		# 	mode='lines',
		# 	name='{0}x + {1} (Original)'.format(str(round(slope, 2)), str(round(intercept, 2))),
		# 	line=dict(color='red')
		# )
		line_adjusted = {
			"x": [np.float(min_value), np.float(max_value)],
			"y": [np.float(slope * min_value + intercept), np.float(slope * max_value + intercept)],
			"mode":'lines',
			"name":'{0}x + {1} (Original)'.format(str(round(slope, 2)), str(round(intercept, 2))),
			"line":dict(color='red')
		}
		line_adjusted2 = {
			"x": [np.float(min_value), np.float(max_value)],
			"y": [np.float(slope2 * min_value + intercept2), np.float(slope2 * max_value + intercept2)],
			"mode":'lines',
			"name":'{0}x + {1} (Original)'.format(str(round(slope2, 2)), str(round(intercept2, 2))),
			"line":dict(color='red')
		}

		# line_adjusted2 = go.Scatter(
		# 	x=[min_value, max_value],
		# 	y=[slope2 * min_value + intercept2, slope2 * max_value + intercept2],
		# 	mode='lines',
		# 	name='{0}x + {1} (Corrected)'.format(str(round(slope2, 2)), str(round(intercept2, 2))),
		# 	line=dict(color='green')
		# )

		# layout = go.Layout(title="Scatter Plot for {0} - {1}".format(codEstacion, nomEstacion),
		#                    xaxis=dict(title='Simulated', ), yaxis=dict(title='Observed', autorange=True),
		#                    showlegend=True)

		layout = {
            "title": "Scatter Plot",
            "codEstacion" : codEstacion,
            "nomEstacion" : nomEstacion,
            "xaxis":"Simulated",
            "yaxis":'Observed',
            "autorange":"true",
			"showlegend":"true"
        }

		chart_obj = {
            "data": [scatter_data, scatter_data2, line_45, line_adjusted, line_adjusted2],
            # "data": daily_avg_obs_Q,
            "layout":layout
        }


		# chart_obj = PlotlyView(
		# 	go.Figure(data=[scatter_data, scatter_data2, line_45, line_adjusted, line_adjusted2], layout=layout))

		return chart_obj


	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No data found for the selected station.'})

def get_scatterPlot(request):
	"""
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """
	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(
			codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

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
		print("testing")
		print(type(slope))
		print(type(min_value))
		return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No data found for the selected station.'})


def get_scatterPlotLogScale2(request):
	"""
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """
	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(
			codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

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

		return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No data found for the selected station.'})
def get_scatterPlotLogScale(request):
	"""
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """
	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(
			codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

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

		return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No data found for the selected station.'})


def get_volumeAnalysis2(request):
	"""
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """
	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(
			codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

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

		# observed_volume = go.Scatter(x=merged_df.index, y=obs_volume_cum, name='Observed', )
		# simulated_volume = go.Scatter(x=merged_df.index, y=sim_volume_cum, name='Simulated', )
		# corrected_volume = go.Scatter(x=merged_df2.index, y=corr_volume_cum, name='Corrected Simulated', )
		# layout = go.Layout(
		# 	title='Observed & Simulated Volume at<br> {0} - {1}'.format(codEstacion, nomEstacion),
		# 	xaxis=dict(title='Dates', ), yaxis=dict(title='Volume (Mm<sup>3</sup>)', autorange=True),
		# 	showlegend=True)
		# chart_obj = PlotlyView(go.Figure(data=[observed_volume, simulated_volume, corrected_volume], layout=layout))
		#
		print(type(obs_volume_cum))
		print(type(sim_volume_cum))
		observed_volume = {
			"x":merged_df.index.tolist(),
			"y":obs_volume_cum,
			"name":'Observed'
		}

		simulated_volume = {
			"x":merged_df.index.tolist(),
			"y":sim_volume_cum,
			"name":'Simulated'
		}
		corrected_volume = {
			"x":merged_df2.index.tolist(),
			"y":corr_volume_cum,
			"name":'Corrected Simulated'
		}
		layout = {
            "title": "Observed & Simulated Volume",
            "codEstacion" : codEstacion,
            "nomEstacion" : nomEstacion,
            "xaxis":"Dates",
            "yaxis":'Volume (Mm<sup>3</sup>)',
            "autorange":"true",
			"showlegend":"true"
        }
		chart_obj = {
            "data": [observed_volume, simulated_volume,corrected_volume],
            "layout":layout
        }


		return chart_obj

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No data found for the selected station.'})
def get_volumeAnalysis(request):
	"""
    Get observed data from csv files in Hydroshare
    Get historic simulations from ERA Interim
    """
	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(
			codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

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

		context = {
			'gizmo_object': chart_obj,
		}

		return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No data found for the selected station.'})


def volume_table_ajax(request):
	"""Calculates the volumes of the simulated and observed streamflow"""

	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

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

		return JsonResponse(resp)

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No data found for the selected station.'})


def make_table_ajax(request):
	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		# Indexing the metrics to get the abbreviations
		selected_metric_abbr = get_data.getlist("metrics[]", None)

		# print(selected_metric_abbr)

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

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

		'''Merge Data'''

		merged_df = hd.merge_data(sim_df=simulated_df, obs_df=observed_df)

		merged_df2 = hd.merge_data(sim_df=corrected_df, obs_df=observed_df)

		'''Plotting Data'''

		# Creating the Table Based on User Input
		table = hs.make_table(
			merged_dataframe=merged_df,
			metrics=selected_metric_abbr,
			# remove_neg=remove_neg,
			# remove_zero=remove_zero,
			mase_m=extra_param_dict['mase_m'],
			dmod_j=extra_param_dict['dmod_j'],
			nse_mod_j=extra_param_dict['nse_mod_j'],
			h6_mhe_k=extra_param_dict['h6_mhe_k'],
			h6_ahe_k=extra_param_dict['h6_ahe_k'],
			h6_rmshe_k=extra_param_dict['h6_rmshe_k'],
			d1_p_obs_bar_p=extra_param_dict['d1_p_x_bar_p'],
			lm_x_obs_bar_p=extra_param_dict['lm_x_bar_p'],
			# seasonal_periods=all_date_range_list
		)
		table_html = table.transpose()
		table_html = table_html.to_html(classes="table table-hover table-striped").replace('border="1"', 'border="0"')

		# Creating the Table Based on User Input
		table2 = hs.make_table(
			merged_dataframe=merged_df2,
			metrics=selected_metric_abbr,
			# remove_neg=remove_neg,
			# remove_zero=remove_zero,
			mase_m=extra_param_dict['mase_m'],
			dmod_j=extra_param_dict['dmod_j'],
			nse_mod_j=extra_param_dict['nse_mod_j'],
			h6_mhe_k=extra_param_dict['h6_mhe_k'],
			h6_ahe_k=extra_param_dict['h6_ahe_k'],
			h6_rmshe_k=extra_param_dict['h6_rmshe_k'],
			d1_p_obs_bar_p=extra_param_dict['d1_p_x_bar_p'],
			lm_x_obs_bar_p=extra_param_dict['lm_x_bar_p'],
			# seasonal_periods=all_date_range_list
		)
		table_html2 = table2.transpose()
		table_html2 = table_html2.to_html(classes="table table-hover table-striped").replace('border="1"', 'border="0"')

		return HttpResponse(table_html)

	except Exception:
		traceback.print_exc()
		return JsonResponse({'error': 'No data found for the selected station.'})


def make_table_ajax2(request):
	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		# Indexing the metrics to get the abbreviations
		selected_metric_abbr = get_data.getlist("metrics[]", None)

		# print(selected_metric_abbr)

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

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

		'''Merge Data'''

		merged_df = hd.merge_data(sim_df=simulated_df, obs_df=observed_df)

		merged_df2 = hd.merge_data(sim_df=corrected_df, obs_df=observed_df)

		'''Plotting Data'''

		# Creating the Table Based on User Input
		table = hs.make_table(
			merged_dataframe=merged_df,
			metrics=selected_metric_abbr,
			# remove_neg=remove_neg,
			# remove_zero=remove_zero,
			mase_m=extra_param_dict['mase_m'],
			dmod_j=extra_param_dict['dmod_j'],
			nse_mod_j=extra_param_dict['nse_mod_j'],
			h6_mhe_k=extra_param_dict['h6_mhe_k'],
			h6_ahe_k=extra_param_dict['h6_ahe_k'],
			h6_rmshe_k=extra_param_dict['h6_rmshe_k'],
			d1_p_obs_bar_p=extra_param_dict['d1_p_x_bar_p'],
			lm_x_obs_bar_p=extra_param_dict['lm_x_bar_p'],
			# seasonal_periods=all_date_range_list
		)
		table_html = table.transpose()
		table_html = table_html.to_html(classes="table table-hover table-striped").replace('border="1"', 'border="0"')

		# Creating the Table Based on User Input
		table2 = hs.make_table(
			merged_dataframe=merged_df2,
			metrics=selected_metric_abbr,
			# remove_neg=remove_neg,
			# remove_zero=remove_zero,
			mase_m=extra_param_dict['mase_m'],
			dmod_j=extra_param_dict['dmod_j'],
			nse_mod_j=extra_param_dict['nse_mod_j'],
			h6_mhe_k=extra_param_dict['h6_mhe_k'],
			h6_ahe_k=extra_param_dict['h6_ahe_k'],
			h6_rmshe_k=extra_param_dict['h6_rmshe_k'],
			d1_p_obs_bar_p=extra_param_dict['d1_p_x_bar_p'],
			lm_x_obs_bar_p=extra_param_dict['lm_x_bar_p'],
			# seasonal_periods=all_date_range_list
		)
		table_html2 = table2.transpose()
		table_html2 = table_html2.to_html(classes="table table-hover table-striped").replace('border="1"', 'border="0"')

		return HttpResponse(table_html2)

	except Exception:
		traceback.print_exc()
		return JsonResponse({'error': 'No data found for the selected station.'})


def get_units_title(unit_type):
	"""
    Get the title for units
    """
	units_title = "m"
	if unit_type == 'english':
		units_title = "ft"
	return units_title


def get_available_dates(request):
	get_data = request.GET

	watershed = get_data['watershed']
	subbasin = get_data['subbasin']
	comid = get_data['streamcomid']

	# request_params
	request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid)

	# Token is for the demo account
	request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

	res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetAvailableDates/',
	                   params=request_params, headers=request_headers)

	dates = []
	for date in eval(res.content):
		if len(date) == 10:
			date_mod = date + '000'
			date_f = dt.datetime.strptime(date_mod, '%Y%m%d.%H%M').strftime('%Y-%m-%d %H:%M')
		else:
			date_f = dt.datetime.strptime(date, '%Y%m%d.%H%M').strftime('%Y-%m-%d %H:%M')
		dates.append([date_f, date, watershed, subbasin, comid])

	dates.append(['Select Date', dates[-1][1]])
	dates.reverse()

	return JsonResponse({
		"success": "Data analysis complete!",
		"available_dates": json.dumps(dates)
	})


def get_time_series(request):
	get_data = request.GET
	try:
		# model = get_data['model']
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		if get_data['startdate'] != '':
			startdate = get_data['startdate']
		else:
			startdate = 'most_recent'
		units = 'metric'

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid,
		                      forecast_folder=startdate, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetForecast/',
		                   params=request_params, headers=request_headers)

		pairs = res.content.splitlines()
		header = pairs.pop(0)

		dates = []
		hres_dates = []

		mean_values = []
		hres_values = []
		min_values = []
		max_values = []
		std_dev_lower_values = []
		std_dev_upper_values = []

		for pair in pairs:
			pair = pair.decode('utf-8')
			if b'high_res' in header:
				hres_dates.append(dt.datetime.strptime(pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
				hres_values.append(float(pair.split(',')[1]))

				if 'nan' not in pair:
					dates.append(dt.datetime.strptime(pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
					max_values.append(float(pair.split(',')[2]))
					mean_values.append(float(pair.split(',')[3]))
					min_values.append(float(pair.split(',')[4]))
					std_dev_lower_values.append(float(pair.split(',')[5]))
					std_dev_upper_values.append(float(pair.split(',')[6]))

			else:
				dates.append(dt.datetime.strptime(pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
				max_values.append(float(pair.split(',')[1]))
				mean_values.append(float(pair.split(',')[2]))
				min_values.append(float(pair.split(',')[3]))
				std_dev_lower_values.append(float(pair.split(',')[4]))
				std_dev_upper_values.append(float(pair.split(',')[5]))

		# Removing Negative Values
		mean_values2 = [0 if i < 0 else i for i in mean_values]
		mean_values = mean_values2
		hres_values2 = [0 if i < 0 else i for i in hres_values]
		hres_values = hres_values2
		min_values2 = [0 if i < 0 else i for i in min_values]
		min_values = min_values2
		max_values2 = [0 if i < 0 else i for i in max_values]
		max_values = max_values2
		std_dev_lower_values2 = [0 if i < 0 else i for i in std_dev_lower_values]
		std_dev_lower_values = std_dev_lower_values2
		std_dev_upper_values2 = [0 if i < 0 else i for i in std_dev_upper_values]
		std_dev_upper_values = std_dev_upper_values2

		# ----------------------------------------------
		# Chart Section
		# ----------------------------------------------

		datetime_start = dates[0]
		datetime_end = dates[-1]

		avg_series = go.Scatter(
			name='Mean',
			x=dates,
			y=mean_values,
			line=dict(
				color='blue',
			)
		)

		max_series = go.Scatter(
			name='Max',
			x=dates,
			y=max_values,
			fill='tonexty',
			mode='lines',
			line=dict(
				color='rgb(152, 251, 152)',
				width=0,
			)
		)

		min_series = go.Scatter(
			name='Min',
			x=dates,
			y=min_values,
			fill=None,
			mode='lines',
			line=dict(
				color='rgb(152, 251, 152)',
			)
		)

		std_dev_lower_series = go.Scatter(
			name='Std. Dev. Lower',
			x=dates,
			y=std_dev_lower_values,
			fill='tonexty',
			mode='lines',
			line=dict(
				color='rgb(152, 251, 152)',
				width=0,
			)
		)

		std_dev_upper_series = go.Scatter(
			name='Std. Dev. Upper',
			x=dates,
			y=std_dev_upper_values,
			fill='tonexty',
			mode='lines',
			line=dict(
				width=0,
				color='rgb(34, 139, 34)',
			)
		)

		plot_series = [min_series,
		               std_dev_lower_series,
		               std_dev_upper_series,
		               max_series,
		               avg_series]

		if hres_values:
			plot_series.append(go.Scatter(
				name='HRES',
				x=hres_dates,
				y=hres_values,
				line=dict(
					color='black',
				)
			))

		try:
			return_shapes, return_annotations = get_return_period_ploty_info(request, datetime_start, datetime_end)
		except:
			return_annotations = []
			return_shapes = []

		layout = go.Layout(
			title="Forecast<br><sub>{0} ({1}): {2}</sub>".format(
				watershed, subbasin, comid),
			xaxis=dict(
				title='Date',
			),
			yaxis=dict(
				title='Streamflow ({}<sup>3</sup>/s)'.format(get_units_title(units)),
				range=[0, max(max_values) + max(max_values) / 5]
			),
			shapes=return_shapes,
			annotations=return_annotations
		)

		chart_obj = PlotlyView(
			go.Figure(data=plot_series,
			          layout=layout)
		)

		context = {
			'gizmo_object': chart_obj,
		}

		return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No data found for the selected reach.'})


def get_time_series_bc(request):
	get_data = request.GET
	try:
		# model = get_data['model']
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		if get_data['startdate'] != '':
			startdate = get_data['startdate']
		else:
			startdate = 'most_recent'
		units = 'metric'
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(
			codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Get Forecast'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid,
		                      forecast_folder=startdate, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetForecast/',
		                   params=request_params, headers=request_headers)

		pairs = res.content.splitlines()
		header = pairs.pop(0)

		dates = []
		hres_dates = []

		mean_values = []
		hres_values = []
		min_values = []
		max_values = []
		std_dev_lower_values = []
		std_dev_upper_values = []

		for pair in pairs:
			pair = pair.decode('utf-8')
			if b'high_res' in header:
				hres_dates.append(dt.datetime.strptime(pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
				hres_values.append(float(pair.split(',')[1]))

				if 'nan' not in pair:
					dates.append(dt.datetime.strptime(pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
					max_values.append(float(pair.split(',')[2]))
					mean_values.append(float(pair.split(',')[3]))
					min_values.append(float(pair.split(',')[4]))
					std_dev_lower_values.append(float(pair.split(',')[5]))
					std_dev_upper_values.append(float(pair.split(',')[6]))

			else:
				dates.append(dt.datetime.strptime(pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
				max_values.append(float(pair.split(',')[1]))
				mean_values.append(float(pair.split(',')[2]))
				min_values.append(float(pair.split(',')[3]))
				std_dev_lower_values.append(float(pair.split(',')[4]))
				std_dev_upper_values.append(float(pair.split(',')[5]))

		# Removing Negative Values
		mean_values2 = [0 if i < 0 else i for i in mean_values]
		mean_values = mean_values2
		hres_values2 = [0 if i < 0 else i for i in hres_values]
		hres_values = hres_values2
		min_values2 = [0 if i < 0 else i for i in min_values]
		min_values = min_values2
		max_values2 = [0 if i < 0 else i for i in max_values]
		max_values = max_values2
		std_dev_lower_values2 = [0 if i < 0 else i for i in std_dev_lower_values]
		std_dev_lower_values = std_dev_lower_values2
		std_dev_upper_values2 = [0 if i < 0 else i for i in std_dev_upper_values]
		std_dev_upper_values = std_dev_upper_values2

		mean_forecast = pd.DataFrame(np.array(mean_values), columns=['streamflow (m3/s)'], index=dates)
		max_forecast = pd.DataFrame(np.array(max_values), columns=['streamflow (m3/s)'], index=dates)
		min_forecast = pd.DataFrame(np.array(min_values), columns=['streamflow (m3/s)'], index=dates)
		std_dev_lower_forecast = pd.DataFrame(np.array(std_dev_lower_values), columns=['streamflow (m3/s)'],
		                                      index=dates)
		std_dev_upper_forecast = pd.DataFrame(np.array(std_dev_upper_values), columns=['streamflow (m3/s)'],
		                                      index=dates)

		high_res_forecast = pd.DataFrame(np.array(hres_values), columns=['streamflow (m3/s)'], index=hres_dates)

		'''Correct Forecast'''

		iniDate = mean_forecast.index[0]
		monIdx = iniDate.month

		# filter historic data to only be current month
		monData = simulated_df[simulated_df.index.month.isin([monIdx])]
		# filter the observations to current month
		monObs = observed_df[observed_df.index.month.isin([monIdx])]

		# get maximum value to bound histogram
		obs_tempMax = np.max(monObs.max())
		sim_tempMax = np.max(monData.max())
		obs_tempMin = np.min(monObs.min())
		sim_tempMin = np.min(monData.min())

		obs_maxVal = math.ceil(obs_tempMax)
		sim_maxVal = math.ceil(sim_tempMax)
		obs_minVal = math.floor(obs_tempMin)
		sim_minVal = math.floor(sim_tempMin)

		n_elementos_obs = len(monObs.iloc[:, 0].values)
		n_elementos_sim = len(monData.iloc[:, 0].values)

		n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
		n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

		# specify the bin width for histogram (in m3/s)
		step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
		step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

		# specify histogram bins
		bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
		bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

		if (bins_obs[0] == 0):
			bins_obs = np.concatenate((-bins_obs[1], bins_obs))
		elif (bins_obs[0] > 0):
			bins_obs = np.concatenate((-bins_obs[0], bins_obs))

		if (bins_sim[0] >= 0):
			bins_sim = np.concatenate((-bins_sim[1], bins_sim))
		elif (bins_sim[0] > 0):
			bins_sim = np.concatenate((-bins_sim[0], bins_sim))

		# get the histograms
		sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
		obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

		# adjust the bins to be the center
		bin_edges_sim = bin_edges_sim[1:]
		bin_edges_obs = bin_edges_obs[1:]

		# normalize the histograms
		sim_counts = sim_counts.astype(float) / monData.size
		obs_counts = obs_counts.astype(float) / monObs.size

		# calculate the cdfs
		simcdf = np.cumsum(sim_counts)
		obscdf = np.cumsum(obs_counts)

		# interpolated function to convert simulated streamflow to prob
		f = interpolate.interp1d(bin_edges_sim, simcdf, fill_value="extrapolate")

		# interpolated function to convert simulated prob to observed streamflow
		backout = interpolate.interp1d(obscdf, bin_edges_obs, fill_value="extrapolate")

		# Fixing the forecast
		fixed_dates = mean_forecast.index.to_list()
		fixed_mean_values = backout(f(mean_forecast.iloc[:, 0].to_list()))
		fixed_mean_values = fixed_mean_values.tolist()
		fixed_max_values = backout(f(max_forecast.iloc[:, 0].to_list()))
		fixed_max_values = fixed_max_values.tolist()
		fixed_min_values = backout(f(min_forecast.iloc[:, 0].to_list()))
		fixed_min_values = fixed_min_values.tolist()
		fixed_std_dev_lower_values = backout(f(std_dev_lower_forecast.iloc[:, 0].to_list()))
		fixed_std_dev_lower_values = fixed_std_dev_lower_values.tolist()
		fixed_std_dev_upper_values = backout(f(std_dev_upper_forecast.iloc[:, 0].to_list()))
		fixed_std_dev_upper_values = fixed_std_dev_upper_values.tolist()

		# Fixing the high-res forecast
		fixed_dates_high_res = high_res_forecast.index.to_list()
		fixed_high_res_values = backout(f(high_res_forecast.iloc[:, 0].to_list()))
		fixed_high_res_values = fixed_high_res_values.tolist()

		# Removing Negative Values
		fixed_mean_values2 = [0 if i < 0 else i for i in fixed_mean_values]
		fixed_mean_values = fixed_mean_values2
		fixed_high_res_values2 = [0 if i < 0 else i for i in fixed_high_res_values]
		fixed_high_res_values = fixed_high_res_values2
		fixed_min_values2 = [0 if i < 0 else i for i in fixed_min_values]
		fixed_min_values = fixed_min_values2
		fixed_max_values2 = [0 if i < 0 else i for i in fixed_max_values]
		fixed_max_values = fixed_max_values2
		fixed_std_dev_lower_values2 = [0 if i < 0 else i for i in fixed_std_dev_lower_values]
		fixed_std_dev_lower_values = fixed_std_dev_lower_values2
		fixed_std_dev_upper_values2 = [0 if i < 0 else i for i in fixed_std_dev_upper_values]
		fixed_std_dev_upper_values = fixed_std_dev_upper_values2

		# ----------------------------------------------
		# Chart Section
		# ----------------------------------------------

		datetime_start = fixed_dates[0]
		datetime_end = fixed_dates[-1]

		avg_series = go.Scatter(
			name='Mean',
			x=fixed_dates,
			y=fixed_mean_values,
			line=dict(
				color='blue',
			)
		)

		max_series = go.Scatter(
			name='Max',
			x=fixed_dates,
			y=fixed_max_values,
			fill='tonexty',
			mode='lines',
			line=dict(
				color='rgb(152, 251, 152)',
				width=0,
			)
		)

		min_series = go.Scatter(
			name='Min',
			x=fixed_dates,
			y=fixed_min_values,
			fill=None,
			mode='lines',
			line=dict(
				color='rgb(152, 251, 152)',
			)
		)

		std_dev_lower_series = go.Scatter(
			name='Std. Dev. Lower',
			x=fixed_dates,
			y=fixed_std_dev_lower_values,
			fill='tonexty',
			mode='lines',
			line=dict(
				color='rgb(152, 251, 152)',
				width=0,
			)
		)

		std_dev_upper_series = go.Scatter(
			name='Std. Dev. Upper',
			x=fixed_dates,
			y=fixed_std_dev_upper_values,
			fill='tonexty',
			mode='lines',
			line=dict(
				width=0,
				color='rgb(34, 139, 34)',
			)
		)

		plot_series = [min_series,
		               std_dev_lower_series,
		               std_dev_upper_series,
		               max_series,
		               avg_series]

		if hres_values:
			plot_series.append(go.Scatter(
				name='HRES',
				x=fixed_dates_high_res,
				y=fixed_high_res_values,
				line=dict(
					color='black',
				)
			))

		try:
			return_shapes, return_annotations = get_return_period_ploty_info(request, datetime_start, datetime_end)
		except:
			return_annotations = []
			return_shapes = []

		layout = go.Layout(
			title="Forecast<br><sub>{0} ({1}): {2}</sub>".format(
				watershed, subbasin, comid),
			xaxis=dict(
				title='Date',
			),
			yaxis=dict(
				title='Streamflow ({}<sup>3</sup>/s)'.format(get_units_title(units)),
				range=[0, max(max_values) + max(max_values) / 5]
			),
			shapes=return_shapes,
			annotations=return_annotations
		)

		chart_obj = PlotlyView(
			go.Figure(data=plot_series,
			          layout=layout)
		)

		context = {
			'gizmo_object': chart_obj,
		}

		return render(request, 'historical_validation_tool_colombia/gizmo_ajax.html', context)

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No data found for the selected reach.'})


def get_observed_discharge_csv(request):
	"""
    Get observed data from csv files in Hydroshare
    """

	get_data = request.GET

	try:
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0, skiprows=26)
		df.index = pd.to_datetime(df.index)

		datesObservedDischarge = df.index.tolist()
		observedDischarge = df.iloc[:, 0].values
		observedDischarge.tolist()

		pairs = [list(a) for a in zip(datesObservedDischarge, observedDischarge)]

		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename=observed_discharge_{0}.csv'.format(codEstacion)

		writer = csv_writer(response)
		writer.writerow(['datetime', 'flow (m3/s)'])

		for row_data in pairs:
			writer.writerow(row_data)

		return response

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'An unknown error occurred while retrieving the Discharge Data.'})


def get_simulated_discharge_csv(request):
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

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		pairs = [list(a) for a in zip(era_dates, era_values)]

		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename=simulated_discharge_{0}.csv'.format(codEstacion)

		writer = csv_writer(response)
		writer.writerow(['datetime', 'flow (m3/s)'])

		for row_data in pairs:
			writer.writerow(row_data)

		return response

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'An unknown error occurred while retrieving the Discharge Data.'})


def get_simulated_bc_discharge_csv(request):
	"""
    Get historic simulations from ERA Interim
    """

	get_data = request.GET

	try:
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Correct the Bias in Sumulation'''

		years = ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992',
		         '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005',
		         '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014']

		months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

		dates = []
		values = []

		for year in years:
			data_year = simulated_df[simulated_df.index.year == int(year)]

			for month in months:
				data_month = data_year[data_year.index.month == int(month)]

				# select a specific month for bias correction example
				# in this case we will use current month from forecast
				iniDate = data_month.index[0]
				monIdx = iniDate.month

				# filter historic data to only be current month
				monData = simulated_df[simulated_df.index.month.isin([monIdx])]
				# filter the observations to current month
				monObs = observed_df[observed_df.index.month.isin([monIdx])]

				# get maximum value to bound histogram
				obs_tempMax = np.max(monObs.max())
				sim_tempMax = np.max(monData.max())
				obs_tempMin = np.min(monObs.min())
				sim_tempMin = np.min(monData.min())

				obs_maxVal = math.ceil(obs_tempMax)
				sim_maxVal = math.ceil(sim_tempMax)
				obs_minVal = math.floor(obs_tempMin)
				sim_minVal = math.floor(sim_tempMin)

				n_elementos_obs = len(monObs.iloc[:, 0].values)
				n_elementos_sim = len(monData.iloc[:, 0].values)

				n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
				n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

				# specify the bin width for histogram (in m3/s)
				step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
				step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

				# specify histogram bins
				bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
				bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

				if (bins_obs[0] == 0):
					bins_obs = np.concatenate((-bins_obs[1], bins_obs))
				elif (bins_obs[0] > 0):
					bins_obs = np.concatenate((-bins_obs[0], bins_obs))

				if (bins_sim[0] >= 0):
					bins_sim = np.concatenate((-bins_sim[1], bins_sim))
				elif (bins_sim[0] > 0):
					bins_sim = np.concatenate((-bins_sim[0], bins_sim))

				# get the histograms
				sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
				obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

				# adjust the bins to be the center
				bin_edges_sim = bin_edges_sim[1:]
				bin_edges_obs = bin_edges_obs[1:]

				# normalize the histograms
				sim_counts = sim_counts.astype(float) / monData.size
				obs_counts = obs_counts.astype(float) / monObs.size

				# calculate the cdfs
				simcdf = np.cumsum(sim_counts)
				obscdf = np.cumsum(obs_counts)

				# interpolated function to convert simulated streamflow to prob
				f = interpolate.interp1d(bin_edges_sim, simcdf)

				# interpolated function to convert simulated prob to observed streamflow
				backout = interpolate.interp1d(obscdf, bin_edges_obs)

				date = data_month.index.to_list()
				value = backout(f(data_month.iloc[:, 0].to_list()))
				value = value.tolist()

				dates.append(date)
				values.append(value)

		dates = reduce(lambda x, y: x + y, dates)
		values = reduce(lambda x, y: x + y, values)

		corrected_df = pd.DataFrame(data=values, index=dates, columns=['Corrected Simulated Streamflow'])

		pairs = [list(a) for a in zip(dates, values)]

		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename=corrected_simulated_discharge_{0}.csv'.format(
			codEstacion)

		writer = csv_writer(response)
		writer.writerow(['datetime', 'flow (m3/s)'])

		for row_data in pairs:
			writer.writerow(row_data)

		return response

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'An unknown error occurred while retrieving the Discharge Data.'})


def get_forecast_data_csv(request):
	"""""
    Returns Forecast data as csv
    """""

	get_data = request.GET

	try:
		# model = get_data['model']
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		if get_data['startdate'] != '':
			startdate = get_data['startdate']
		else:
			startdate = 'most_recent'

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetAvailableDates/',
		                   params=request_params, headers=request_headers)

		qout_data = res.content.decode('utf-8').splitlines()
		qout_data.pop(0)

		init_time = qout_data[0].split(',')[0].split(' ')[0]
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename=streamflow_forecast_{0}_{1}_{2}_{3}.csv'.format(
			watershed,
			subbasin,
			comid,
			init_time)

		writer = csv_writer(response)
		writer.writerow(
			['datetime', 'high_res (m3/s)', 'max (m3/s)', 'mean (m3/s)', 'min (m3/s)', 'std_dev_range_lower (m3/s)',
			 'std_dev_range_upper (m3/s)'])

		for row_data in qout_data:
			writer.writerow(row_data.split(','))

		return response

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No forecast data found.'})


def get_forecast_bc_data_csv(request):
	"""""
    Returns Forecast data as csv
    """""

	get_data = request.GET
	try:
		# model = get_data['model']
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']
		comid = get_data['streamcomid']
		if get_data['startdate'] != '':
			startdate = get_data['startdate']
		else:
			startdate = 'most_recent'
		units = 'metric'
		codEstacion = get_data['stationcode']
		nomEstacion = get_data['stationname']

		'''Get Simulated Data'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		era_res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/',
		                       params=request_params, headers=request_headers)

		era_pairs = era_res.content.splitlines()
		era_pairs.pop(0)

		era_dates = []
		era_values = []

		for era_pair in era_pairs:
			era_pair = era_pair.decode('utf-8')
			era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
			era_values.append(float(era_pair.split(',')[1]))

		# Removing Negative Values
		era_values2 = [0 if i < 0 else i for i in era_values]
		era_values = era_values2

		simulated_df = pd.DataFrame(data=era_values, index=era_dates, columns=['Simulated Streamflow'])

		'''Get Observed Data'''

		url = 'https://www.hydroshare.org/resource/d222676fbd984a81911761ca1ba936bf/data/contents/Discharge_Data/{0}.csv'.format(
			codEstacion)

		s = requests.get(url, verify=False).content

		df = pd.read_csv(io.StringIO(s.decode('utf-8')), index_col=0)
		df.index = pd.to_datetime(df.index)

		datesDischarge = df.index.tolist()
		dataDischarge = df.iloc[:, 0].values
		dataDischarge.tolist()

		if isinstance(dataDischarge[0], str):
			dataDischarge = map(float, dataDischarge)

		observed_df = pd.DataFrame(data=dataDischarge, index=datesDischarge, columns=['Observed Streamflow'])

		'''Get Forecast'''

		# request_params
		request_params = dict(watershed_name=watershed, subbasin_name=subbasin, reach_id=comid,
		                      forecast_folder=startdate, return_format='csv')

		# Token is for the demo account
		request_headers = dict(Authorization='Token 1adf07d983552705cd86ac681f3717510b6937f6')

		res = requests.get('https://tethys2.byu.edu/apps/streamflow-prediction-tool/api/GetForecast/',
		                   params=request_params, headers=request_headers)

		pairs = res.content.splitlines()
		header = pairs.pop(0)

		dates = []
		hres_dates = []

		mean_values = []
		hres_values = []
		min_values = []
		max_values = []
		std_dev_lower_values = []
		std_dev_upper_values = []

		for pair in pairs:
			pair = pair.decode('utf-8')
			if b'high_res' in header:
				hres_dates.append(dt.datetime.strptime(pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
				hres_values.append(float(pair.split(',')[1]))

				if 'nan' not in pair:
					dates.append(dt.datetime.strptime(pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
					max_values.append(float(pair.split(',')[2]))
					mean_values.append(float(pair.split(',')[3]))
					min_values.append(float(pair.split(',')[4]))
					std_dev_lower_values.append(float(pair.split(',')[5]))
					std_dev_upper_values.append(float(pair.split(',')[6]))

			else:
				dates.append(dt.datetime.strptime(pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
				max_values.append(float(pair.split(',')[1]))
				mean_values.append(float(pair.split(',')[2]))
				min_values.append(float(pair.split(',')[3]))
				std_dev_lower_values.append(float(pair.split(',')[4]))
				std_dev_upper_values.append(float(pair.split(',')[5]))

		# Removing Negative Values
		mean_values2 = [0 if i < 0 else i for i in mean_values]
		mean_values = mean_values2
		hres_values2 = [0 if i < 0 else i for i in hres_values]
		hres_values = hres_values2
		min_values2 = [0 if i < 0 else i for i in min_values]
		min_values = min_values2
		max_values2 = [0 if i < 0 else i for i in max_values]
		max_values = max_values2
		std_dev_lower_values2 = [0 if i < 0 else i for i in std_dev_lower_values]
		std_dev_lower_values = std_dev_lower_values2
		std_dev_upper_values2 = [0 if i < 0 else i for i in std_dev_upper_values]
		std_dev_upper_values = std_dev_upper_values2

		mean_forecast = pd.DataFrame(np.array(mean_values), columns=['streamflow (m3/s)'], index=dates)
		max_forecast = pd.DataFrame(np.array(max_values), columns=['streamflow (m3/s)'], index=dates)
		min_forecast = pd.DataFrame(np.array(min_values), columns=['streamflow (m3/s)'], index=dates)
		std_dev_lower_forecast = pd.DataFrame(np.array(std_dev_lower_values), columns=['streamflow (m3/s)'],
		                                      index=dates)
		std_dev_upper_forecast = pd.DataFrame(np.array(std_dev_upper_values), columns=['streamflow (m3/s)'],
		                                      index=dates)

		high_res_forecast = pd.DataFrame(np.array(hres_values), columns=['streamflow (m3/s)'], index=hres_dates)

		'''Correct Forecast'''

		iniDate = mean_forecast.index[0]
		monIdx = iniDate.month

		# filter historic data to only be current month
		monData = simulated_df[simulated_df.index.month.isin([monIdx])]
		# filter the observations to current month
		monObs = observed_df[observed_df.index.month.isin([monIdx])]

		# get maximum value to bound histogram
		obs_tempMax = np.max(monObs.max())
		sim_tempMax = np.max(monData.max())
		obs_tempMin = np.min(monObs.min())
		sim_tempMin = np.min(monData.min())

		obs_maxVal = math.ceil(obs_tempMax)
		sim_maxVal = math.ceil(sim_tempMax)
		obs_minVal = math.floor(obs_tempMin)
		sim_minVal = math.floor(sim_tempMin)

		n_elementos_obs = len(monObs.iloc[:, 0].values)
		n_elementos_sim = len(monData.iloc[:, 0].values)

		n_marcas_clase_obs = math.ceil(1 + (3.322 * math.log10(n_elementos_obs)))
		n_marcas_clase_sim = math.ceil(1 + (3.322 * math.log10(n_elementos_sim)))

		# specify the bin width for histogram (in m3/s)
		step_obs = (obs_maxVal - obs_minVal) / n_marcas_clase_obs
		step_sim = (sim_maxVal - sim_minVal) / n_marcas_clase_sim

		# specify histogram bins
		bins_obs = np.arange(-np.min(step_obs), obs_maxVal + 2 * np.min(step_obs), np.min(step_obs))
		bins_sim = np.arange(-np.min(step_sim), sim_maxVal + 2 * np.min(step_sim), np.min(step_sim))

		if (bins_obs[0] == 0):
			bins_obs = np.concatenate((-bins_obs[1], bins_obs))
		elif (bins_obs[0] > 0):
			bins_obs = np.concatenate((-bins_obs[0], bins_obs))

		if (bins_sim[0] >= 0):
			bins_sim = np.concatenate((-bins_sim[1], bins_sim))
		elif (bins_sim[0] > 0):
			bins_sim = np.concatenate((-bins_sim[0], bins_sim))

		# get the histograms
		sim_counts, bin_edges_sim = np.histogram(monData, bins=bins_sim)
		obs_counts, bin_edges_obs = np.histogram(monObs, bins=bins_obs)

		# adjust the bins to be the center
		bin_edges_sim = bin_edges_sim[1:]
		bin_edges_obs = bin_edges_obs[1:]

		# normalize the histograms
		sim_counts = sim_counts.astype(float) / monData.size
		obs_counts = obs_counts.astype(float) / monObs.size

		# calculate the cdfs
		simcdf = np.cumsum(sim_counts)
		obscdf = np.cumsum(obs_counts)

		# interpolated function to convert simulated streamflow to prob
		f = interpolate.interp1d(bin_edges_sim, simcdf, fill_value="extrapolate")

		# interpolated function to convert simulated prob to observed streamflow
		backout = interpolate.interp1d(obscdf, bin_edges_obs, fill_value="extrapolate")

		# Fixing the forecast
		fixed_dates = mean_forecast.index.to_list()
		fixed_mean_values = backout(f(mean_forecast.iloc[:, 0].to_list()))
		fixed_mean_values = fixed_mean_values.tolist()
		fixed_max_values = backout(f(max_forecast.iloc[:, 0].to_list()))
		fixed_max_values = fixed_max_values.tolist()
		fixed_min_values = backout(f(min_forecast.iloc[:, 0].to_list()))
		fixed_min_values = fixed_min_values.tolist()
		fixed_std_dev_lower_values = backout(f(std_dev_lower_forecast.iloc[:, 0].to_list()))
		fixed_std_dev_lower_values = fixed_std_dev_lower_values.tolist()
		fixed_std_dev_upper_values = backout(f(std_dev_upper_forecast.iloc[:, 0].to_list()))
		fixed_std_dev_upper_values = fixed_std_dev_upper_values.tolist()

		# Fixing the high-res forecast
		fixed_dates_high_res = high_res_forecast.index.to_list()
		fixed_high_res_values = backout(f(high_res_forecast.iloc[:, 0].to_list()))
		fixed_high_res_values = fixed_high_res_values.tolist()

		# Removing Negative Values
		fixed_mean_values2 = [0 if i < 0 else i for i in fixed_mean_values]
		fixed_mean_values = fixed_mean_values2
		fixed_high_res_values2 = [0 if i < 0 else i for i in fixed_high_res_values]
		fixed_high_res_values = fixed_high_res_values2
		fixed_min_values2 = [0 if i < 0 else i for i in fixed_min_values]
		fixed_min_values = fixed_min_values2
		fixed_max_values2 = [0 if i < 0 else i for i in fixed_max_values]
		fixed_max_values = fixed_max_values2
		fixed_std_dev_lower_values2 = [0 if i < 0 else i for i in fixed_std_dev_lower_values]
		fixed_std_dev_lower_values = fixed_std_dev_lower_values2
		fixed_std_dev_upper_values2 = [0 if i < 0 else i for i in fixed_std_dev_upper_values]
		fixed_std_dev_upper_values = fixed_std_dev_upper_values2

		pairs = [list(a) for a in zip(fixed_dates, fixed_mean_values)]
		mean_forecast = pd.DataFrame(pairs, columns=['Datetime', 'mean (m3/s)'])
		mean_forecast.set_index('Datetime', inplace=True)

		pairs = [list(a) for a in zip(fixed_dates, fixed_max_values)]
		max_forecast = pd.DataFrame(pairs, columns=['Datetime', 'max (m3/s)'])
		max_forecast.set_index('Datetime', inplace=True)

		pairs = [list(a) for a in zip(fixed_dates, fixed_min_values)]
		min_forecast = pd.DataFrame(pairs, columns=['Datetime', 'min (m3/s)'])
		min_forecast.set_index('Datetime', inplace=True)

		pairs = [list(a) for a in zip(fixed_dates, fixed_std_dev_lower_values)]
		std_dev_lower_forecast = pd.DataFrame(pairs, columns=['Datetime', 'std_dev_range_lower (m3/s)'])
		std_dev_lower_forecast.set_index('Datetime', inplace=True)

		pairs = [list(a) for a in zip(fixed_dates, fixed_std_dev_upper_values)]
		std_dev_upper_forecast = pd.DataFrame(pairs, columns=['Datetime', 'std_dev_range_upper (m3/s)'])
		std_dev_upper_forecast.set_index('Datetime', inplace=True)

		pairs = [list(a) for a in zip(fixed_dates_high_res, fixed_high_res_values)]
		high_res_forecast = pd.DataFrame(pairs, columns=['Datetime', 'high_res (m3/s)'])
		high_res_forecast.set_index('Datetime', inplace=True)

		init_time = mean_forecast.index[0]

		corrected_forecast_df = pd.concat(
			[mean_forecast, max_forecast, mean_forecast, min_forecast, std_dev_lower_forecast, std_dev_upper_forecast,
			 high_res_forecast], axis=1)

		response = HttpResponse(content_type='text/csv')
		response[
			'Content-Disposition'] = 'attachment; filename=corrected_streamflow_forecast_{0}_{1}_{2}_{3}.csv'.format(
			watershed, subbasin, comid, init_time)
		corrected_forecast_df.to_csv(encoding='utf-8', header=True, path_or_buf=response)

		return response

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No forecast data found.'})
