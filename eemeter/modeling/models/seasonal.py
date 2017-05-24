import holidays
import numpy as np
import pandas as pd

from eemeter.modeling.models.elastic_net_base import ElasticNetCVBaseModel


class SeasonalElasticNetCVModel(ElasticNetCVBaseModel):
    ''' Linear regression using daily frequency data to build a model of
    formatted energy trace data that takes into account HDD, CDD, day of week,
    month, and holiday effects, with elastic net regularization.

    Parameters
    ----------
    cooling_base_temp : float
        Base temperature (degrees F) used in calculating cooling degree days.
    heating_base_temp : float
        Base temperature (degrees F) used in calculating heating degree days.
    custom_holidays : None for United States holidays, or pass in a custom object
        which implements the "get" method as in the holidays package.
    '''

    def __init__(self, cooling_base_temp=65, heating_base_temp=65,
                 modeling_period_interpretation='baseline',
                 custom_holidays = None):

        super(SeasonalElasticNetCVModel, self).__init__(
            cooling_base_temp, heating_base_temp)
        self.modeling_period_interpretation = modeling_period_interpretation
        self.custom_holidays = custom_holidays

    def __repr__(self):
        return (
            'SeasonalElasticNetCVModel(cooling_base_temp={},'
            ' heating_base_temp={})'
            .format(
                self.cooling_base_temp,
                self.heating_base_temp,
            )
        )

    def _model_data_from_input_data(self, input_data):

        model_freq = pd.tseries.frequencies.Day()

        model_data = input_data.resample(model_freq).agg(
            {'energy': np.sum, 'tempF': np.mean})

        model_data = model_data.dropna()

        if model_data.empty:
            message = (
                "No data left for model fit after resampling to daily and"
                " dropping NaN values."
            )
            raise ValueError(message)

        model_data.loc[:, 'CDD'] = np.maximum(
            model_data.tempF - self.cooling_base_temp, 0.)
        model_data.loc[:, 'HDD'] = np.maximum(
            self.heating_base_temp - model_data.tempF, 0.)
        return model_data

    def _patsy_formula(self, model_data):

        formula = self.base_formula

        # Make sure these factors have enough levels to not
        # cause issues.
        if len(np.unique(model_data.index.month)) >= 12:
            formula += (
                ' + CDD * C(tempF.index.month)'
                ' + HDD * C(tempF.index.month)'
                ' + C(tempF.index.month)'
            )

        if len(np.unique(model_data.index.weekday)) >= 7:
            formula += (
                ' + (CDD) * C(tempF.index.weekday)'
                ' + (HDD) * C(tempF.index.weekday)'
                ' + C(tempF.index.weekday)'
            )

        holiday_names = self._holidays_indexed(
            model_data.index)

        if len(np.unique(holiday_names)) == 11:
            model_data.loc[:, 'holiday_name'] = self._holidays_indexed(
                model_data.index)
            formula += " + C(holiday_name)"
        return formula

    @staticmethod
    def _holidays_indexed(dt_index):
        if self.custom_holidays is None:
            holidays_raw = holidays.UnitedStates()
        else:
            holidays_raw = self.custom_holidays

        def clean_holiday_name(dt):
            raw_name = holidays_raw.get(dt, "none")
            if raw_name.endswith(" (Observed)"):
                return raw_name[:-11]
            else:
                return raw_name

        holiday_names = pd.Series(dt_index.map(clean_holiday_name),
                                  index=dt_index)
        return holiday_names

    def _model_data_from_demand_fixture_data(self, demand_fixture_data):
        model_freq = pd.tseries.frequencies.Day()

        # needs only tempF
        model_data = demand_fixture_data.resample(model_freq).agg(
            {'tempF': np.mean})

        model_data.loc[:, 'CDD'] = np.maximum(model_data.tempF -
                                              self.cooling_base_temp, 0.)
        model_data.loc[:, 'HDD'] = np.maximum(self.heating_base_temp -
                                              model_data.tempF, 0.)

        holiday_names = self._holidays_indexed(model_data.index)

        model_data.loc[:, 'holiday_name'] = holiday_names
        return model_data
