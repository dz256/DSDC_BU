#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 11:37:23 2019

@author: sambrown
"""

import requests
import xmltodict

def search(query, numResponses = 100, retrievedDataTypes = ("authors", "pub_date", "affiliations", "journal", "open_src", "pdf_links"), constraints = {"authors" : "", "start_date" : "", "end_date" : "", "within_days" : 0, "affiliations" : "", "journals" : ""}, returnAsList = False):
    # PubMed search function
    # Exclusive inputs:
    #       1. Query (str): A search query
    #       2. Query (int): A single ID to retreive information for
    #       3. Query (list(int)): A list of ID's (up to 500) to retreive information for
    # Other inputs, valid with all:
    #       1. Type of data (authors, publication date, affiliation, journal, ...)
    #       2. Behavior with outputs (return as lists, or push to database)
    # Other inputs, valid with one:
    #       1. Number of responses (default = 100)
    #           Valid only with a search query (str)
    #       1. Constraints (authors, publication date, affiliation, journal, ...)
    #           Valid only with a search query (str)
    # Always returned outputs:
    #       1. Request status
    #
    # Optional outputs
    #       2. List of requested outputs (includes boolean for "if opensource", as well as link to pdf if true)

    # First, set up some parameters that will be needed for the function
    searchTool = "esearch"
    summaryTool = "esummary"
    fetchTool = "efetch"
    pmcDB = "pmc"
    pubMedDB = "pub_med"
    maxNumIDs = 500
    programToolName = "DSDC" # To inform the requst server of our name
    programEmail = "samuelgb@bu.edu" # To inform the request server how to contact us if there is a problem (please don't screw something up with my name on it)
    baseURL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/{tool}.fcgi?db={db}" + f"&tool={programToolName}&email={programEmail}"
    

    # Next, parse the inputs
    requestURL = ""
    if isinstance(query, str):
        # If our query is a string, then it is a search query.  Start building the request
        
        # Error check the input
        if numResponses > 100000:
            raise Exception("Cannot currently request more than 100,000 responses at a time.  It CAN be done, just...bug Sam or Dana about it")

        dateConstraintStr = ""
        if constraints["within_days"] != 0:
            # If the within_days parameter is set...
            if (constraints["start_date"] != "" or constraints["end_date"] != ""):
                raise Exception("Can only have one date restriction: either within_days or a start and/or end date")

            # Generation a constraint string based on this input
            dateConstraintStr = f"&reldate={constraints['within_days']}"
        elif constraints["start_date"] != "" and constraints["end_date"] != "":
            # If the start/end date parameter is being used (they must be used together)
            dateConstraintStr = f"&mindate={constraints['start_date']}&maxdate={constraints['end_date']}"
        
        # Send the query, along with the constraint information
        requestURL = baseURL.format(db=pmcDB, tool=searchTool) + f"&term={query}" + dateConstraintStr + f"&retmax={numResponses}"
        response = requests.get(requestURL)
        
        # TODO: Error check the types of responses (expecting a 200)
        
        # Get the IDs from the response, as a list
        fullResponseDict = xmltodict.parse(response.text)
        idList = fullResponseDict['eSearchResult']['IdList']['Id']
    elif isinstance(query, int):
        # If we are only requesting a single id, then turn it into a list of size 1
        idList = [query]
    elif isinstance(query, list):
        # If we received a list, then just assign it directly to the idList variable
        
        # TODO: Perform some error-checking to ensure that each value in the list is an int
        
        if len(query) > maxNumIDs:
            raise Exception("Can only request up to " + str(maxNumIDs) + " IDs at once")
            
        idList = query;
    else:
        raise Exception("Query must be a str (for a search term), an int (for a single document ID), or a list of ints (for a number of document IDs)")
    
    # A test for now, to see how well the function works
    return idList, requestURL