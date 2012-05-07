#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy  as np
import sys
import os
import cPickle
try:
    import simplejson as json
except ImportError:
    import json
import logging
import random
import copy
import tablib

class Data:
    """A generic data manager for exploring generic datasets.

    A dataset is simply a list of data samples, and samples are nothing but
    key-value pairs, or dictionaries. This class is a wrapper that allows you
    to rapidly interact with these kind of data sets.

    Storing your datasets as lists of key-value pairs has the advantage that we
    can save them as JSON, or put them into a MongoDB. Let's assume we've got a
    JSON object in the file mydata.json that looks roughly like this:

      [
        {
          name: "Jeanne D'Arc",
          gender: "female",
          continent: "Europe",
          age: '19'
        },
        {

        }
      ]

    - we can construct a Data object like this:

      data = Data("mydata.json")

    Now let's play around a bit:

      data = data.filter(gender='male', continent=('Europe', 'Asia')).get('age')

    Will return a numpy array containing the ages of all dudes living in Europe
    or Asia. Notice the method chaining; filter (and other methods like it) will
    always return a new Data object. Want some statistics:

      data.filter(lambda d: squeeze(d) == "quiek").mean('size', 'weight')

    gives you the mean size and weight of all samples that make "quiek" when
    squeezed (ie. all key-value-pairs that return "quiek" when passed to the
    squeeze function). If we're often interested in the same variables, we can set

        data.set_dependent('size', 'weight')

    and now just call data.mean() to get the mean size and weight.

    But hey, let's get serious and run a proper test:

        data.set_dependent('awesomeness')
        ninjas = data.filter(job='ninja').remove_outliers()
        pirates = data.filter(job='pirate').remove_outliers()
        ninja.permutation_test(pirates)

    Will first construct datasets with only ninjas and pirates, respectively,
    remove the super awesome and super lame from each group, and then run a
    permutation test to see whether the dependent variable (awesomeness) is
    significantly different in these two groups. The great thing about 
    permutation tests is that you need to know almost nothing about your 
    distribution. It's the most take-no-prisoners kind of statistical test there
    is. And it will give you a p value. Less is more. e.g. a p-value of 0.04 will
    tell you that there's a 96%% chance that these groups really differ in
    awesomeness and it's not just random fluctuation that makes for different mean
    values.

    """
    logging.basicConfig(format="%(levelname)-7s %(asctime)s:  %(message)s", level=logging.INFO)
    log = logging.getLogger("Data Analysis")
    
    # Define some scales
    NOMINAL = 0     # For Strings and Booleans
    ORDINAL = 1     # For Integers
    CARDINAL = 2    # For Floats 
    ARRAY = 3       # For tuples, lists, np.arrays of fixed length across dataset
    FLEX_ARRAY = 4  # For tuples, lists, np.arrays of flexible length across dataset

    def __init__(self, data=[], label="Unnamed Dataset", use_json=True, dependent=[]):
        if type(data) is str:
            self.load(data)
        elif type(data) in (list, tuple):
            self.data = data
        else:
            self.data = []
        self.str_label = label
        self.use_json = use_json
        self.pickle = json if use_json else cPickle
        self.dependent = self._np1d(dependent)


    def _new(self, data=[]):
        """Creates an empty dataset, copying over dependent varuables and label from the current dataset"""
        return self.__class__(data, dependent=self.dependent, use_json = self.use_json, label=self.label()+"*")


    def set_dependent(self, *variables):
        self.dependent = self._np1d(variables)
        return self

    def label(self, label=None):
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

    def _one_sample_perm(self, data, ranked):
        pass

    def map(self, attribute, new_attribute, function):
        """Creates a new attribute in each sample by mapping an existing one using the given function. 
        knyfe.map('age', 'life_expectancy', lambda age: 82 - age)
        Will create an attribute 'life_expectancy' in each sample of the dataset."""
        for sample in self.data:
            sample[new_attribute] = function(sample[old_attribute])

    def extend(self, other_data):
        """Appends a different Data object or list of data samples to self.data"""
        if type(other_data) is list:
            self.data.extend(other_data)
        elif hasattr(other_data, 'data'):
            self.data.extend(other_data.data)

    def load(self, *filenames):
        """Opens specified files using the standard protocol (json by default)
        and loads their data into self.data"""
        for filename in filenames:
            data_file = open(filename)
            subject_data = self.pickle.load(data_file)
            data_file.close()
            self.data.extend(subject_data)

    def save(self, filename):
        """Saves the current dataset as JSON to the given filename."""
        with open(filename) as f:
            json.dump(self.data, f, indent=2)

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
        self._scales() # Get all attributes present
        all_keys = self.scales.keys()
        new_data = [dict.fromkeys(all_keys, None) for i in xrange(len(self))]
        for i, d in enumerate(self.data):
            new_data[i].update(d)    
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
        return "%s (%d samples)" % (self.label(), len(self))

    def get(self, attribute):
        """Gets all values of an attribute across all samples."""
        return np.asarray([date[attribute] for date in self.data if attribute in date])


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
        

    def get_set(self, attribute):
        """Returns a set of all values present in the dataset for a given attribute"""
        subjects = set(d['subject'] for d in self.data)
        return sorted(subjects)


    def median_split(self, attribute):
        """Returns two datasets, split at the median of the given attribute"""
        data_median = np.median(self.get(attribute))
        set0 = self.filter(lambda d: d[attribute] < data_median)
        set0 = self.filter(lambda d: d[attribute] >= data_median)
        return set0, set1


    def toggle_verbose(self, verbose=False):
        """If True, log all info, else log only warnings and errors."""
        self.log.setLevel(logging.DEBUG if verbose else logging.WARNING)


    def filter(self, _func=None, **kwargs):
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

        Alternatively, a function may be given to implement more complex filters:

            data.filter(lambda d: d['subject'] > 3)

        Will return all data where the subject key is greater than 3."""
        def _all(boollist):
            return reduce(lambda b1, b2: b1 and b2, boollist)
        def _condition(c, v):
            if type(v) in (list, tuple, np.ndarray):
                return lambda data: c in data and data[c] in v
            else:
                return lambda data: c in data and data[c] == v

        if _func and callable(_func):
            return self._new([trial for trial in self.data if _func(trial)]).filter(**kwargs)
        elif _func and type(_func) is str:
            return self.filter(lambda trial: trial.has_key(_func) and trial[_func], **kwargs)
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
            elif type(value) in (str, bool):
                return Data.NOMINAL
            elif type(value) in (tuple, list, np.ndarray):
                return Data.ARRAY

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
        if not hasattr(self, 'scales'):
            self._scales()
        self.meta = {}
        # Now, go through data and compute some statistics, dependent on data type
        for attr in self.scales.keys():
            values = [sample[attr] for sample in self.data]
            if self.scales[attr] is Data.ARRAY:
                array_lengths = set(len(data) for data in values)
                if len(array_lengths) is 1:
                    pass # TODO: deal with  arrays
                else:
                    self.scales[attr] = Data.FLEX_ARRAY
                    self.meta[attr] = {
                        'min': min(array_lengths),
                        'max': max(array_lengths)
                    }
            elif self.scales[attr] is Data.NOMINAL:
                self.meta[attr] = {
                    'values': list(set(values))
                }
            elif self.scales[attr] is Data.ORDINAL:
                self.meta[attr] = {
                    'min': min(values),
                    'max': max(values)
                }
            elif self.scales[attr] is Data.CARDINAL:
                self.meta[attr] = {
                    'min': min(values),
                    'max': max(values),
                    'mean': np.asarray(values).mean(),
                    'std': np.asarray(values).std()
                }


    def print_summary(self):
        """Prints a summary of the data set."""
        self._meta()
        print "%s (%d samples)" %(self.label(), len(self))
        print "-"*60
        for attr in self.scales:
            attrname = "* "+attr if attr in self.dependent else "  "+attr
            if self.scales[attr] is Data.NOMINAL:
                values = self.meta[attr]['values']
                if len(values) > 6:
                    values = values[:6]
                    values.append("...")
                desc = "[%s]" % ", ".join(values)
            elif self.scales[attr] is Data.ORDINAL:
                desc = "%(min)d - %(max)d" % (self.meta[attr])
            elif self.scales[attr] is Data.CARDINAL:
                desc = "%(mean).2f +- %(std).2f [%(min)0.2f - %(max)0.2f]" % (self.meta[attr])
            elif self.scales[attr] is Data.FLEX_ARRAY:
                desc = "ARRAY [%(min)d - %(max)d elements]" % (self.meta[attr])
            elif self.scales[attr] is Data.ARRAY:
                desc = "ARRAY"
            print "%-20s: %s" %(attrname, desc)
        print "="*60


if __name__ == "__main__":
    A = [51.2,46.5,24.1,10.2,65.3,92.1,30.3,49.2]#,16.4,14.1,13.4,15.4,14.0,11.3]
    B = [45.8,41.3,15.8,11.1,58.5,70.3,31.6,35.4]#,12.6,11.4,13.2,11.2,09.4,12.0]
    raw_data = [{'group': 'A', 'x': a} for a in A] + [{'group': 'B', 'x': b} for b in B]
    data = Data(data=raw_data, dependent='x').label("All data")
    data_a = data.filter(group='A').label("A")
    data_b = data.filter(group='B').label("B")

    from scipy.misc import comb as bincoef
    tp = bincoef(len(data_a)*2, len(data_a))
    #data_a.permutation_test(data_b, ranked=True, two_samples=False)
    print data_a.permutation_test(data_b, ranked=False, two_samples=True, limit=30)
#    print data_a.permutation_test(data_b, ranked=False, two_samples=True, limit=2000)

#    r2 = data_a.permutation_test(data_b, ranked=False, two_samples=True, limit=800)
    # r = []
    # for x in xrange(1, tp, 100):
    #     r2 = data_a.permutation_test(data_b, ranked=False, two_samples=True, limit=x)
    #     r.append(r1[0] - r2[0])
    # print r
    

    #print r2

# one-sample
# [ 0.98828125  0.01953125  0.0390625 ]
# two-sample
# [ 0.71313131  0.32268842  0.64537685]


    # from random import gauss
    # raw_data = []
    # for sample in range(100):
    #     d = {'subject': sample}
    #     if sample % 2:
    #         d['species'] = 'dog'
    #         d['mischief'] = gauss(20, 5)
    #         d['stinkyness'] = gauss(60, 14)
    #         d['teeth'] = (12, 4, 16, 10) # (incisors, premolars, canines, molars)
    #     else:
    #         d['species'] = 'cat'
    #         d['mischief'] = gauss(40, 6)
    #         d['stinkyness'] = gauss(50, 8)
    #         d['teeth'] = (12, 4, 10, 4)
    #     raw_data.append(d)

    # all_data = Data(data=raw_data, dependent='stinkyness', label="Animals")
    # cats = all_data.filter(species='cat').label('Cats')
    # dogs = all_data.filter(species='dog').label('Dogs')
    # dogs.print_summary()
    # cats.print_summary()
    # dogs.permutation_test(cats)