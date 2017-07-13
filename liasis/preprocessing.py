#!/usr/bin/env python3

import os
import pandas as pa
import pronto
import urllib.request

from gzip import GzipFile
from lxml import etree

def preprocessing_files(object_to_analyze, name_path_file_interest, name_path_file_reference):
    '''
    Function creating a dataframe from two files, compatible with PandasBasedEnrichmentAnalysis.
    The input are the name of the column to analyse (common between the two files) and the
    two path and name of the file (with extension).
    Files must contain two columns, one with the object to analyse and the other with the
    occurrences of the object.
    '''

    file_name_interest, file_extension_interest = os.path.splitext(name_path_file_interest)
    if file_extension_interest == '.xls':
        counts_df = pa.read_excel(name_path_file_interest, sep=None, na_values="")
    else:
        counts_df = pa.read_csv(name_path_file_interest, sep=None,
                                        engine="python", na_values="")

    file_name_reference, file_extension_reference = os.path.splitext(name_path_file_reference)
    if file_extension_reference == '.xls':
        counts_df_reference = pa.read_excel(name_path_file_reference, sep=None, na_values="")
    else:
        counts_df_reference = pa.read_csv(name_path_file_reference, sep=None,
                                        engine="python", na_values="")

    counts_df.set_index(object_to_analyze, inplace=True)
    column_interest_name = counts_df.columns[0]

    counts_df_reference.set_index(object_to_analyze, inplace=True)
    column_reference_name = counts_df_reference.columns[0]

    df_joined = counts_df.join(counts_df_reference)

    return df_joined, column_interest_name, column_reference_name


def go_translation_dictionary_creation():
    '''
    Create a dictionary containing GO number as key
    and GO label as value in order to translate GO number.
    This function need an internet connexion because it is
    interrogating the Gene Ontology with Pronto module.
    Use it to create the dictionary needed in the
    GOEnrichmentAnalysis class.
    '''
    go_number_to_labels = {}

    go_ontology = pronto.Ontology('http://purl.obolibrary.org/obo/go/go-basic.obo')

    for go_term in go_ontology:
        go_number_to_labels[go_term.id] = go_term.name

    return go_number_to_labels

def ec_translation_dictionary_creation():
    '''
    Create a dictionary containing EC number as key
    and EC name as value in order to translate EC number.
    '''
    enzyme_number_to_names = {}

    url = 'ftp://ftp.expasy.org/databases/enzyme/enzyme.dat'
    enzyme_data = urllib.request.urlopen(url).read().decode('utf-8')

    for enzyme_description in enzyme_data.split('//\n'):
        for line in enzyme_description.split("\n"):
            if 'ID' in line and 'DR' not in line:
                enzyme_number = line.replace('ID   ', '').strip()
            if 'DE' in line and 'DR' not in line:
                enzyme_name = line.replace('DE ','').replace('.', '').strip()
                enzyme_number_to_names[enzyme_number] = enzyme_name

    return enzyme_number_to_names

def interpro_translation_dictionary_creation():
    '''
    Create a dictionary containing interpro ID as key
    and interpro name as value in order to translate interpro number.
    '''
    interpro_id_to_names = {}

    url = 'ftp://ftp.ebi.ac.uk/pub/databases/interpro/interpro.xml.gz'
    response = urllib.request.urlopen(url)

    with GzipFile(fileobj = response) as xmlFile:
        root = etree.parse(xmlFile).getroot()
        for child_IPR in root:
            interpro_id = child_IPR.attrib.get('id')
            for child_IPR_data in child_IPR:
                if child_IPR_data.tag == 'name':
                    interpro_name = child_IPR_data.text
            if interpro_id is not None:
                interpro_id_to_names[interpro_id] = interpro_name

    return interpro_id_to_names
