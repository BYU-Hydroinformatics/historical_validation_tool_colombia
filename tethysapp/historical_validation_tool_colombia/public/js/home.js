// Getting the csrf token
console.log("Gio aqui");
let csrftoken = Cookies.get('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

var feature_layer;
var current_layer;
var map;

let $loading = $('#view-file-loading');
var m_downloaded_historical_streamflow = false;

function init_map() {

	var base_layer = new ol.layer.Tile({
		source: new ol.source.BingMaps({
			key: 'eLVu8tDRPeQqmBlKAjcw~82nOqZJe2EpKmqd-kQrSmg~AocUZ43djJ-hMBHQdYDyMbT-Enfsk0mtUIGws1WeDuOvjY4EXCH-9OK3edNLDgkc',
			imagerySet: 'Road'
			//            imagerySet: 'AerialWithLabels'
		})
	});

	var streams = new ol.layer.Image({
		source: new ol.source.ImageWMS({
			//url: 'https://tethys2.byu.edu/geoserver/colombia_hydroviewer/wms',
			url: 'https://tethys.byu.edu/geoserver/colombia_hydroviewer/wms',
			params: { 'LAYERS': 'south_america-colombia-drainage_line' },
			serverType: 'geoserver',
			crossOrigin: 'Anonymous'
		}),
		opacity: 0.5
	});

	var stations = new ol.layer.Image({
		source: new ol.source.ImageWMS({
			//url: 'https://tethys2.byu.edu/geoserver/colombia_hydroviewer/wms',
			url: 'https://tethys.byu.edu/geoserver/colombia_hydroviewer/wms',
			params: { 'LAYERS': 'IDEAM_Stations' },
			serverType: 'geoserver',
			crossOrigin: 'Anonymous'
		})
	});

	feature_layer = stations;

	map = new ol.Map({
		target: 'map',
		layers: [base_layer, streams, stations],
		view: new ol.View({
			center: ol.proj.fromLonLat([-74.08083, 4.598889]),
			zoom: 5
		})
	});

}

//let ajax_url = 'https://tethys2.byu.edu/geoserver/colombia_hydroviewer/wfs?request=GetCapabilities';
let ajax_url = 'https://tethys.byu.edu/geoserver/colombia_hydroviewer/wfs?request=GetCapabilities';

let capabilities = $.ajax(ajax_url, {
	type: 'GET',
	data:{
		service: 'WFS',
		version: '1.0.0',
		request: 'GetCapabilities',
		outputFormat: 'text/javascript'
	},
	success: function() {
		let x = capabilities.responseText
		.split('<FeatureTypeList>')[1]
		.split('colombia_hydroviewer:south_america-colombia-drainage_line')[1]
		.split('LatLongBoundingBox ')[1]
		.split('/></FeatureType>')[0];

		let minx = Number(x.split('"')[1]);
		let miny = Number(x.split('"')[3]);
		let maxx = Number(x.split('"')[5]);
		let maxy = Number(x.split('"')[7]);

		minx = minx + 2;
		miny = miny + 2;
		maxx = maxx - 2;
		maxy = maxy - 2;

		let extent = ol.proj.transform([minx, miny], 'EPSG:4326', 'EPSG:3857').concat(ol.proj.transform([maxx, maxy], 'EPSG:4326', 'EPSG:3857'));

		map.getView().fit(extent, map.getSize());
	}
});

function get_discharge_info (stationcode, stationname) {
	$('#observed-loading-Q').removeClass('hidden');
    $.ajax({
        url: 'get-discharge-data',
        type: 'GET',
        data: {'stationcode' : stationcode, 'stationname': stationname},
        error: function () {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the observed data</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function () {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function (data) {
            if (!data.error) {
                $('#observed-loading-Q').addClass('hidden');
                $('#dates').removeClass('hidden');
//                $('#obsdates').removeClass('hidden');
                $loading.addClass('hidden');
                $('#observed-chart-Q').removeClass('hidden');
                $('#observed-chart-Q').html(data);

                //resize main graph
                Plotly.Plots.resize($("#observed-chart-Q .js-plotly-plot")[0]);
                Plotly.relayout($("#observed-chart-Q .js-plotly-plot")[0], {
                	'xaxis.autorange': true,
                	'yaxis.autorange': true
                });

                var params = {
                    stationcode: stationcode,
                    stationname: stationname,
                };

                $('#submit-download-observed-discharge').attr({
                    target: '_blank',
                    href: 'get-observed-discharge-csv?' + jQuery.param(params)
                });

                $('#download_observed_discharge').removeClass('hidden');

            } else if (data.error) {
            	$('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the Observed Data</strong></p>');
            	$('#info').removeClass('hidden');

            	setTimeout(function() {
            		$('#info').addClass('hidden')
                }, 5000);

            } else {
            	$('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
            }
        }
    });
};

function get_simulated_data (watershed, subbasin, streamcomid, stationcode, stationname) {
	$('#simulated-loading-Q').removeClass('hidden');
	m_downloaded_historical_streamflow = true;
    $.ajax({
        url: 'get-simulated-data',
        type: 'GET',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'streamcomid': streamcomid,
            'stationcode':stationcode,
            'stationname': stationname
        },
        error: function() {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the simulated data</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function () {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function (data) {
            if (!data.error) {
                $('#simulated-loading-Q').addClass('hidden');
                $('#dates').removeClass('hidden');
//                $('#obsdates').removeClass('hidden');
                $loading.addClass('hidden');
                $('#simulated-chart-Q').removeClass('hidden');
                $('#simulated-chart-Q').html(data);

                //resize main graph
                Plotly.Plots.resize($("#simulated-chart-Q .js-plotly-plot")[0]);
                Plotly.relayout($("#simulated-chart-Q .js-plotly-plot")[0], {
                	'xaxis.autorange': true,
                	'yaxis.autorange': true
                });

                var params = {
                    watershed: watershed,
                	subbasin: subbasin,
                	streamcomid: streamcomid,
                	stationcode:stationcode,
                	stationname: stationname
                };

                $('#submit-download-simulated-discharge').attr({
                    target: '_blank',
                    href: 'get-simulated-discharge-csv?' + jQuery.param(params)
                });

                $('#download_simulated_discharge').removeClass('hidden');

           		 } else if (data.error) {
           		 	$('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the Simulated Data</strong></p>');
           		 	$('#info').removeClass('hidden');

           		 	setTimeout(function() {
           		 		$('#info').addClass('hidden')
           		 	}, 5000);
           		 } else {
           		 	$('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
           		 }
       		}
    });
};

function get_simulated_bc_data (watershed, subbasin, streamcomid, stationcode, stationname) {
	$('#simulated-bc-loading-Q').removeClass('hidden');
	m_downloaded_historical_streamflow = true;
    $.ajax({
        url: 'get-simulated-bc-data',
        type: 'GET',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'streamcomid': streamcomid,
            'stationcode':stationcode,
            'stationname': stationname
        },
        error: function() {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the corrected simulated data</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function () {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function (data) {
            if (!data.error) {
                $('#simulated-bc-loading-Q').addClass('hidden');
                $('#dates').removeClass('hidden');
//                $('#obsdates').removeClass('hidden');
                $loading.addClass('hidden');
                $('#simulated-bc-chart-Q').removeClass('hidden');
                $('#simulated-bc-chart-Q').html(data);

                //resize main graph
                Plotly.Plots.resize($("#simulated-bc-chart-Q .js-plotly-plot")[0]);
                Plotly.relayout($("#simulated-bc-chart-Q .js-plotly-plot")[0], {
                	'xaxis.autorange': true,
                	'yaxis.autorange': true
                });

                var params = {
                    watershed: watershed,
                	subbasin: subbasin,
                	streamcomid: streamcomid,
                	stationcode:stationcode,
                	stationname: stationname
                };

                $('#submit-download-simulated-bc-discharge').attr({
                    target: '_blank',
                    href: 'get-simulated-bc-discharge-csv?' + jQuery.param(params)
                });

                $('#download_simulated_bc_discharge').removeClass('hidden');

           		 } else if (data.error) {
           		 	$('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the Simulated Data</strong></p>');
           		 	$('#info').removeClass('hidden');

           		 	setTimeout(function() {
           		 		$('#info').addClass('hidden')
           		 	}, 5000);
           		 } else {
           		 	$('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
           		 }
       		}
    });
};

function get_hydrographs (watershed, subbasin, streamcomid, stationcode, stationname) {
	$('#hydrographs-loading').removeClass('hidden');
	m_downloaded_historical_streamflow = true;
    $.ajax({
        url: 'get-hydrographs',
        type: 'GET',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'streamcomid': streamcomid,
            'stationcode': stationcode,
            'stationname': stationname
        },
        error: function() {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the data</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function () {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function (data) {
            if (!data.error) {
                $('#hydrographs-loading').addClass('hidden');
                $('#dates').removeClass('hidden');
//                $('#obsdates').removeClass('hidden');
                $loading.addClass('hidden');
                $('#hydrographs-chart').removeClass('hidden');
                $('#hydrographs-chart').html(data);

                //resize main graph
                Plotly.Plots.resize($("#hydrographs-chart .js-plotly-plot")[0]);
                Plotly.relayout($("#hydrographs-chart .js-plotly-plot")[0], {
                	'xaxis.autorange': true,
                	'yaxis.autorange': true
                });

           		 } else if (data.error) {
           		 	$('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the Data</strong></p>');
           		 	$('#info').removeClass('hidden');

           		 	setTimeout(function() {
           		 		$('#info').addClass('hidden')
           		 	}, 5000);
           		 } else {
           		 	$('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
           		 }
       		}
    });
};

function get_hydro_stats (watershed, subbasin, streamcomid, stationcode, stationname) {
	$('#hydro_stats-loading').removeClass('hidden');
  console.log("entering teh hydro_stats function");
	m_downloaded_historical_streamflow = true;
    $.ajax({
        url: 'get-hydro-stats',
        type: 'GET',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'streamcomid': streamcomid,
            'stationcode': stationcode,
            'stationname': stationname
        },
        error: function() {
          console.log("error");
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the data</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function () {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function (data) {
            if (!data.error) {
              console.log(data);

                $('#hydro_stats-loading').addClass('hidden');
                $('#dates').removeClass('hidden');
//                $('#obsdates').removeClass('hidden');
                $loading.addClass('hidden');
                $('#hydro_stats-chart').removeClass('hidden');
                var observed_trace_daily = {
                  x: data['gizmo_object_daily_average']['data'][0]['x'],
                  y: data['gizmo_object_daily_average']['data'][0]['y'],
                  type: 'scatter',
                  name:data['gizmo_object_daily_average']['data'][0]['name']
                };
                //daily data
                var simulated_trace_daily = {
                  x: data['gizmo_object_daily_average']['data'][1]['x'],
                  y: data['gizmo_object_daily_average']['data'][1]['y'],
                  type: 'scatter',
                  name:data['gizmo_object_daily_average']['data'][1]['name'],

                };

                var simulated_trace_corrected_daily = {
                  x: data['gizmo_object_daily_average']['data'][2]['x'],
                  y: data['gizmo_object_daily_average']['data'][2]['y'],
                  type: 'scatter',
                  name:data['gizmo_object_daily_average']['data'][2]['name'],

                };
                //monthly//
                var observed_trace_monthly = {
                  x: data['gizmo_object_monthly_average']['data'][0]['x'],
                  y: data['gizmo_object_monthly_average']['data'][0]['y'],
                  type: 'scatter',
                  name:data['gizmo_object_monthly_average']['data'][0]['name'],

                };

                var simulated_trace_monthly = {
                  x: data['gizmo_object_monthly_average']['data'][1]['x'],
                  y: data['gizmo_object_monthly_average']['data'][1]['y'],
                  type: 'scatter',
                  name:data['gizmo_object_monthly_average']['data'][1]['name'],

                };

                var simulated_trace_corrected_monthly = {
                  x: data['gizmo_object_monthly_average']['data'][2]['x'],
                  y: data['gizmo_object_monthly_average']['data'][2]['y'],
                  type: 'scatter',
                  name:data['gizmo_object_monthly_average']['data'][2]['name'],

                };
                //Scatter plot //
                var scatter_plot_original = {
                  x: data['gizmo_object_scatterplot']['data'][0]['x'],
                  y: data['gizmo_object_scatterplot']['data'][0]['y'],
                  type: 'scatter',
                  mode:'markers',
                  markers:{
                    color:data['gizmo_object_scatterplot']['data'][0]['marker']['color']
                  },
                  name:data['gizmo_object_scatterplot']['data'][0]['name'],
                };
                var scatter_plot_corrected = {
                  x: data['gizmo_object_scatterplot']['data'][1]['x'],
                  y: data['gizmo_object_scatterplot']['data'][1]['y'],
                  type: 'scatter',
                  mode:'markers',
                  markers:{
                    color:data['gizmo_object_scatterplot']['data'][1]['marker']['color']
                  },
                  name:data['gizmo_object_scatterplot']['data'][1]['name'],
                };
                var scatter_plot_45_line = {
                  x: data['gizmo_object_scatterplot']['data'][2]['x'],
                  y: data['gizmo_object_scatterplot']['data'][2]['y'],
                  type: 'scatter',
                  name:data['gizmo_object_scatterplot']['data'][2]['name'],
                };
                var scatter_plot_original_line = {
                  x: data['gizmo_object_scatterplot']['data'][3]['x'],
                  y: data['gizmo_object_scatterplot']['data'][3]['y'],
                  type: 'scatter',
                  name:data['gizmo_object_scatterplot']['data'][3]['name'],
                };
                var scatter_plot_corrected_line = {
                  x: data['gizmo_object_scatterplot']['data'][4]['x'],
                  y: data['gizmo_object_scatterplot']['data'][4]['y'],
                  type: 'scatter',
                  name:data['gizmo_object_scatterplot']['data'][4]['name'],
                };
                // VOLUME ANALYSIS //
                var volume_analysis_observed = {
                  x: data['gizmo_volume_analysis']['data'][0]['x'],
                  y: data['gizmo_volume_analysis']['data'][0]['y'],
                  type: 'scatter',
                  name:data['gizmo_volume_analysis']['data'][0]['name'],

                };

                var volume_analysis_simulated= {
                  x: data['gizmo_volume_analysis']['data'][1]['x'],
                  y: data['gizmo_volume_analysis']['data'][1]['y'],
                  type: 'scatter',
                  name:data['gizmo_volume_analysis']['data'][1]['name'],

                };

                var volume_analysis_simulated_corrected= {
                  x: data['gizmo_volume_analysis']['data'][2]['x'],
                  y: data['gizmo_volume_analysis']['data'][2]['y'],
                  type: 'scatter',
                  name:data['gizmo_volume_analysis']['data'][2]['name'],

                };

                // var data_graphs = [observed_trace_daily, simulated_trace_daily, simulated_trace_corrected_daily,observed_trace_monthly,simulated_trace_monthly,simulated_trace_corrected_monthly];
                var data_graphs1 = [observed_trace_daily, simulated_trace_daily, simulated_trace_corrected_daily];
                var data_graphs2 = [observed_trace_monthly,simulated_trace_monthly,simulated_trace_corrected_monthly];
                var data_graphs3 = [scatter_plot_original,scatter_plot_corrected, scatter_plot_45_line, scatter_plot_original_line,scatter_plot_corrected_line];
                var data_graphs4 = [scatter_plot_original,scatter_plot_corrected, scatter_plot_45_line];
                var data_graphs5 = [volume_analysis_observed,volume_analysis_simulated,volume_analysis_simulated_corrected];
                var layout ={
                  xaxis:{
                    title:{
                      text: data['gizmo_object_daily_average']['layout']['xaxis'],
                    },
                    autorange: true,
                  },
                  yaxis:{
                    title:{
                      text: data['gizmo_object_daily_average']['layout']['yaxis'],
                    },
                    autorange: true,
                  },

                  title: data['gizmo_object_daily_average']['layout']['title']

                }
                var layout2 = {
                  xaxis:{
                    title:{
                      text: data['gizmo_object_monthly_average']['layout']['xaxis'],
                    },
                    autorange: true,
                  },
                  yaxis:{
                    title:{
                      text: data['gizmo_object_monthly_average']['layout']['yaxis'],
                    },
                    autorange: true,
                  },
                  title: data['gizmo_object_monthly_average']['layout']['title']

                }
                var layout3 = {
                  xaxis:{
                    title:{
                      text: data['gizmo_object_scatterplot']['layout']['xaxis'],
                    },
                    autorange: true,
                  },
                  yaxis:{
                    title:{
                      text:data['gizmo_object_scatterplot']['layout']['yaxis'],
                    },
                    autorange: true,
                  },
                  title: data['gizmo_object_scatterplot']['layout']['title']

                }
                var layout4 = {
                  xaxis:{
                    type:'log',
                    title:{
                      text: data['gizmo_object_scatterplot']['layout']['xaxis'],
                    },
                    autorange: true,
                  },
                  yaxis:{
                    type:'log',
                    title:{
                      text:data['gizmo_object_scatterplot']['layout']['yaxis'],
                    },
                    autorange: true,
                  },
                  title: `${data['gizmo_object_scatterplot']['layout']['title']}(Log Scale)`

                }
                var layout5 = {
                  xaxis:{
                    title:{
                      text: data['gizmo_volume_analysis']['layout']['xaxis'],
                    },
                    autorange: true,
                  },
                  yaxis:{
                    title:{
                      text:data['gizmo_volume_analysis']['layout']['yaxis'],
                    },
                    autorange: true,
                  },
                  title: `${data['gizmo_volume_analysis']['layout']['title']}`

                }

                // Plotly.newPlot('hydro_stats-chart', data_graphs, layout);
                Plotly.newPlot('daily2', data_graphs1, layout);
                Plotly.newPlot('monthly2', data_graphs2, layout2);
                Plotly.newPlot('scatterplot2', data_graphs3, layout3);
                Plotly.newPlot('scatterplotLog2', data_graphs4, layout4);
                Plotly.newPlot('volumeAnaysis2', data_graphs5, layout5);

           		 }
               else if (data.error) {
           		 	$('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the Data</strong></p>');
           		 	$('#info').removeClass('hidden');

           		 	setTimeout(function() {
           		 		$('#info').addClass('hidden')
           		 	}, 5000);
           		 } else {
           		 	$('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
           		 }
       		}
    });
};
function get_dailyAverages (watershed, subbasin, streamcomid, stationcode, stationname) {
	$('#dailyAverages-loading').removeClass('hidden');
	m_downloaded_historical_streamflow = true;
    $.ajax({
        url: 'get-dailyAverages',
        type: 'GET',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'streamcomid': streamcomid,
            'stationcode': stationcode,
            'stationname': stationname
        },
        error: function() {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the data</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function () {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function (data) {
            if (!data.error) {
                $('#dailyAverages-loading').addClass('hidden');
                $('#dates').removeClass('hidden');
//                $('#obsdates').removeClass('hidden');
                $loading.addClass('hidden');
                $('#dailyAverages-chart').removeClass('hidden');
                $('#dailyAverages-chart').html(data);

                //resize main graph
                Plotly.Plots.resize($("#dailyAverages-chart .js-plotly-plot")[0]);
                Plotly.relayout($("#dailyAverages-chart .js-plotly-plot")[0], {
                	'xaxis.autorange': true,
                	'yaxis.autorange': true
                });

           		 } else if (data.error) {
           		 	$('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the Data</strong></p>');
           		 	$('#info').removeClass('hidden');

           		 	setTimeout(function() {
           		 		$('#info').addClass('hidden')
           		 	}, 5000);
           		 } else {
           		 	$('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
           		 }
       		}
    });
};

function get_monthlyAverages (watershed, subbasin, streamcomid, stationcode, stationname) {
	$('#monthlyAverages-loading').removeClass('hidden');
	m_downloaded_historical_streamflow = true;
    $.ajax({
        url: 'get-monthlyAverages',
        type: 'GET',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'streamcomid': streamcomid,
            'stationcode': stationcode,
            'stationname': stationname
        },
        error: function() {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the data</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function () {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function (data) {
            if (!data.error) {
                $('#monthlyAverages-loading').addClass('hidden');
                $('#dates').removeClass('hidden');
//                $('#obsdates').removeClass('hidden');
                $loading.addClass('hidden');
                $('#monthlyAverages-chart').removeClass('hidden');
                $('#monthlyAverages-chart').html(data);

                //resize main graph
                Plotly.Plots.resize($("#monthlyAverages-chart .js-plotly-plot")[0]);
                Plotly.relayout($("#monthlyAverages-chart .js-plotly-plot")[0], {
                	'xaxis.autorange': true,
                	'yaxis.autorange': true
                });

           		 } else if (data.error) {
           		 	$('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the Data</strong></p>');
           		 	$('#info').removeClass('hidden');

           		 	setTimeout(function() {
           		 		$('#info').addClass('hidden')
           		 	}, 5000);
           		 } else {
           		 	$('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
           		 }
       		}
    });
};

function get_scatterPlot (watershed, subbasin, streamcomid, stationcode, stationname) {
	$('#scatterPlot-loading').removeClass('hidden');
	m_downloaded_historical_streamflow = true;
    $.ajax({
        url: 'get-scatterPlot',
        type: 'GET',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'streamcomid': streamcomid,
            'stationcode': stationcode,
            'stationname': stationname
        },
        error: function() {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the data</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function () {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function (data) {
            if (!data.error) {
                $('#scatterPlot-loading').addClass('hidden');
                $('#dates').removeClass('hidden');
//                $('#obsdates').removeClass('hidden');
                $loading.addClass('hidden');
                $('#scatterPlot-chart').removeClass('hidden');
                $('#scatterPlot-chart').html(data);

                //resize main graph
                Plotly.Plots.resize($("#scatterPlot-chart .js-plotly-plot")[0]);
                Plotly.relayout($("#scatterPlot-chart .js-plotly-plot")[0], {
                	'xaxis.autorange': true,
                	'yaxis.autorange': true
                });

           		 } else if (data.error) {
           		 	$('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the Data</strong></p>');
           		 	$('#info').removeClass('hidden');

           		 	setTimeout(function() {
           		 		$('#info').addClass('hidden')
           		 	}, 5000);
           		 } else {
           		 	$('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
           		 }
       		}
    });
};

function get_scatterPlotLogScale (watershed, subbasin, streamcomid, stationcode, stationname) {
	$('#scatterPlotLogScale-loading').removeClass('hidden');
	m_downloaded_historical_streamflow = true;
    $.ajax({
        url: 'get-scatterPlotLogScale',
        type: 'GET',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'streamcomid': streamcomid,
            'stationcode': stationcode,
            'stationname': stationname
        },
        error: function() {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the data</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function () {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function (data) {
            if (!data.error) {
                $('#scatterPlotLogScale-loading').addClass('hidden');
                $('#dates').removeClass('hidden');
//                $('#obsdates').removeClass('hidden');
                $loading.addClass('hidden');
                $('#scatterPlotLogScale-chart').removeClass('hidden');
                $('#scatterPlotLogScale-chart').html(data);

                //resize main graph
                Plotly.Plots.resize($("#scatterPlotLogScale-chart .js-plotly-plot")[0]);
                Plotly.relayout($("#scatterPlotLogScale-chart .js-plotly-plot")[0], {
                	'xaxis.autorange': true,
                	'yaxis.autorange': true
                });

           		 } else if (data.error) {
           		 	$('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the Data</strong></p>');
           		 	$('#info').removeClass('hidden');

           		 	setTimeout(function() {
           		 		$('#info').addClass('hidden')
           		 	}, 5000);
           		 } else {
           		 	$('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
           		 }
       		}
    });
};

function get_volumeAnalysis (watershed, subbasin, streamcomid, stationcode, stationname) {
	$('#volumeAnalysis-loading').removeClass('hidden');
	m_downloaded_historical_streamflow = true;
    $.ajax({
        url: 'get-volumeAnalysis',
        type: 'GET',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'streamcomid': streamcomid,
            'stationcode': stationcode,
            'stationname': stationname
        },
        error: function() {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the data</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function () {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function (data) {
            if (!data.error) {
                $('#volumeAnalysis-loading').addClass('hidden');
                $('#dates').removeClass('hidden');
//                $('#obsdates').removeClass('hidden');
                $loading.addClass('hidden');
                $('#volumeAnalysis-chart').removeClass('hidden');
                $('#volumeAnalysis-chart').html(data);

                //resize main graph
                Plotly.Plots.resize($("#volumeAnalysis-chart .js-plotly-plot")[0]);
                Plotly.relayout($("#volumeAnalysis-chart .js-plotly-plot")[0], {
                	'xaxis.autorange': true,
                	'yaxis.autorange': true
                });

           		 } else if (data.error) {
           		 	$('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the Data</strong></p>');
           		 	$('#info').removeClass('hidden');

           		 	setTimeout(function() {
           		 		$('#info').addClass('hidden')
           		 	}, 5000);
           		 } else {
           		 	$('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
           		 }
       		}
    });
};

// Ajax for Volume Table
function createVolumeTable(watershed, subbasin, streamcomid, stationcode, stationname) {
	$('#volumeAnalysis-loading').removeClass('hidden');
	m_downloaded_historical_streamflow = true;
    $.ajax({
        url : "volume-table-ajax/", // the endpoint
        type: 'GET',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'streamcomid': streamcomid,
            'stationcode': stationcode,
            'stationname': stationname
        },

        // handle a successful response
        success : function(resp) {
            //console.log(resp);
            let obs_volume = resp["obs_volume"].toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
            let sim_volume = resp["sim_volume"].toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
            let corr_volume = resp["corr_volume"].toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
            $("#volume_table_div").show();
            $("#volume_table").html(`<table class="table table-hover table-striped">\
                                        <thead>\
                                          <tr>\
                                            <th>Observed Data Volume (Mm<sup>3</sup>)</th>\
                                            <th>Simulated Data Volume (Mm<sup>3</sup>)</th>\
                                            <th>Corrected Simulated Data Volume (Mm<sup>3</sup>)</th>\
                                          </tr>\
                                        </thead>\
                                        <tbody>\
                                          <tr>\
                                            <td>${obs_volume}</td>\
                                            <td>${sim_volume}</td>\
                                            <td>${corr_volume}</td>\
                                          </tr>\
                                        </tbody>\
                                      </table>`);
        },

        // handle a non-successful response
        error : function(xhr, errmsg, err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+".</div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
}

function map_events() {
	map.on('pointermove', function(evt) {
		if (evt.dragging) {
			return;
		}
		var pixel = map.getEventPixel(evt.originalEvent);
		var hit = map.forEachLayerAtPixel(pixel, function(layer) {
			if (layer == feature_layer) {
				current_layer = layer;
				return true;
			}
			});
		map.getTargetElement().style.cursor = hit ? 'pointer' : '';
	});

	map.on("singleclick", function(evt) {

		if (map.getTargetElement().style.cursor == "pointer") {

			var view = map.getView();
			var viewResolution = view.getResolution();
			var wms_url = current_layer.getSource().getGetFeatureInfoUrl(evt.coordinate, viewResolution, view.getProjection(), { 'INFO_FORMAT': 'application/json' });

			if (wms_url) {
				$("#obsgraph").modal('show');
				// $('#observed-chart-Q').addClass('hidden');
				// $('#simulated-chart-Q').addClass('hidden');
				// $('#simulated-bc-chart-Q').addClass('hidden');
				// $('#hydrographs-chart').addClass('hidden');
				$('#hydrographs-chart').addClass('hidden');
				$('#hydro_stats-chart').addClass('hidden');
				// $('#dailyAverages-chart').addClass('hidden');
				// $('#monthlyAverages-chart').addClass('hidden');
				// $('#scatterPlot-chart').addClass('hidden');
				// $('#scatterPlotLogScale-chart').addClass('hidden');
				// $('#volumeAnalysis-chart').addClass('hidden');
				$('#forecast-chart').addClass('hidden');
				$('#forecast-bc-chart').addClass('hidden');
				$('#observed-loading-Q').removeClass('hidden');
				$('#simulated-loading-Q').removeClass('hidden');
				$('#simulated-bc-loading-Q').removeClass('hidden');
				$('#hydrographs-loading').removeClass('hidden');
				$('#hydro_stats-loading').removeClass('hidden');
				$('#dailyAverages-loading').removeClass('hidden');
				$('#monthlyAverages-loading').removeClass('hidden');
				$('#scatterPlot-loading').removeClass('hidden');
				$('#scatterPlotLogScale-loading').removeClass('hidden');
				$('#volumeAnalysis-loading').removeClass('hidden');
				$('#forecast-loading').removeClass('hidden');
				$('#forecast-bc-loading').removeClass('hidden');
				$("#station-info").empty()
				$('#download_observed_discharge').addClass('hidden');
                $('#download_simulated_discharge').addClass('hidden');
                $('#download_simulated_bc_discharge').addClass('hidden');
                $('#download_forecast').addClass('hidden');
                $('#download_forecast_bc').addClass('hidden');

				$.ajax({
					type: "GET",
					url: wms_url,
					dataType: 'json',
					success: function (result) {
						watershed = 'south_america' //OJO buscar como hacerla generica
		         		subbasin = 'continental' //OJO buscar como hacerla generica
		         		var startdate = '';
		         		stationcode = result["features"][0]["properties"]["ID"];
		         		stationname = result["features"][0]["properties"]["Name"];
		         		streamcomid = result["features"][0]["properties"]["COMID"];
		         		stream = result["features"][0]["properties"]["Stream_Nam"];
		         		$("#station-info").append('<h3 id="Station-Name-Tab">Current Station: '+ stationname
                        			+ '</h3><h5 id="Station-Code-Tab">Station Code: '
                        			+ stationcode + '</h3><h5 id="COMID-Tab">Station COMID: '
                        			+ streamcomid+ '</h5><h5>Stream: '+ stream);
                        // get_discharge_info (stationcode, stationname);
                        // get_simulated_data (watershed, subbasin, streamcomid, stationcode, stationname);
                        // get_simulated_bc_data (watershed, subbasin, streamcomid, stationcode, stationname);
                        get_hydrographs (watershed, subbasin, streamcomid, stationcode, stationname);
                        get_hydro_stats (watershed, subbasin, streamcomid, stationcode, stationname);
                        // get_dailyAverages (watershed, subbasin, streamcomid, stationcode, stationname);
                        // get_monthlyAverages (watershed, subbasin, streamcomid, stationcode, stationname);
                        // get_scatterPlot (watershed, subbasin, streamcomid, stationcode, stationname);
                        // get_scatterPlotLogScale (watershed, subbasin, streamcomid, stationcode, stationname);
                        // get_volumeAnalysis (watershed, subbasin, streamcomid, stationcode, stationname);
                        createVolumeTable(watershed, subbasin, streamcomid, stationcode, stationname);
                        get_available_dates(watershed, subbasin, streamcomid);
                        get_time_series(watershed, subbasin, streamcomid, startdate);
                        get_time_series_bc(watershed, subbasin, streamcomid, startdate, stationcode, stationname);
                    }
                });
            }
		}

	});
}



function resize_graphs() {
    // $("#observedQ_tab_link").click(function() {
    //     Plotly.Plots.resize($("#observed-chart-Q .js-plotly-plot")[0]);
    //     Plotly.relayout($("#observed-chart-Q .js-plotly-plot")[0], {
    //     	'xaxis.autorange': true,
    //     	'yaxis.autorange': true
    //     });
    // });
    // $("#simulatedQ_tab_link").click(function() {
    // 	if (m_downloaded_historical_streamflow) {
    // 		Plotly.Plots.resize($("#simulated-chart-Q .js-plotly-plot")[0]);
    // 		Plotly.relayout($("#simulated-chart-Q .js-plotly-plot")[0], {
    //     		'xaxis.autorange': true,
    //     		'yaxis.autorange': true
    //     	});
    // 	}
    // });
    // $("#simulated_bc_Q_tab_link").click(function() {
    // 	Plotly.Plots.resize($("#simulated-bc-chart-Q .js-plotly-plot")[0]);
    // 	Plotly.relayout($("#simulated-bc-chart-Q .js-plotly-plot")[0], {
    //     	'xaxis.autorange': true,
    //     	'yaxis.autorange': true
    //     });
    // });
    $("#hydrographs_tab_link").click(function() {
    	Plotly.Plots.resize($("#hydrographs-chart .js-plotly-plot")[0]);
    	Plotly.relayout($("#hydrographs-chart .js-plotly-plot")[0], {
        	'xaxis.autorange': true,
        	'yaxis.autorange': true
        });
    });
    $("#hydro_stats_tab_link").click(function() {
    	Plotly.Plots.resize($("#hydro_stats-chart .js-plotly-plot")[0]);
    	Plotly.relayout($("#hydro_stats-chart .js-plotly-plot")[0], {
        	'xaxis.autorange': true,
        	'yaxis.autorange': true
        });
    });
    // $("#dailyAverages_tab_link").click(function() {
    // 	Plotly.Plots.resize($("#dailyAverages-chart .js-plotly-plot")[0]);
    // 	Plotly.relayout($("#dailyAverages-chart .js-plotly-plot")[0], {
    //     	'xaxis.autorange': true,
    //     	'yaxis.autorange': true
    //     });
    // });
    // $("#monthlyAverages_tab_link").click(function() {
    // 	Plotly.Plots.resize($("#monthlyAverages-chart .js-plotly-plot")[0]);
    // 	Plotly.relayout($("#monthlyAverages-chart .js-plotly-plot")[0], {
    //     	'xaxis.autorange': true,
    //     	'yaxis.autorange': true
    //     });
    // });
    // $("#scatterPlot_tab_link").click(function() {
    // 	Plotly.Plots.resize($("#scatterPlot-chart .js-plotly-plot")[0]);
    // 	Plotly.relayout($("#scatterPlot-chart .js-plotly-plot")[0], {
    //     	'xaxis.autorange': true,
    //     	'yaxis.autorange': true
    //     });
    // });
    // $("#scatterPlotLogScale_tab_link").click(function() {
    // 	Plotly.Plots.resize($("#scatterPlotLogScale-chart .js-plotly-plot")[0]);
    // 	Plotly.relayout($("#scatterPlotLogScale-chart .js-plotly-plot")[0], {
    //     	'xaxis.autorange': true,
    //     	'yaxis.autorange': true
    //     });
    // });
    // $("#volumeAnalysis_tab_link").click(function() {
    // 	Plotly.Plots.resize($("#volumeAnalysis-chart .js-plotly-plot")[0]);
    // 	Plotly.relayout($("#volumeAnalysis-chart .js-plotly-plot")[0], {
    //     	'xaxis.autorange': true,
    //     	'yaxis.autorange': true
    //     });
    // });
    $("#forecast_tab_link").click(function() {
        Plotly.Plots.resize($("#forecast-chart .js-plotly-plot")[0]);
        Plotly.relayout($("#forecast-chart .js-plotly-plot")[0], {
        	'xaxis.autorange': true,
        	'yaxis.autorange': true
        });
    });
    $("#forecast_bc_tab_link").click(function() {
        Plotly.Plots.resize($("#forecast-bc-chart .js-plotly-plot")[0]);
        Plotly.relayout($("#forecast-bc-chart .js-plotly-plot")[0], {
        	'xaxis.autorange': true,
        	'yaxis.autorange': true
        });
    });
};

$(function() {
	$("#app-content-wrapper").removeClass('show-nav');
	$(".toggle-nav").removeClass('toggle-nav');

	//make sure active Plotly plots resize on window resize
    window.onresize = function() {
        $('#graph .modal-body .tab-pane.active .js-plotly-plot').each(function(){
            Plotly.Plots.resize($(this)[0]);
        });
    };
    init_map();
    map_events();
    resize_graphs();

    $('#datesSelect').change(function() { //when date is changed
       var sel_val = ($('#datesSelect option:selected').val()).split(',');
       var startdate = sel_val[0];
       $('#forecast-loading').removeClass('hidden');
       get_time_series(watershed, subbasin, streamcomid, startdate);
       $('#forecast-bc-loading').removeClass('hidden');
       get_time_series_bc(watershed, subbasin, streamcomid, startdate, stationcode, stationname);
    });
});

// // Function for the select2 metric selection tool
// $(document).ready(function() {
//     $('#metric_select2').select2({ width: 'resolve' });
// });
//
// $('#metric_select2').on("select2:close", function(e) { // Display optional parameters
//     //console.log("triggered!");
//     let select_val = $( '#metric_select2' ).val();
// 	//console.log(select_val);
//
//     if ( select_val.includes("MASE") ) {
//         $('#mase_param_div').fadeIn()
//     } else {
//         $('#mase_param_div').fadeOut()
//     }
//
//     if ( select_val.includes("d (Mod.)") ) {
//         $('#dmod_param_div').fadeIn()
//     } else {
//         $('#dmod_param_div').fadeOut()
//     }
//
//     if ( select_val.includes("NSE (Mod.)") ) {
//         $('#nse_mod_param_div').fadeIn()
//     } else {
//         $('#nse_mod_param_div').fadeOut()
//     }
//
//     if ( select_val.includes("E1'") ) {
//         $('#lm_eff_param_div').fadeIn()
//     } else {
//         $('#lm_eff_param_div').fadeOut()
//     }
//
//     if ( select_val.includes("D1'") ) {
//         $('#d1_p_param_div').fadeIn()
//     } else {
//         $('#d1_p_param_div').fadeOut()
//     }
//
//     if ( select_val.includes("H6 (MHE)") ) {
//         $('#mean_h6_param_div').fadeIn()
//     } else {
//         $('#mean_h6_param_div').fadeOut()
//     }
//
//     if ( select_val.includes("H6 (MAHE)") ) {
//         $('#mean_abs_H6_param_div').fadeIn()
//     } else {
//         $('#mean_abs_H6_param_div').fadeOut()
//     }
//
//     if ( select_val.includes("H6 (RMSHE)") ) {
//         $('#rms_H6_param_div').fadeIn()
//     } else {
//         $('#rms_H6_param_div').fadeOut()
//     }
// });


// // Event handler for the make table button
// $(document).ready(function(){
//
//     $("#make-table").click(function(){
//         //console.log('Make Table Event Triggered');
//         var model = $('#model option:selected').text();
//         var watershed = 'south_america' //OJO buscar como hacerla generica
//         var subbasin = 'continental' //OJO buscar como hacerla generica
//         var startdate = '';
//         let xName = $("#Station-Name-Tab")
//         let xCode = $("#Station-Code-Tab")
//         let xComid = $("#COMID-Tab")
//         let htmlName = xName.html()
//         let htmlCode = xCode.html()
//         let htmlComid = xComid.html()
//         var arName = htmlName.split(': ')
//         var arCode = htmlCode.split(': ')
//         var arComid = htmlComid.split(': ')
//         let stationname = arName[1];
//         let stationcode = arCode[1];
//         let streamcomid = arComid[1];
//
//         let selected_metrics = $( '#metric_select2' ).val();  // Selected Metrics
// 		let additionalParametersNameList = ["mase_m", "dmod_j", "nse_mod_j", "h6_k_MHE", "h6_k_AHE", "h6_k_RMSHE", "lm_x_bar", "d1_p_x_bar"];
// 		let additionalParametersValuesList = [];
//
// 		let getData = {
// 			'watershed': watershed,
// 			'subbasin': subbasin,
// 			'streamcomid': streamcomid,
// 			'stationcode': stationcode,
// 			'stationname': stationname,
// 			'metrics': selected_metrics,
// 		}
//
// 		for (let i = 0; i < additionalParametersNameList.length; i++) {
// 			metricAbbr = additionalParametersNameList[i];
// 			getData[metricAbbr] = $(`#${metricAbbr}`).val();
// 		}
//
// 		// Creating the table
// 		$.ajax({
// 			url : "make-table-ajax", // the endpoint
// 			type : "GET", // http method
// 			data: getData,
// //			contentType : "json",
//
// 			// handle a successful response
// 			success : function(resp) {
// 				$("#metric-table").show();
//         console.log(resp);
// 				$('#table').html(resp); // Render the Table
// 				//console.log(resp)
// 				//console.log("success"); // another sanity check
// 			},
//
// 			// handle a non-successful response
// 			error : function(xhr, errmsg, err) {
// 				$('#table').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+".</div>"); // add the error to the dom
// 				console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
// 			}
// 		});
// 	});
// });

// Function for the select4 metric selection tool
$(document).ready(function() {
    $('#metric_select4').select2({ width: 'resolve' });
});


$('#metric_select4').on("select2:close", function(e) { // Display optional parameters
    //console.log("triggered!");
    let select_val = $( '#metric_select4' ).val();
	//console.log(select_val);

    if ( select_val.includes("MASE") ) {
        $('#mase_param_div2').fadeIn()
    } else {
        $('#mase_param_div2').fadeOut()
    }

    if ( select_val.includes("d (Mod.)") ) {
        $('#dmod_param_div2').fadeIn()
    } else {
        $('#dmod_param_div2').fadeOut()
    }

    if ( select_val.includes("NSE (Mod.)") ) {
        $('#nse_mod_param_div2').fadeIn()
    } else {
        $('#nse_mod_param_div2').fadeOut()
    }

    if ( select_val.includes("E1'") ) {
        $('#lm_eff_param_div2').fadeIn()
    } else {
        $('#lm_eff_param_div2').fadeOut()
    }

    if ( select_val.includes("D1'") ) {
        $('#d1_p_param_div2').fadeIn()
    } else {
        $('#d1_p_param_div2').fadeOut()
    }

    if ( select_val.includes("H6 (MHE)") ) {
        $('#mean_h6_param_div2').fadeIn()
    } else {
        $('#mean_h6_param_div2').fadeOut()
    }

    if ( select_val.includes("H6 (MAHE)") ) {
        $('#mean_abs_H6_param_div2').fadeIn()
    } else {
        $('#mean_abs_H6_param_div2').fadeOut()
    }

    if ( select_val.includes("H6 (RMSHE)") ) {
        $('#rms_H6_param_div2').fadeIn()
    } else {
        $('#rms_H6_param_div2').fadeOut()
    }
});


// Event handler for the make table button
$(document).ready(function(){

    $("#make-table2").click(function(){
        //console.log('Make Table Event Triggered');
        var model = $('#model option:selected').text();
        var watershed = 'south_america' //OJO buscar como hacerla generica
        var subbasin = 'continental' //OJO buscar como hacerla generica
        var startdate = '';
        let xName = $("#Station-Name-Tab")
        let xCode = $("#Station-Code-Tab")
        let xComid = $("#COMID-Tab")
        let htmlName = xName.html()
        let htmlCode = xCode.html()
        let htmlComid = xComid.html()
        var arName = htmlName.split(': ')
        var arCode = htmlCode.split(': ')
        var arComid = htmlComid.split(': ')
        let stationname = arName[1];
        let stationcode = arCode[1];
        let streamcomid = arComid[1];

        let selected_metrics = $( '#metric_select4' ).val();  // Selected Metrics
		let additionalParametersNameList = ["mase_m2", "dmod_j2", "nse_mod_j2", "h6_k_MHE2", "h6_k_AHE2", "h6_k_RMSHE2", "lm_x_bar2", "d1_p_x_bar2"];
		let additionalParametersValuesList = [];

		let getData = {
			'watershed': watershed,
			'subbasin': subbasin,
			'streamcomid': streamcomid,
			'stationcode': stationcode,
			'stationname': stationname,
			'metrics': selected_metrics,
		}

		for (let i = 0; i < additionalParametersNameList.length; i++) {
			metricAbbr = additionalParametersNameList[i];
			getData[metricAbbr] = $(`#${metricAbbr}`).val();
		}
    console.log(getData);
		// Creating the table
		$.ajax({
			url : "make-table-ajax2", // the endpoint
			type : "GET", // http method
			data: getData,
//			contentType : "json",

			// handle a successful response
			success : function(resp) {
				$("#metric-table2").show();
				$('#table2').html(resp); // Render the Table
				//console.log(resp)
				//console.log("success"); // another sanity check
			},

			// handle a non-successful response
			error : function(xhr, errmsg, err) {
				$('#table2').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+".</div>"); // add the error to the dom
				console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
			}
		});
	});
});

function get_available_dates(watershed, subbasin, streamcomid) {
	$.ajax({
		type: 'GET',
		url: 'get-available-dates/',
		dataType: 'json',
		data: {
			'watershed': watershed,
			'subbasin': subbasin,
			'streamcomid': streamcomid
		},
		error: function() {
			$('#dates').html(
				'<p class="alert alert-danger" style="text-align: center"><strong>An error occurred while retrieving the available dates</strong></p>'
			);

			setTimeout(function() {
				$('#dates').addClass('hidden')
			}, 5000);
        },
        success: function(dates) {
        	datesParsed = JSON.parse(dates.available_dates);
        	$('#datesSelect').empty();

        	$.each(datesParsed, function(i, p) {
        		var val_str = p.slice(1).join();
        		$('#datesSelect').append($('<option></option>').val(val_str).html(p[0]));
        	});
        }
    });
}

function get_time_series(watershed, subbasin, streamcomid, startdate) {
    $('#forecast-loading').removeClass('hidden');
    $('#forecast-chart').addClass('hidden');
    $('#dates').addClass('hidden');
    $.ajax({
        type: 'GET',
        url: 'get-time-series/',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'streamcomid': streamcomid,
            'startdate': startdate
        },
        error: function() {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the forecast</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function() {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function(data) {
            if (!data.error) {
                // $('#forecast-loading').addClass('hidden');
                $('#dates').removeClass('hidden');
                //$loading.addClass('hidden');
                $('#forecast-chart').removeClass('hidden');
                $('#forecast-chart').html(data);

                //resize main graph
                Plotly.Plots.resize($("#forecast-chart .js-plotly-plot")[0]);
                Plotly.relayout($("#forecast-chart .js-plotly-plot")[0], {
                	'xaxis.autorange': true,
                	'yaxis.autorange': true
                });

                var params = {
                    watershed: watershed,
                    subbasin: subbasin,
                    streamcomid: streamcomid,
                    startdate: startdate,
                };

                $('#submit-download-forecast').attr({
                    target: '_blank',
                    href: 'get-forecast-data-csv?' + jQuery.param(params)
                });

                $('#download_forecast').removeClass('hidden');

            } else if (data.error) {
                $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the forecast</strong></p>');
                $('#info').removeClass('hidden');

                setTimeout(function() {
                    $('#info').addClass('hidden')
                }, 5000);
            } else {
                $('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
            }
        }
    });
}

function get_time_series_bc(watershed, subbasin, streamcomid, startdate, stationcode, stationname) {
    $('#forecast-bc-loading').removeClass('hidden');
    $('#forecast-bc-chart').addClass('hidden');
    $('#dates').addClass('hidden');
    $.ajax({
        type: 'GET',
        url: 'get-time-series-bc/',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'streamcomid': streamcomid,
            'startdate': startdate,
            'stationcode': stationcode,
            'stationname': stationname
        },
        error: function() {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the corrected forecast</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function() {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function(data) {
            if (!data.error) {
                $('#forecast-bc-loading').addClass('hidden');
                $('#forecast-loading').addClass('hidden');
                $('#dates').removeClass('hidden');
                //$loading.addClass('hidden');
                $('#forecast-chart').removeClass('hidden');
                //resize main graph

                $('#forecast-bc-chart').removeClass('hidden');
                $('#forecast-bc-chart').html(data);


                //resize main graph
                Plotly.Plots.resize($("#forecast-bc-chart .js-plotly-plot")[0]);
                Plotly.relayout($("#forecast-bc-chart .js-plotly-plot")[0], {
                	'xaxis.autorange': true,
                	'yaxis.autorange': true
                });

                var params = {
                    watershed: watershed,
                    subbasin: subbasin,
                    streamcomid: streamcomid,
                    startdate: startdate,
                    stationcode: stationcode,
                    stationname: stationname
                };

                $('#submit-download-forecast-bc').attr({
                    target: '_blank',
                    href: 'get-forecast-bc-data-csv?' + jQuery.param(params)
                });

                $('#download_forecast_bc').removeClass('hidden');

            } else if (data.error) {
                $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the corrected forecast</strong></p>');
                $('#info').removeClass('hidden');

                setTimeout(function() {
                    $('#info').addClass('hidden')
                }, 5000);
            } else {
                $('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
            }
        }
    });
}
