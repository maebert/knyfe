#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    knyfe

    copyright (c) 2011-2012 by Manuel Ebert.
    license: MIT, see LICENSE for more details.
"""

import numpy  as np
import sys
import os
try:
    import simplejson as json
except ImportError:
    import json
import logging
import random
import copy
import glob
import tablib
import csv

__title__ = 'knyfe'
__version__ = '0.4.3'
__author__ = 'Manuel Ebert'
__license__ = 'MIT'
__copyright__ = 'Copyright 2011-2012 Manuel Ebert'

class Data:
    """A generic data manager for exploring generic datasets."""
    logging.basicConfig(format="%(levelname)-7s %(asctime)s:  %(message)s", level=logging.INFO)
    log = logging.getLogger("Data Analysis")

    # Define some scales
    NOMINAL = 0     # For Strings and Booleans
    ORDINAL = 1     # For Integers
    CARDINAL = 2    # For Floats 
    ARRAY = 3       # For tuples, lists, np.arrays of fixed length across dataset
    FLEX_ARRAY = 4  # For tuples, lists, np.arrays of flexible length across dataset
    UNKNOWN = 98    # For WE DON't KNOW.

    def __init__(self, *sources):
        """ Constructs a new Dataset from given sources. Sources may be:
        * Strings, interpreted as paths to JSON files
        * dictionaries, interpreted as single samples
        * lists of dictionaries
        * other Data instances
        Or any combination of the above. The resulting Dataset will join all the sources.
        """
        self.data = []
        for source in sources:
            if type(source) in (str, unicode):
                filenames = glob.glob(source)
                if filenames:
                    self.load(*filenames)
                else:
                    self.log.error("{} does not match any files".format(source))
            elif type(source) is dict:
                self.data.append(source)
            elif type(source) in (list, tuple):
                self.data.extend(source)
            elif isinstance(source, self.__class__):
                self.data.extend(source.data)
            elif hasattr(source, 'data') and type(source.data) is list:
                # Wild guess here, but may be useful for subclassing
                self.data.extend(source.data)
            else:
                self.log.error("Can't interpret source {}".format(source))

        self.str_label = "Unnamed Dataset"
        self.dependent = self._np1d([])

        """Tries to convert n into an int or float, returns n if that fails."""
    def _num(self, n):
        """Tries to convert n into an int or float, returns n if that fails."""
        try:
            return int(n)
        except ValueError:
            pass
        try:
            return float(n)
        except ValueError:
            return n


    def _new(self, data=[]):
        """Creates an empty dataset, copying over dependent varuables and label from the current dataset"""
        return self.__class__(data).dependent_vars(self.dependent).label(self.label()+"*")

    def __getattr__(self, attr):
        if attr in self.attributes:
            return self.get(attr)
        else:
            raise AttributeError


    def __add__(self, other):
        new_data = self._new()
        new_data.label(self._combine_labels(other))
        # Extend data
        new_data.data.extend(self.data)
        if hasattr(other, "data"):
            new_data.data.extend(other.data)
        elif type(other) in (list, tuple):
            new_data.data.extend(other)
        return new_data

    def __iadd__(self, other):
        if hasattr(other, "data"):
            self.data.extend(other.data)
        elif type(other) in (list, tuple):
            self.data.extend(other)
        return self

    def _combine_labels(self, other, template="{self} + {other}"):
        """Combines the Data's label with another datasets label using a given template.
        The template should contain {self} and {other} as placeholders."""
        # Pick a nice label
        if hasattr(other, "label"):
            if self.label() == "Unnamed Dataset":
                return other.label()
            elif other.label() == "Unnamed Dataset":
                return self.label()
            else:
                return template.format(self=self.label(), other=other.label())

    def __sub__(self, other):
        new_data = self._new()
        new_data.label(self._combine_labels(other, template="{self} - {other}"))
        if type(other) not in (list, tuple):
            other = other.data
        diff = [sample for sample in self.data if not sample in other]
        new_data.data = diff
        return new_data

    def __isub__(self, other):
        if type(other) not in (list, tuple):
            other = other.data
        self.data = [sample for sample in self.data if not sample in other]
        return self

    def dependent_vars(self, *variables):
        """Sets or returns the dependent variables of the dataset.
        Use Data.depentend(None) to clear all dependent variables."""
        if not variables:
            return self.dependent
        else:
            if not variables[0]:
                self.dependent = self._np1d([])
            else:
                self.dependent = self._np1d(variables)
            return self

    def label(self, label=None):
        """Sets or returns the label of the dataset."""
        if not label:
            return self.str_label
        else:
            self.str_label = label
            return self


    def _np1d(self, anything, fallback=None):
        """Converts anything into a numpy 1d-array.
        Atoms will be wrapped, lists or tuples directly converted. If anything
        evaluates to False the fallback will be used instead)"""
        anything = anything or fallback
        if type(anything) not in (list, tuple, np.ndarray):
            anything = [anything]
        return np.asarray(anything)


    def add_attribute(self, attribute, values):
        """Adds a new attribute with given values, eg.
        mydata.add_attribute('distance', mydata.finish - mydata.start )"""
        if len(values) != len(self):
            self.log.error("Length of values must match length of dataset!")
            return self
        values = values.tolist()
        for index, s in enumerate(self.data):
            s[attribute] = values[index]
        return self

    def map(self, new_attribute, function):
        """Creates a new attribute in each sample by mapping an existing one using the given function. 
        mydata.map('life_expectancy', lambda s: 82 - s['age'])
        Will create an attribute 'life_expectancy' in each sample of the dataset."""
        for sample in self.data:
            sample[new_attribute] = function(sample)
        return self

    def extend(self, other_data):
        """Appends a different Data object or list of data samples to self.data"""
        if type(other_data) is list:
            self.data.extend(other_data)
        elif hasattr(other_data, 'data'):
            self.data.extend(other_data.data)

    def import_csv(self, filename, delimiter=',', quotechar='"'):
        """Imports an CSV files. First row must be a header row!"""
        with open(filename) as data_file:
            reader = csv.reader(data_file, delimiter=delimiter, quotechar=quotechar)
            header = [h.strip() for h in reader.next()]
            for row in reader:
                self.data.append({k: self._num(v) for k, v in zip(header, row)})


    def load(self, *filenames):
        """Opens specified files and loads their data into self.data"""
        for filename in filenames:
            with open(filename) as data_file:
                self.log.info("Loading '{}'...".format(filename))
                self.data.extend(json.load(data_file))

    def save(self, filename):
        """Saves the current dataset as JSON to the given filename."""
        with open(filename, 'w') as data_file:
            json.dump(self.data, data_file, indent=2)

    def export(self, filename, format=None):
        """Exports the current dataset.
        Format from export will be guessed from file extension, or can be specified explicitly.
        Format may be
         - 'csv' for comma separated value
         - 'xlsx' for Excel 07 or newer
         - 'xls' for legacy Excel
         - 'ods' for open document spreadsheet
         - 'html' for an html file
         """
        modes = {
            'xlsx' : 'wb', 'xls' : 'wb', 'ods' : 'wb',
            'html': 'w', 'csv': 'w'
        }

        if not format:
            name, ext = os.path.splitext(filename)
            format = ext[1:]

        if not format in modes:
            self.log.warn("Invalid export format '%s'. Valid options are csv, xlsx, xls, ods and html." % format)
            return

        # Prepare a tablib object for exporting
        all_keys = set(key for d in self.data for key in d)
        new_data = copy.deepcopy(self.data)
        for sample in new_data:
            sample.update((k,None) for k in all_keys - sample.viewkeys())
        
        tab = tablib.Dataset()
        tab._set_dict(new_data)

        if not filename.endswith(format):
            filename += "." + format
        with open(filename, modes[format]) as f:
            f.write(getattr(tab, format))
            self.log.info("Saved to %s" % filename)


    def __len__(self):
        return len(self.data)


    def __repr__(self):
        return "<%s (%d samples)>" % (self.label(), len(self))

    __default = object()
    def get(self, attribute, missing=__default):
        """Gets all values of an attribute across all samples.
        If missing is set, missing values will be replaced by the value of missing."""
        if missing is Data.__default:
            return np.asarray([date[attribute] for date in self.data if attribute in date])
        else:
            return np.asarray([date[attribute] if attribute in date else missing for date in self.data ])


    def get_once(self, attribute, check_unique = True):
        """Gets the value of the attribute in the first sample of the dataset. 
        By default, checks whether all data samples have the same value and echoes a
        warning otherwise. This can be turned off for increased performance."""
        if not len(self):
            self.log.warn("asking for %s, but no data in dataset", attribute)
            return None
        if check_unique and len(set(d[attribute] for d in self.data)) > 1:
            self.log.warn("more than one value for %s", attribute)
        return self.data[0][attribute]


    def mean(self, *variables):
        """Returns the mean value of the dependent variables, or the variables given
        as the argument (string or list of strings)"""
        variables = self._np1d(variables) if variables else self.dependent
        if variables == 1:
            return np.mean(self.get(variables[0]))
        else:
            return np.asarray([np.mean([self.get(var) for var in variables])])
        
    @property
    def attributes(self):
        return {attr for sample in self.data for attr in sample}

    def get_set(self, attribute):
        """Returns a set of all values present in the dataset for a given attribute"""        
        return sorted(set(self.get(attribute)))


    def median_split(self, attribute):
        """Returns two datasets, split at the median of the given attribute"""
        data_median = np.median(self.get(attribute))
        set0 = self.filter(lambda d: d[attribute] < data_median)
        set0 = self.filter(lambda d: d[attribute] >= data_median)
        return set0, set1


    def toggle_verbose(self, verbose=False):
        """If True, log all info, else log only warnings and errors."""
        self.log.setLevel(logging.DEBUG if verbose else logging.WARNING)


    def filter(self, _func=__default, **kwargs):
        """Returns a Data object with only the data that matches the filter.

            data.filter(subject=8)

        Will return all data files of subject 8. Multiple filters can be used:

            data.filter(subject=8, condition=2)

        which is equivalent to

            data.filter(subject=8).filter(condition=2)

        If value is a list or tuple, filter will check if the data's subject is a
        value of this list or tuple, as in

            data.filter(subject=(11, 12, 13))

        Which will return all data of subjects 11, 12 and 13. If only a string is
        given, filter will retain all data that have that string in their dict and
        don't evaluate to False, e.g.

            data.filter('light')

        will keep data that looks like {'light': True} or {'light': 'on'}, but not
        {'light': 0} or {'LIGHT': True}.

        If the first argument is an boolean array, it will be used to select samples:

            data.filter(data.age > 18)

        Note that in this case data.age must not have any missing values, because then
        `data.age > 18` will be shorter than data itself. 

        Alternatively, a function may be given to implement more complex filters:

            data.filter(lambda d: d['age'] > 18)

        Will return all data where the age key is greater than 18."""
        def _all(boollist):
            return reduce(lambda b1, b2: b1 and b2, boollist)
        def _condition(c, v):
            if type(v) in (list, tuple, np.ndarray):
                return lambda data: c in data and data[c] in v
            else:
                return lambda data: c in data and data[c] == v

        if _func is not None and callable(_func):
            return self._new([trial for trial in self.data if _func(trial)]).filter(**kwargs)
        elif _func is not None and type(_func) is str:
            return self.filter(lambda trial: trial.has_key(_func) and trial[_func], **kwargs)
        elif _func is not None and type(_func) is np.ndarray and _func.dtype is np.dtype('bool'):
            if len(_func) != len(self):
                self.log.error("Length of boolean filter does not match length of dataset. Missing values? Use filter(Data.get('attribute', missing=NaN)) instead.")
                return self.filter(**kwargs)
            else:
                return self._new([trial for index, trial in enumerate(self.data) if _func[index]]).filter(**kwargs)
        elif kwargs:           
            conditions = [_condition(c, v) for c, v in kwargs.iteritems()]
            return self.filter(lambda trial: _all([c(trial) for c in conditions]))
        else:
            return self


    def remove_outliers(self, variables=None, cutoff=3, within=None):
        """Removes data samples based on the variance of the independent variables.
        If variables is not a string or list of strings, the independent variables of
        the data set will be used. All samples that are further then cutoff standard
        deviations from the data sets mean will be removed. If the within arg is passed,
        this will be done separately for all subsets with that attribute, ie.

            data.remove_outliers(within='subject', cutoff=2)

        Will remove all outliers that are more then 2 stds away from the respectively
        subject's mean, not the population mean. Returns a new data set."""
        result = self._new([])
        variables = self._np1d(variables, fallback = self.dependent)

        def _threshold(data):
            for var in variables:
                e = data.get(var)
                threshold = np.mean(e) + cutoff * np.std(e)
                new_data = data.filter(lambda d: d[var] < threshold)
                return new_data

        if not variables:
            self.log.error("Remove outliers: no variables given in method call, and no dependent variables defined on dataset.")
            return self
        elif within:
            for subject in self.get_set(within):
                subject_data = self.filter(subject=subject)
                new_data = _threshold(subject_data)
                result.extend(new_data)
                self.log.info("Subject %d: removing %3d samples (%-4d remaining)", subject, len(subject_data) - len(new_data), len(new_data))
        else:
            result.extend(_threshold(self))

        self.log.info("Removed %3d samples (%-4d remaining)",  len(self) - len(result), len(result))
        return result


    def _scales(self):
        """Analyses the data and guesses a scale for each attribute present in dataset.
        Will construct a scales variable containing information on this scale."""
        def _guess_scale(value):
            if type(value) is float:
                return Data.CARDINAL
            elif type(value) is int:
                return Data.ORDINAL
            elif type(value) in (str, unicode, bool):
                return Data.NOMINAL
            elif type(value) in (tuple, list, np.ndarray):
                return Data.ARRAY
            else:
                return Data.UNKNOWN

        # Algorithm: Run through each sample of dataset
        # Ad each attribute to our scale dict. The scale constants are ordered such
        # that 0 is nominal and the least we can say about any scale. Hence we first
        # assume the best for each of our attributes (namely, all are flots and cardinal),
        # and when encountering new data types, keep the minimum we can certainly say
        # about our scale.
        self.scales = {}
        for sample in self.data:
            for attr in sample:
                self.scales[attr] = min(_guess_scale(sample[attr]), self.scales.get(attr, 99))
                

    def _meta(self):
        """Compute meta information about our data, such as min, max, mean..."""
        self._scales()
        self.meta = {}
        # Now, go through data and compute some statistics, dependent on data type
        for attr in self.scales.keys():
            values = [sample[attr] for sample in self.data if attr in sample and sample[attr] not in (np.NaN, None)]
            summary = ""
            notes = ""
            warnings = ""
            if self.scales[attr] is Data.ARRAY:
                array_lengths = set(len(data) for data in values)
                if len(array_lengths) is 1:
                    self.meta[attr] = {
                        'len': min(array_lengths),
                    }
                    summary = "ARRAY"
                    notes = "Length: {len}"
                else:
                    self.scales[attr] = Data.FLEX_ARRAY
                    self.meta[attr] = {
                        'minlen': min(array_lengths),
                        'maxlen': max(array_lengths)
                    }
                    summary = "ARRAY"
                    notes = "Lengths: {minlen} - {maxlen}"
            elif self.scales[attr] is Data.NOMINAL:
                self.meta[attr] = {
                    'values': list(set(values))
                }
                summary = "[{0}]".format(", ".join(set(values)))
                if len(summary) > 20:
                    summary = summary[:16]+"...]"
            elif self.scales[attr] is Data.ORDINAL:
                self.meta[attr] = {
                    'min': min(values),
                    'max': max(values)
                }
                if min(values) is max(values):
                    summary = "{min}"
                else:
                    summary = "{min} - {max}"
            elif self.scales[attr] is Data.CARDINAL:
                self.meta[attr] = {
                    'min': min(values),
                    'max': max(values),
                    'mean': np.asarray(values).mean(),
                    'std': np.asarray(values).std()
                }
                summary = "{min:.2f} - {max:.2f}"
                notes = "Mean: {mean:.2f} +- {std:.2f}"

            self.meta[attr]['missing'] = len(self) - len(values)

            # Construct a string representation of the meta info
            summary = summary.format(**self.meta[attr])
            notes = notes.format(**self.meta[attr])
            if self.meta[attr]['missing']:
                warnings = "(missing in {missing} samples)".format(**self.meta[attr])

            self.meta[attr]['summary'] = "{0:20} {1:22} {2}".format(summary, notes, warnings)


    @property
    def summary(self):
        """Returns a summary of the data set as a string."""
        self._meta()
        summary = "{0} ({1} samples)".format(self.label(), len(self))
        if len(self) == 0:
            return summary

        summary += "\n" + "'"*80
        max_attr_len = max(len(attr) for attr in self.scales) + 1
        for attr in self.scales:
            summary += "\n{0:{1}}: {2}".format(attr+"*"*(attr in self.dependent), max_attr_len, self.meta[attr]['summary']) 
        summary += "\n" + "="*80
        return summary

