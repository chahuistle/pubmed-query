#!/usr/bin/env python3

# Queries PubMed to obtain number of multiomics studies between 2000 and 2018 
# A multiomics study is defined as a study that has two or more from the following keywords ("Other Term" PubMed field): 
# genomics, lipidomics, proteomics, glycomics, transcriptomics, metabolomics, epigenomics, microbiomics

import xml.etree.ElementTree as ET
import itertools, requests, time
from datetime import date, timedelta

# useful constants
DATE_FROM = date(2000, 1, 1)
DATE_UNTIL = date(2018, 12, 31)
ALL_KEYWORDS = ["genomics", "lipidomics", "proteomics", "glycomics", "transcriptomics", "metabolomics", "epigenomics", "metagenomics", "phosphoproteomics"]
DATE_FORMAT = "%Y/%m/%d"
QUERY_WINDOW_SIZE = 1050.0
MAX_QUERIES_PER_WINDOW = 3

# global variables
time_last_query = -1
n_window_queries = 0

# returns a pubmed url
def build_query_url(keywords, date_from, date_until):
    query_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?retmax=100000&tool=qbic&email=luis.delagarza@qbic.uni-tuebingen.de&term=%s[Date+-+Publication]:%s[Date+-+Publication]" % (date_from.strftime(DATE_FORMAT), date_until.strftime(DATE_FORMAT))
    for keyword in keywords:
        query_url += "+AND+%s[Other+Term]" % (keyword)
    return query_url

# returns the ids
def query_pubmed(url):
    # In order not to overload the E-utility servers, NCBI recommends that users post no more 
    # than three URL requests per second and limit large jobs to either weekends or between 9:00 PM and 5:00 AM Eastern time during weekdays. 
    global time_last_query
    global n_window_queries
    current_time = current_milli_time()
    # new window started, query away!
    if (current_time - time_last_query) > QUERY_WINDOW_SIZE:
        n_window_queries = 0
    if n_window_queries >= MAX_QUERIES_PER_WINDOW:
        # wait one whole window to be on the safe side (also, just be lazy, I guess)
        print("Doing it like Verizon...")
        time.sleep(QUERY_WINDOW_SIZE / 1000.0)
        n_window_queries = 0
    raw_response = requests.get(url).text
    #print("Querying using %s" % url)
    #raw_response = "<?xml version=\"1.0\" encoding=\"UTF-8\" ?><!DOCTYPE eSearchResult PUBLIC \"-//NLM//DTD esearch 20060628//EN\" \"https://eutils.ncbi.nlm.nih.gov/eutils/dtd/20060628/esearch.dtd\"><eSearchResult><Count>15</Count><RetMax>15</RetMax><RetStart>0</RetStart><IdList><Id>12465651</Id><Id>12159840</Id><Id>11701847</Id><Id>11262879</Id><Id>11187813</Id><Id>10755918</Id><Id>11130686</Id><Id>23105267</Id><Id>10778367</Id><Id>10766612</Id><Id>10746694</Id><Id>10746688</Id><Id>10659812</Id><Id>10646564</Id><Id>10639503</Id></IdList><TranslationSet/><TranslationStack>   <TermSet>    <Term>2000/01/01[PDAT]</Term>    <Field>PDAT</Field>    <Count>0</Count>    <Explode>N</Explode>   </TermSet>   <TermSet>    <Term>2000/12/31[PDAT]</Term>    <Field>PDAT</Field>    <Count>0</Count>    <Explode>N</Explode>   </TermSet>   <OP>RANGE</OP>   <TermSet>    <Term>genomics[Other Term]</Term>    <Field>Other Term</Field>    <Count>7402</Count>    <Explode>N</Explode>   </TermSet>   <OP>AND</OP>  </TranslationStack><QueryTranslation>2000/01/01[PDAT] : 2000/12/31[PDAT] AND genomics[Other Term]</QueryTranslation></eSearchResult>"
    time_last_query = current_milli_time()
    n_window_queries += 1
    xml_response = ET.fromstring(raw_response)
    # do some sanity check
    if int(xml_response.findall(".//Count")[0].text) > int(xml_response.findall(".//RetMax")[0].text):
        print("Query returned more results than expected!!! %s" % url)
    return [study_id.text.strip() for study_id in xml_response.findall(".//IdList/Id")]

def current_milli_time(): 
    return int(round(time.time() * 1000))

# generate combinations of 2, 3, ... N elements from all_keywords
def get_keyword_combinations(all_keywords):
    keywords = []
    for i in range(2, len(all_keywords) + 1):
        keywords.extend(itertools.combinations(all_keywords, i))
    return keywords

def do_all_queries():
    keyword_combinations = get_keyword_combinations(ALL_KEYWORDS)
    # go through the years, query
    current_date_from = DATE_FROM
    while current_date_from < DATE_UNTIL:
        # date until the end of the year 
        current_date_until = date(current_date_from.year + 1, 1, 1) - timedelta(days=1)
        print("Finding multiomics studies between %s and %s" % (current_date_from.strftime(DATE_FORMAT), current_date_until.strftime(DATE_FORMAT)))
        # keep track of all studies published in this same year
        multiomics_studies = set()
        for current_keyword_combination in keyword_combinations:
            ids = query_pubmed(build_query_url(current_keyword_combination, current_date_from, current_date_until))
            print ("  Keywords=[%s]; From=")
            multiomics_studies.update(ids)

        print("From %s to %s there were %d multiomics studies" % (current_date_from.strftime(DATE_FORMAT), current_date_until.strftime(DATE_FORMAT), len(multiomics_studies)))

        # increment date to next year
        current_date_from = date(current_date_from.year + 1, 1, 1)

do_all_queries()
