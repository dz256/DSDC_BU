#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 13:46:10 2019

@author: sambrown
"""

import spacy

def analyze(analysisDict, extracted = 'all'):
    # TODO: Perhaps put the abstract analysis aspect into a subfunction, which is only called if an abstract is supplied AND information is requested that requires an abstract
    # Abstract analysis function
    # Inputs:
    #   analysisDict (dict): The article to be analyzed, as the dictionary returned by the pubmed_search function
    #   extracted (str/list(str)): Data type to be extracted from the abstract.  Options are: ['all', 'ages', TODO ADD MORE]
    # Outputs:
    #   data (dict): Extracted data, organized into a dict for each abstract that was entered into the function
    
    # First, set up some parameters that will be needed for the function
    dataTypes = ["ages"]
    test = False
    
    # TODO: Parse all inputs: Convert analysisDict so that it is a list(str).  For now, assume that it's a str or list(str)
    if ~isinstance(analysisDict, dict):
        if isinstance(analysisDict, str):
            # This is just a special test case, so go into test mode
            test = True
            abstractStr = analysisDict
        else:
            raise TypeError("Query must be a dict, as returned by the search function")
    else:
        # Get the keys to the dictionary (the pubmed id's)
        idList = analysisDict.keys();
    
#    if isinstance(analysisDict, str):
#        abstractList = [analysisDict]; # Convert the string to a 1 element list of strings
#    else:
#        abstractList = analysisDict;
    
    if extracted == 'all':
        extracted = dataTypes
    elif isinstance(extracted, str):
        if extracted not in dataTypes:
            raise ValueError(extracted + " is not a supported data type.  Options are: %s" % dataTypes)
        extracted = [extracted]
    elif isinstance(extracted, list):
        extracted = list(set(extracted) & set(dataTypes))
        if len(extracted) == 0:
            raise ValueError("Extracted does not contain any supported data types.  Options are: %s" % dataTypes)
    
    # Since we are analyzing the abstract, prepare the NLP functionality
    nlp = spacy.load("en_core_web_sm");
    nlpDocsList = []
    nlpDateEntities = {} # Primarily for testing
    
    # Perform an nlp analysis on all of the abstracts
    if test:
        # Just do the analysis on the single incoming string entry
        nlpDocsList = nlp(abstractStr);
        if len(nlpDocsList) > 0:
            # If there are some named entities in this entry
            thisEntList = []
            for ent in nlpDocsList.ents:
                # Add each entity that is a date
                if ent.label_ == "DATE":
                    thisEntList.append(ent)
            nlpDateEntities = thisEntList
        else:
            nlpDateEntities = []
    else:
        for id in idList:
            # Go through each entry in the incoming data, and perform the required analysis
            thisAbstract = analysisDict[id]['abstract']
            
            thisDoc = nlp(thisAbstract);
            nlpDocsList.append(thisDoc)
            if len(thisDoc) > 0:
                # If there are some named entities in this entry
                thisEntList = []
                for ent in thisDoc.ents:
                    # Add each entity that is a date
                    if ent.label_ == "DATE":
                        thisEntList.append(ent)
                nlpDateEntities.append(thisEntList)
            else:
                nlpDateEntities.append([])
    
    # Return the results of the analysis (nlpDocsList is only returned for testing purposes)
    return nlpDateEntities, nlpDocsList