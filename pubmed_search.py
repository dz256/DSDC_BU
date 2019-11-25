#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 11:37:23 2019

@author: sambrown
@edited by dz256 
"""
from configure import * #crediential of app - if you don't have that file tool won't work 
from warnings import warn
import datetime
import numpy as np

import requests
import xmltodict
from operator import itemgetter
from collections import OrderedDict

def search(query, numResponses = 100, retreived = 'all', constraints = None, pushToDB = False):
    # PubMed search function
    # Inputs:
    #       Query (str/int/list(int)): A search query, artical ID, or list of artical IDs
    #       numResponses (int): maximum number of responses returned - OPTIONAL
    #                           ONLY VALID IF SEARCH QUERY PROVIDED
    #       retreived (str/list(str)): data type to be returned. Options are: 
    #                 ['all','authors', 'pub_date', 'journal', 'open_src',  
    #                   'pdf_links','doi', 'id', 'title', 'abstract']
    #       constraints (dict): constraints for search query. Valid fields:
    #                 ['authors', 'start_date', 'end_date', 'within_days', 
    #                   'affiliations', 'journals']. 
    #       pushToDB (bool): for dev purposes only - push results to *OUR* db
    # Outputs:
    #       Request status (int): status request (200 == successful)
    #       Data (dict): a dictionary with the data requested, or error details 
    #                    if request was unsuccessful
   
    # First, set up some parameters that will be needed for the function
    infoTypes = ["authors", "pub_date", "journal", "open_src", "pdf_links", "doi", "title", "abstract"]
    
#    locals().update(credentials) # credentials == dict loaded from configure.py 
    baseURL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/{tool}.fcgi?db={db}&rettype=xml" + f"&tool={credentials['programToolName']}&email={credentials['programEmail']}"
    
    # error handling on request info type:
    if retreived == 'all':
        # retrieve all data
        retreived = infoTypes
    elif isinstance(retreived,str):
        if retreived not in infoTypes:
            raise ValueError(retreived +" is not a supported info type. Options are: %s" % infoTypes)
        retreived = [retreived]
    elif isinstance(retreived,list):
        retreived = list(set(retreived) & set(infoTypes))
        if len(retreived) == 0:
            raise ValueError("request dose not contain any supported info type. Options are: %s" % infoTypes)
               
    # Next, parse the inputs
    requestURL = ""
    if isinstance(query, str):
        # If our query is a string, then it is a search query.  Start building the request
        
        # User input validation
        if numResponses > 100000:
            warn("""We decided to set a limit of max 100,000 responses at a time. \n  
                 if you REALLY want more than the first 100,000 bug Sam or Dana about it. """)
            numResponses = 100000
        if isinstance(constraints,dict):
            # parse constraints string and add to URL
            dateConstraintStr = createConstraintStr(constraints)
        else:
            dateConstraintStr = ""
                
        # Send the query, along with the constraint information
        requestURL = baseURL.format(db=credentials['pubMedDB'], tool=credentials['searchTool']) + f"&term={query}" + dateConstraintStr + f"&retmax={numResponses}"
        response = requests.get(requestURL)
        
        # TODO: Error check the types of responses (expecting a 200)
        
        # Get the IDs from the response, as a list
        fullResponseDict = xmltodict.parse(response.text)
        idList = fullResponseDict['eSearchResult']['IdList']['Id']
    elif isinstance(query, int):
        # If we are only requesting a single id, then turn it into a list of size 1
        idList = [query]
    elif isinstance(query, list):
        if not isinstance(query[0],int):
            raise TypeError("""Query can be a search str, id (int), or list of 
                            ids (list of integers). The list provided contains
                            %s """ % type(query[0]))
        idList = query
        if len(idList) > maxNumIDs:
            warn("Can only request up to " + str(maxNumIDs) + " IDs at once")
            idList = idList[0:maxNumIDs]
    else:
        raise TypeError("Query must be a str (for a search term), an int (for a single document ID), or a list of ints (for a number of document IDs)")
    
    # By this point, we should have a list of id's (idList) of all of the items that we want information on
       
    # form the request:
    # First, create a string list of the ID's
    idStr = "&id=" + ",".join(map(str, idList))
    
    # Depending on how many ID's are provided, it's kind of nice to use the POST method to upload them
    maxIDsWithoutPost = credentials['maxIDsWithoutPost']
    if len(idList) > maxIDsWithoutPost:
        # Upload the ID's using post
        uploadRequestURL = baseURL.format(db=credentials['pubMedDB'], tool=credentials['postTool']) + idStr
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
    fetchRequestURL = baseURL.format(db=credentials['pubMedDB'], tool=credentials['fetchTool']) + fetchRequestIdStr
    fetchResponse = requests.get(fetchRequestURL)
    fetchResponseDict = xmltodict.parse(fetchResponse.text)
    
    # Create a list of all resulting articles
    allData = fetchResponseDict['PubmedArticleSet']['PubmedArticle']
    allCitationInfoLists = list(map(itemgetter('MedlineCitation'), allData))
    allArticleDataLists = list(map(itemgetter('Article'), allCitationInfoLists))    
    
    # Now that we have the results of the fetch (after a long time, probably), pull out all of the interesting information
    resultsDict = { i : {} for i in idList }
    
    infoMaps = {'authors':"allArticleDataLists[ind]['AuthorList']['Author']",
                'pub_date':"allArticleDataLists[ind]['ArticleDate']",
                'journal': "allArticleDataLists[ind]['Journal']",
                'title':"allArticleDataLists[ind]['ArticleTitle']",
                'doi':"[val['#text'] for val in allData[ind]['PubmedData']['ArticleIdList']['ArticleId'] if val['@IdType'] == 'doi']",        
                "open_src":"3", 
                "pdf_links":"3",
                "abstract":"3"
                }
    

        # If we need the authors, then extract all valid authors
    for ind,ids in enumerate(idList):
        for rType in retreived:
            resultsDict[ids][rType] = eval(infoMaps[rType])
 
               
#        for authorList in allAuthorLists:
#            if isinstance(authorList, OrderedDict):
#                 # If this author list is an OrderedDict, then it's actually just an author
##                 try:
##                     authorList['Affiliations'] = list(authorList['AffiliationInfo'].values())
##                     authorList.pop('AffiliationInfo')
##                 except:
##                     authorList['Affiliations'] = []
#                 allAuthors.extend([authorList])
#            else:
#                 # If this is a list of OrderedLists, then go through each one and get the required data 
##                 for author in authorList:
##                     try:
##                         author['Affiliations'] = list(author['AffiliationInfo'].values())
##                         author.pop('AffiliationInfo')
##                     except:
##                         author['Affiliations'] = []
#                 allAuthors.extend(authorList)
#        
#        resultsDict['authors'] = allAuthors
        
    # Get publication date
                   
#    # Get Abstract
        # TODO: Deal with some articles not having abstracts!!!
#    if 'abstract' in retreived:
#        allAbstractLists = list(map(itemgetter('Abstract'), allArticleDataLists))
#        resultsDict['abstract'] = list(map(itemgetter('AbstractText'), allAbstractLists))
    
    # TODO: Get open-source information, and a pdf link if possible
    
    # A test for now, to see how well the function works
    return resultsDict, fetchResponseDict, fetchRequestURL


def createConstraintStr(constraints):
    
    assert isinstance(constraints,dict), "constraints must be a dict. constraint type: %r" % type(constraints)

    conTypes = ['authors','start_date','end_date','within_days','affiliations',
                'journals']
    cons = list(constraints.keys())
    
    if len(set(cons) & set(conTypes)) == 0:
        warn("cons dose not contain any supported constraint types. Options are: %s" % conTypes)
        return ""
        
    invalidCons = np.setdiff1d(cons,conTypes).tolist()
    if len(invalidCons)>0:
        warn(""" %s are not valid constraint fields and were ignored. 
             valid constraints are: %s""" % (invalidCons,conTypes))
    
    cons = list(set(cons) & set(conTypes))
    if "within_days" in cons:
        if "start_date" in cons or "end_date" in cons:
            warn("""Can only have one date restriction: either within_days 
                     or a start and/or end date. ONLY the 'within_days' 
                     constraint was used for this search """)
    
        # Generation a constraint string based on this input
        dateConstraintStr = f"&reldate={constraints['within_days']}"
    # TODO: make sure dates are in acceptable format: [YYYY/MM/DD, YYYY/MM, YYYY]
    elif "start_date" in cons:
        if "end_date" in cons:
            dateConstraintStr = f"&mindate={constraints['start_date']}&maxdate={constraints['end_date']}"
        else: 
            d = datetime.datetime.today()
            constraints["end_date"] = d.strftime("%Y/%m/%d")
            dateConstraintStr = f"&mindate={constraints['start_date']}&maxdate={constraints['end_date']}"
    elif "end_date" in cons:
        constraints["start_date"] = "1900"
        dateConstraintStr = f"&mindate={constraints['start_date']}&maxdate={constraints['end_date']}"
    
    # TODO: hundle all other constraint types
    return dateConstraintStr
    