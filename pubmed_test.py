#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 10:14:39 2019

@author: sambrown
"""

from pubmed_search import search
from article_analysis import analyze

# Test the tool
resultsDict, fetchResponseDict, fetchRequestURL = search([11158633,31760027,28298962], numResponses = 1)

# Test the abstract analyzer
testStr = "This report discusses the public health impact of Alzheimer’s disease (AD), including incidence and prevalence, mortality rates, costs of care and the overall effect on caregivers and society. It also examines the challenges encountered by health care providers when disclosing an AD diagnosis to patients and caregivers. An estimated 5.3 million Americans have AD; 5.1 million are age 65 years, and approximately 200,000 are age <65 years and have younger onset AD. By mid-century, the number of people living with AD in the United States is projected to grow by nearly 10 million, fueled in large part by the aging baby boom generation. Today, someone in the country develops AD every 67 seconds. By 2050, one new case of AD is expected to develop every 33 seconds, resulting in nearly 1 million new cases per year, and the estimated prevalence is expected to range from 11 million to 16 million. In 2013, official death certificates recorded 84,767 deaths from AD, making AD the sixth leading cause of death in the United States and the fifth leading cause of death in Americans age 65 years. Between 2000 and 2013, deaths resulting from heart disease, stroke and prostate cancer decreased 14%, 23% and 11%, respectively, whereas deaths from AD increased 71%. The actual number of deaths to which AD contributes (or deaths with AD) is likely much larger than the number of deaths from AD recorded on death certificates. In 2015, an estimated 700,000 Americans age 65 years will die with AD, and many of them will die from complications caused by AD. In 2014, more than 15 million family members and other unpaid caregivers provided an estimated 17.9 billion hours of care to people with AD and other dementias, a contribution valued at more than $217 billion. Average per-person Medicare payments for services to beneficiaries age 65 years with AD and other dementias are more than two and a half times as great as payments for all beneficiaries without these conditions, and Medicaid payments are 19 times as great. Total payments in 2015 for health care, long-term care and hospice services for people age 65 years with dementia are expected to be $226 billion. Among people with a diagnosis of AD or another dementia, fewer than half report having been told of the diagnosis by their health care provider. Though the benefits of a prompt, clear and accurate disclosure of an AD diagnosis are recognized by the medical profession, improvements to the disclosure process are needed. These improvements may require stronger support systems for health care providers and their patients."
nlpDateEntities, nlpDocsList = analyze(testStr)

# Print out the results of the nlp analysis
print("All named entities:")
for ent in nlpDocsList.ents:
    print('{:35s} {:10s}'.format(ent.text, ent.label_))

print()
print()

print("All date entities:")
for ent in nlpDateEntities:
    print('{:35s} {:10s}'.format(ent.text, ent.label_))