#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 11:37:23 2019

@author: sambrown
"""

import requests
import xmltodict
from operator import itemgetter
from collections import OrderedDict

def search(query, numResponses = 100, retreived = ("authors", "pub_date", "journal", "open_src", "pdf_links", "doi", "id", "title", "abstract"), constraints = {"authors" : "", "start_date" : "", "end_date" : "", "within_days" : 0, "affiliations" : "", "journals" : ""}, returnAsList = False):
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
    # Always returned outputs:s
    #       1. Request status
    #
    # Optional outputs
    #       2. List of requested outputs (includes boolean for "if opensource", as well as link to pdf if true)

    # First, set up some parameters that will be needed for the function
    searchTool = "esearch"
    summaryTool = "esummary"
    fetchTool = "efetch"
    postTool = "epost"
    pmcDB = "pmc"
    pubMedDB = "pubmed"
    maxNumIDs = 500
    maxIDsWithoutPost = 200 # The threshold for using the post method to upload an id list
    programToolName = "DSDC" # To inform the requst server of our name
    programEmail = "samuelgb@bu.edu" # To inform the request server how to contact us if there is a problem (please don't screw something up with my name on it)
    baseURL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/{tool}.fcgi?db={db}&rettype=xml" + f"&tool={programToolName}&email={programEmail}"
    

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
        requestURL = baseURL.format(db=pubMedDB, tool=searchTool) + f"&term={query}" + dateConstraintStr + f"&retmax={numResponses}"
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
    
    # By this point, we should have a list of id's (idList) of all of the items that we want information on
    
    # First, check if we're actually getting anything, before we go to all the trouble
    if len(retreived) == 0:
        # If there isn't any data that the user wants, then just return the idList
        return idList
    
    # If we actually need to communicate with the server, then form the request
    # First, create a string list of the ID's
    idStr = "&id=" + ",".join(map(str, idList))
    
    # Depending on how many ID's are provided, it's kind of nice to use the POST method to upload them
    if len(idList) > maxIDsWithoutPost:
        # Upload the ID's using post
        uploadRequestURL = baseURL.format(db=pubMedDB, tool=postTool) + idStr
        postResponse = requests.get(uploadRequestURL)
        
        # Get the query key and webenv from the response
        postResponseDict = xmltodict.parse(postResponse.text)
        queryKey = postResponseDict['ePostResult']['QueryKey']
        webEnv = postResponseDict['ePostResult']['WebEnv']
        
        # Finally, create an addition to the fetchRequst, below, so that it uses the UID list that we just uploaded
        fetchRequestIdStr = f"&query_key={queryKey}&WebEnv={webEnv}"
    else:
        # Simply append the id's to the fetch requst
        fetchRequestIdStr = idStr
    
    # Now, perform the fetch
    fetchRequestURL = baseURL.format(db=pubMedDB, tool=fetchTool) + fetchRequestIdStr
    fetchResponse = requests.get(fetchRequestURL)
    fetchResponseDict = xmltodict.parse(fetchResponse.text)
    
    # Create a list of all resulting articles
    allData = fetchResponseDict['PubmedArticleSet']['PubmedArticle']
    allCitationInfoLists = list(map(itemgetter('MedlineCitation'), allData))
    allArticleDataLists = list(map(itemgetter('Article'), allCitationInfoLists))    
    
    # Now that we have the results of the fetch (after a long time, probably), pull out all of the interesting information
    resultsDict = {"ids" : idList}
    
    # Get authors
    if 'authors' in retreived:
        allAuthors = []
        
        # If we need the authors, then extract all valid authors
        allAuthorListMetas = list(map(itemgetter('AuthorList'), allArticleDataLists))
        allAuthorLists = list(map(itemgetter('Author'), allAuthorListMetas))
        
#        allAuthors = [[authorList] if isinstance(authorList, OrderedDict) else authorList for authorList in allAuthorLists]
        
        for authorList in allAuthorLists:
            if isinstance(authorList, OrderedDict):
                 # If this author list is an OrderedDict, then it's actually just an author
#                 try:
#                     authorList['Affiliations'] = list(authorList['AffiliationInfo'].values())
#                     authorList.pop('AffiliationInfo')
#                 except:
#                     authorList['Affiliations'] = []
                 allAuthors.extend([authorList])
            else:
                 # If this is a list of OrderedLists, then go through each one and get the required data 
#                 for author in authorList:
#                     try:
#                         author['Affiliations'] = list(author['AffiliationInfo'].values())
#                         author.pop('AffiliationInfo')
#                     except:
#                         author['Affiliations'] = []
                 allAuthors.extend(authorList)
        
        resultsDict['authors'] = allAuthors
        
    # Get publication date
    if 'pub_date' in retreived:
        resultsDict['pub_date'] = list(map(itemgetter('ArticleDate'), allArticleDataLists))
        
    # Get Journal information
    if 'journal' in retreived:
        resultsDict['journal'] = list(map(itemgetter('Journal'), allArticleDataLists))
        
    # Get Title
    if 'title' in retreived:
        resultsDict['title'] = list(map(itemgetter('ArticleTitle'), allArticleDataLists))
        
    # Get DOI
    if 'doi' in retreived:
        allPubmedMetadata = list(map(itemgetter('PubmedData'), allData))
        allArticleIdLists = list(map(itemgetter('ArticleIdList'), allPubmedMetadata))
        resultsDict['doi'] = [[idDict['#text'] for idDict in articleIDList['ArticleId'] if idDict['@IdType'] == 'doi'] for articleIDList in allArticleIdLists]
                   
#    # Get Abstract
        # TODO: Deal with some articles not having abstracts!!!
#    if 'abstract' in retreived:
#        allAbstractLists = list(map(itemgetter('Abstract'), allArticleDataLists))
#        resultsDict['abstract'] = list(map(itemgetter('AbstractText'), allAbstractLists))
    
    # TODO: Get open-source information, and a pdf link if possible
    
    # A test for now, to see how well the function works
    return resultsDict, fetchResponseDict, fetchRequestURL
    