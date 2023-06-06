from tethys_sdk.base import TethysAppBase
from tethys_sdk.app_settings import CustomSetting


class HistoricalValidationToolColombia(TethysAppBase):
    """
    Tethys app class for Historical Validation Tool Colombia.
    """

    name = 'Historical Validation Tool Colombia'
    description = ''
    package = 'historical_validation_tool_colombia'  # WARNING: Do not change this value
    index = 'home'
    icon = f'{package}/images/icon.gif'
    root_url = 'historical-validation-tool-colombia'
    color = '#002255'
    tags = '"Geoglows", "Colombia", "Historical data", "Flood forecast"'
    enable_feedback = False
    feedback_emails = []