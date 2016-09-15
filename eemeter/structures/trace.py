import pandas as pd
import warnings


class EnergyTrace(object):
    """ Container for time series energy data.

    Parameters
    ----------
    interpretation : str
        The way this energy time series in the :code:`data` attribute should be
        interpreted. The complete list of supported options is as follows:

        - :code:`ELECTRICITY_CONSUMPTION_SUPPLIED`: Represents the amount of
          utility-supplied electrical energy consumed on-site, as metered at
          a single usage point, such as a utility-owned electricity meter.
          Specifically does not include consumption of electricity generated
          on site, such as by locally installed solar photovoltaic panels.
        - :code:`ELECTRICITY_CONSUMPTION_TOTAL`: Represents the amount of
          electrical energy consumed on-site, including both utility-supplied
          and on-site generated electrical energy. Equivalent, for a single
          electricity meter, to :code:`ELECTRICITY_CONSUMPTION_SUPPLIED` -
          :code:`ELECTRICITY_ON_SITE_GENERATION_CONSUMED`.
        - :code:`ELECTRICITY_CONSUMPTION_NET`: Represents the amount of
          utility-supplied electrical energy consumed on-site minus the amount
          of unconsumed electrical energy generated on site and fed back into
          the grid at a single usage point, such as a utility-owned electricity
          meter. Equivalent, for a single electricity meter, to
          :code:`ELECTRICITY_CONSUMPTION_SUPPLIED` -
          :code:`ELECTRICITY_ON_SITE_GENERATION_UNCONSUMED`.
        - :code:`ELECTRICITY_ON_SITE_GENERATION_TOTAL`: Represents the amount
          of locally generated electrical energy consumed on-site plus the
          amount of locally generated elecrical energy returned to the grid,
          as metered at a single usage point. Equivalent, for a single
          electricity meter, to :code:`ELECTRICITY_ON_SITE_GENERATION_CONSUMED`
          + :code:`ELECTRICITY_ON_SITE_GENERATION_UNCONSUMED`.
        - :code:`ELECTRICITY_ON_SITE_GENERATION_CONSUMED`: Represents the
          amount of locally generated electrical energy consumed on-site, such
          as energy generated by solar photovoltaic panels.
        - :code:`ELECTRICITY_ON_SITE_GENERATION_UNCONSUMED`: Represents the
          amount of excess locally generated energy, which instead of being
          consumed on-site, is fed back into the grid or sold back a utility.
        - :code:`NATURAL_GAS_CONSUMPTION_SUPPLIED`: Represents the amount of
          energy supplied by a utility in the form of natural gas and used on
          site, as metered at a single usage point. Though under the labeling
          scheme used for electricity interpretetations the labels
          :code:`NATURAL_GAS_CONSUMPTION_TOTAL` and
          :code:`NATURAL_GAS_CONSUMPTION_NET` would be equivalent for natural
          gas, :code:`NATURAL_GAS_CONSUMPTION_SUPPLIED` is prefered for its
          greater specificity.

    data : pandas.DataFrame, default None
        A pandas DataFrame with two columns and a timezone-aware DatetimeIndex.
        Timestamps in the index are assumed to refer to the start of each
        period, and the period ends are assumed to coincide with the start
        of the following period. Thus, the value of the last datetime should
        always be :code:`NaN`, since is purpose is only to cap the end of the
        last period, and not to represent a time period over which energy was
        consumed. The DatetimeIndex does not need to have uniform frequency,
        such as those specified in pandas using the :code:`freq` attribute.

        - :code:`value`: Amount of energy between this index and the next.
        - :code:`estimated`: Whether or not the value was estimated.
          Particularly relevant for monthly billing data.

        If :code:`serializer` instance is provided, this should instead be
        records in the format expected by the serializer.
    unit : str
        The name of the unit in which the energy time series is given. These
        names are normalized to either :code:`'KWH'` or :code:`'THERM'` as
        follows:

        - :code:`'kwh'` becomes :code:`'KWH'` with no unit conversion
          multiplier.
        - :code:`'kWh'` becomes :code:`'KWH'` with no unit conversion
          multiplier.
        - :code:`'KWH'` becomes :code:`'KWH'` with no unit conversion
          multiplier.
        - :code:`'therm'` becomes :code:`'THERM'` with no unit conversion
          multiplier.
        - :code:`'therms'` becomes :code:`'THERM'` with no unit conversion
          multiplier.
        - :code:`'thm'` becomes :code:`'THERM'` with no unit conversion
          multiplier.
        - :code:`'THERM'` becomes :code:`'THERM'` with no unit conversion
          multiplier.
        - :code:`'THERMS'` becomes :code:`'THERM'` with no unit conversion
          multiplier.
        - :code:`'THM'` becomes :code:`'THERM'` with no unit conversion
          multiplier.
        - :code:`'wh'` becomes :code:`'KWH'` with a unit conversion
          multiplier of :code:`0.001`.
        - :code:`'Wh'` becomes :code:`'KWH'` with a unit conversion
          multiplier of :code:`0.001`.
        - :code:`'WH'` becomes :code:`'KWH'` with a unit conversion
          multiplier of :code:`0.001`.

    placeholder : bool
        Indicates that this instance is a placeholder - that while for some
        reason the data associated with it is unavailable, its existence is
        still important in considering a whole site.
    serializer : consumption.BaseSerializer
        Serializer instance to be used to deserialize records into a pandas
        dataframe. Must supply the :code:`to_dataframe(records)` method.
    """

    # target_unit must be one of 'kWh' or 'therm'
    UNIT_NORMALIZATION = {
        'kwh': {
            'target_unit': 'KWH',
            'multiplier': 1.0,
        },
        'kWh': {
            'target_unit': 'KWH',
            'multiplier': 1.0,
        },
        'KWH': {
            'target_unit': 'KWH',
            'multiplier': 1.0,
        },
        'therm': {
            'target_unit': 'THERM',
            'multiplier': 1.0,
        },
        'therms': {
            'target_unit': 'THERM',
            'multiplier': 1.0,
        },
        'thm': {
            'target_unit': 'THERM',
            'multiplier': 1.0,
        },
        'THERM': {
            'target_unit': 'THERM',
            'multiplier': 1.0,
        },
        'THERMS': {
            'target_unit': 'THERM',
            'multiplier': 1.0,
        },
        'THM': {
            'target_unit': 'THERM',
            'multiplier': 1.0,
        },
        'wh': {
            'target_unit': 'KWH',
            'multiplier': 0.001,
        },
        'Wh': {
            'target_unit': 'KWH',
            'multiplier': 0.001,
        },
        'WH': {
            'target_unit': 'KWH',
            'multiplier': 0.001,
        },
    }

    INTERPRETATIONS = [
        'ELECTRICITY_CONSUMPTION_SUPPLIED',
        'ELECTRICITY_CONSUMPTION_TOTAL',
        'ELECTRICITY_CONSUMPTION_NET',
        'ELECTRICITY_ON_SITE_GENERATION_TOTAL',
        'ELECTRICITY_ON_SITE_GENERATION_CONSUMED',
        'ELECTRICITY_ON_SITE_GENERATION_UNCONSUMED',
        'NATURAL_GAS_CONSUMPTION_SUPPLIED',
    ]

    def __init__(self, interpretation, data=None, records=None, unit=None,
                 placeholder=False, serializer=None):

        self._set_interpretation(interpretation)
        self._set_data(data, records, unit, placeholder, serializer)

    def __repr__(self):
        if self.placeholder:
            return (
                "EnergyTrace(interpretation={}, placeholder=True)"
                .format(self.interpretation)
            )
        else:
            return (
                "EnergyTrace(interpretation={}, unit={}, data=pd.Dataframe({}))"
                .format(self.interpretation, self.unit, self.data.shape)
            )

    def _set_interpretation(self, interpretation):
        if interpretation in self.INTERPRETATIONS:
            self.interpretation = interpretation
        else:
            message = (
                'Unsupported interpretation: "{}".'
                .format(interpretation)
            )
            raise ValueError(message)

    def _set_data(self, data, records, unit, placeholder, serializer):
        if (placeholder and data is None and records is None and
                serializer is None):
            # placeholder initialization option.
            self.data = None
            self.unit = None
            self.placeholder = True
            return
        elif (records is not None and serializer is not None and
                data is None and not placeholder):
            self._set_unit(unit)
            data = serializer.to_dataframe(records)
        elif (data is not None and records is None and serializer is None and
                not placeholder):
            self._set_unit(unit)

            if not isinstance(data.index, pd.DatetimeIndex):
                message = (
                    '`data` must be indexed with a pandas.DatetimeIndex.'
                )
                raise ValueError(message)

            if not all(data.columns == ['value', 'estimated']):
                message = (
                    'The pandas.DataFrame supplied in `data` must have the'
                    ' columns `[\'value\', and \'estimated\']`.'
                )
                raise ValueError(message)
        else:
            message = (
                'EnergyTrace objects must be initialized in one of the'
                ' following ways, with unused attributes left at their default'
                ' values:\n\n'
                '  1) by suppling a pandas DatetimeIndex\'ed DataFrame with'
                ' the columns `[\'value\', \'estimated\']` using `data`'
                ' argument,\n'
                '  2) by suppling `records` and a `serializer` class that'
                ' can read those records and turn them into a pandas'
                ' DatetimeIndex\'ed DataFrame, or\n'
                '  3) by setting `placeholder=True`.\n\n'
                'However, you supplied `data={}`, `records={}`, '
                '`serializer={}`, and `placeholder={}`, which fits none of'
                ' these options.'
                .format(data, records, serializer, placeholder)
            )
            raise ValueError(message)

        self.data = data
        self.data.value = data.value * self.unit_multiplier
        self.placeholder = False

    def _set_unit(self, unit):
        if unit in self.UNIT_NORMALIZATION:
            self.unit = self.UNIT_NORMALIZATION[unit]["target_unit"]
            self.unit_multiplier = self.UNIT_NORMALIZATION[unit]["multiplier"]
        else:
            message = 'Unsupported unit: "{}".'.format(unit)
            raise ValueError(message)


class EnergyTraceSet(object):
    ''' A container for energy traces which ensures that each is labeled.

    Parameters
    ----------
    traces : list or dict of eemeter.structures.EnergyTrace objects
        EnergyTrace objects to be included in this list.
    labels : list of str
        Unique labels for traces, used only if `traces` is not a dictionary.
    '''

    def __init__(self, traces, labels=None):

        if isinstance(traces, dict):
            if labels is not None:
                message = (
                    'Ignoring supplied `labels` since `traces` was given as'
                    ' a dict.'
                )
                warnings.warn(message)

            self.traces = traces
            return

        if labels is None:
            labels = self._generate_default_labels(traces)

        self._validate_lengths(traces, labels)
        self._validate_uniqueness(labels)

        self.traces = {label: trace for label, trace in zip(labels, traces)}

    def __repr__(self):
        return "EnergyTraceSet(traces={})".format(self.traces)

    def _generate_default_labels(self, traces):
        return [str(i) for i, _ in enumerate(traces)]

    def _validate_lengths(self, traces, labels):
        # make sure zip doesn't miss any
        if len(traces) != len(labels):
            message = (
                'Should be the same number of labels as traces,'
                ' but got {} labels for {} traces.'
                .format(len(labels), len(traces))
            )
            raise ValueError(message)

    def _validate_uniqueness(self, labels):
        if len(labels) != len(set(labels)):
            message = (
                'Labels should be unique, but received the following labels,'
                ' which are not all unique: {}.'
                .format(labels)
            )
            raise ValueError(message)

    def itertraces(self):
        ''' Iterates over traces, yielding `(label, trace)` pairs.
        '''
        for label, trace in self.traces.items():
            yield label, trace
