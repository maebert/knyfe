#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This example uses the FreeBase API to get a list of wines and find out how much alcohol is in 
a typical wine.
"""
import requests
import json
import knyfe

freebase_url = "https://www.googleapis.com/freebase/v1/mqlread?query=%s"
params = [{
    "country": None,
    "name": None,
    "percentage_alcohol": None,
    "percentage_alcohol>": 0, # Make sure this attribute is present
    "type": "/food/wine"
}]

params_json = json.dumps(params)
r = requests.get(url % params_json)
content = json.loads(r.content)

wines = knyfe.Data(content['result'])

# Which countries are present in our data set?
print set(wines.country)

# What's the median alcohol content?
import numpy
print numpy.median(wines.percentage_alcohol)

