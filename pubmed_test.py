#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 10:14:39 2019

@author: sambrown
"""

from pubmed_search import search

# Test the tool
resultsDict, fetchResponseDict, fetchRequestURL = search([11158633,31760027,28298962], numResponses = 1)