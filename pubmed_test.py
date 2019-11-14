#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 10:14:39 2019

@author: sambrown
"""

from pubmed_search import search

# Test the tool
idList, requestURL = search("alzheimers")
print(idList)