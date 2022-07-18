from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import CustomSetting, SpatialDatasetServiceSetting

class HistoricalValidationToolColombia(TethysAppBase):
    """
    Tethys app class for Historical Validation Tool Colombia.
    """

    name = 'Historical Validation Tool Colombia'
    index = 'home'
    icon = 'historical_validation_tool_colombia/images/historic_validation_colombia_logo.png'
    package = 'historical_validation_tool_colombia'
    root_url = 'historical-validation-tool-colombia'
    color = '#002255'
    description = 'This app combines the observed data and the simulated data from the GEOGloWS ECMWF Streaamflow Services in Colombia.'
    tags = '"Hydrology", "Time Series", "Bias Correction", "Hydrostats", "GEOGloWS", "Historical Validation Tool", "Colombia"'
    enable_feedback = False
    feedback_emails = []

    def spatial_dataset_service_settings(self):
        """
		Spatial_dataset_service_settings method.
		"""
        return (
            SpatialDatasetServiceSetting(
                name='main_geoserver',
                description='spatial dataset service for app to use (https://tethys2.byu.edu/geoserver/rest/)',
                engine=SpatialDatasetServiceSetting.GEOSERVER,
                required=True,
            ),
        )

    def custom_settings(self):
        return (
            CustomSetting(
                name='workspace',
                type=CustomSetting.TYPE_STRING,
                description='Workspace within Geoserver where web service is',
                required=True,
                    default='colombia_hydroviewer',
            ),
            CustomSetting(
                name='region',
                type=CustomSetting.TYPE_STRING,
                description='GESS Region',
                required=True,
                default='south_america-geoglows',
            ),
            CustomSetting(
                name='hydroshare_resource_id',
                type=CustomSetting.TYPE_STRING,
                description='Hydroshare Resource ID',
                required=True,
            ),
            CustomSetting(
                name='username',
                type=CustomSetting.TYPE_STRING,
                description='Hydroshare Username',
                required=True,
            ),
            CustomSetting(
                name='password',
                type=CustomSetting.TYPE_STRING,
                description='Hydroshare Password',
                required=True,
            ),
        )
