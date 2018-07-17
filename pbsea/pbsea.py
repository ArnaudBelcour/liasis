#!/usr/bin/env python3

import logging
import csv
import math
import numpy as np
import os
import pandas as pa
import scipy.stats as stats
import six

from statsmodels.sandbox.stats.multicomp import multipletests

logging.basicConfig(filename='analysis.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)


class PandasBasedEnrichmentAnalysis():

    '''
        Performs an enrichment analysis using an hypergeometric test
        (also known as Fisher's exact test) and multiple correction testing.
        To do this you need to enter some values (using the set_something() function):
            -file of interest : the name of your file (with the extension)
             containing the occurrences of each objects from a sample you want to analyze.
            -file of reference : the name of your file (with the extentions)
             containing the occurrences of each objects from a population.
            -number of analyzed object of interest : the number of objects in your sample
             (for example the number of differentially expressed genes in a list).
            -number of analyzed object of reference : the number of objects in your population
             (for example the number of genes in the genome of your species).
            -alpha : the alpha threshold also known as type I error.
            -normal approximation threshold : the threshold separating the hypergeometric test
             (which runs very slowly when using big numbers) and normal approximation.
    '''

    def __init__(self, dataframe, name_column_interest, name_column_reference,
                 number_of_object_of_interest, number_of_genes_in_reference,
                 alpha, threshold_normal_approximation):
        self.dataframe = dataframe.copy()
        self._output_columns = [name_column_interest, name_column_reference,
                                'PercentageInInterest', 'PercentageInReference',
                                'pvalue_hypergeometric', 'pValueBonferroni',
                                'pValueHolm', 'pValueBenjaminiHochberg', 'pValueBenjaminiYekutieli']
        self._column_interest = name_column_interest
        self._column_reference = name_column_reference
        self._number_of_analyzed_object_of_interest = number_of_object_of_interest
        self._number_of_analyzed_object_of_reference = number_of_genes_in_reference
        self._alpha = alpha
        self._normal_approximation_threshold = threshold_normal_approximation
        self._statistic_method = ""
        self.multiple_test_names = ['Sidak', 'Bonferroni', 'Holm', 'BenjaminiHochberg', 'BenjaminiYekutieli']

    @property
    def output_columns(self):
        return self._output_columns

    @output_columns.setter
    def output_columns(self, index, column_name):
        self._output_columns[index] = column_name

    @property
    def column_interest(self):
        return self._column_interest

    @column_interest.setter
    def column_interest(self, column_name):
        self._column_interest = column_name

    @property
    def column_reference(self):
        return self._column_reference

    @column_reference.setter
    def column_reference(self, column_name):
        self._column_reference = column_name

    @property
    def number_of_analyzed_object_of_interest(self):
        return self._number_of_analyzed_object_of_interest

    @number_of_analyzed_object_of_interest.setter
    def number_of_analyzed_object_of_interest(self, value):
        if value > self.number_of_analyzed_object_of_reference:
            raise ValueError("The number of objects in your sample of interest is greater than the number of objects in the reference.")
        else:
            self._number_of_analyzed_object_of_interest = value

    @property
    def number_of_analyzed_object_of_reference(self):
        return self._number_of_analyzed_object_of_reference

    @number_of_analyzed_object_of_reference.setter
    def number_of_analyzed_object_of_reference(self, value):
        if value < self.number_of_analyzed_object_of_interest:
            raise ValueError("The number of objects in the reference is smaller than the number of objects in your sample of interest.")
        else:
            self._number_of_analyzed_object_of_reference = value

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, value):
        self._alpha = value

    @property
    def statistic_method(self):
        return self._statistic_method

    @statistic_method.setter
    def statistic_method(self, method_name):
        self._statistic_method = method_name

    @property
    def normal_approximation_threshold(self):
        return self._normal_approximation_threshold

    @normal_approximation_threshold.setter
    def normal_approximation_threshold(self, value):
        self._normal_approximation_threshold = value

    def test_on_dataframe(self, df):
        analyzed_objects_with_hypergeo_test_nan = []

        approximation_threshold = self.normal_approximation_threshold

        value_higher_threshold = all(df[self.column_interest] > approximation_threshold)

        if value_higher_threshold == False:
            self.statistic_method = "pvalue_hypergeometric"

            df[self.statistic_method] = df.apply(self.compute_hypergeometric_test,
                                                 axis=1)
            df = df.sort_values(self.statistic_method)

        elif value_higher_threshold == True:
            self.output_columns[4] = 'pvalue_normal_approximation'
            self.statistic_method = 'pvalue_normal_approximation'
            df[self.statistic_method] = df.apply(self.compute_normal_approximation,
                                                 axis=1)
            df = df.sort_values(self.statistic_method)

        return df

    def compute_hypergeometric_test(self, row):
        number_of_object_in_interest = row[self.column_interest]
        number_of_object_in_reference = row[self.column_reference]

        pvalue_hypergeo = stats.hypergeom.sf(number_of_object_in_interest - 1, self.number_of_analyzed_object_of_reference,
                                                    number_of_object_in_reference, self.number_of_analyzed_object_of_interest)

        return pvalue_hypergeo

    def compute_normal_approximation(self, row):
        number_of_object_in_interest = row[self.column_interest]
        number_of_object_in_reference = row[self.column_reference]

        p = number_of_object_in_reference / self.number_of_analyzed_object_of_reference
        q = 1 - p
        t = self.number_of_analyzed_object_of_interest / self.number_of_analyzed_object_of_reference

        mu = self.number_of_analyzed_object_of_interest  * p

        if 0 in [self.number_of_analyzed_object_of_interest, p, q, (1 - t)]:
            return np.nan

        sigma = math.sqrt(self.number_of_analyzed_object_of_interest  * p * q * (1 - t))

        pvalue_normal = stats.norm.sf(number_of_object_in_interest, loc=mu, scale=sigma)

        return pvalue_normal

    def multiple_testing_correction(self, df):
        logger.info('-------------------------------------Multiple testing correction-------------------------------------')
        df = df.sort_values([self.statistic_method])

        df = self.correction_bonferroni(df)
        df = self.correction_benjamini_hochberg(df)
        df = self.correction_benjamini_yekutieli(df)
        df = self.correction_holm(df)

        significative_objects = {}

        for multiple_test_name in self.multiple_test_names:
            if multiple_test_name == 'Sidak':
                error_rate = self.error_rate_adjustement_sidak(df)
            elif multiple_test_name == 'Bonferroni':
                error_rate = self.error_rate_adjustement_bonferroni(df)
            if multiple_test_name in ['Sidak', 'Bonferroni']:
                object_significatives = self.selection_object_with_adjusted_error_rate(error_rate, df)
            elif multiple_test_name in ['Holm', 'BenjaminiHochberg', 'BenjaminiYekutieli']:
                object_significatives = self.selection_object_with_adjusted_pvalue(multiple_test_name, df)

            significative_objects[multiple_test_name] = object_significatives

        logger.debug('Multiple testing correction dataframe: %s', df)

        return df, significative_objects

    def writing_output(self, df, significative_objects):
        '''
        For the second results file (file with significative objects):
        Results are written using sorted(dictionnary), so the list of result corresponds to : 
        Sidak (position 4 in the list), Bonferroni (position 2),
        Holm (position 3), Benjamini & Hochberg (position 0) and Benjamini & Yekutieli (position 1).
        '''
        logger.info('-------------------------------------Write output-------------------------------------')

        df.sort_values(['pValueBenjaminiHochberg'], inplace=True)

        comment_file = open("results_annotation_over.tsv", "w")
        comment_file.write("# Number of objects in reference : " + str(self.number_of_analyzed_object_of_reference) +
                                        "\t Number of objects in interest : " + str(self.number_of_analyzed_object_of_interest) +"\n")
        df.to_csv(comment_file, sep="\t", float_format='%.6f', index=True, header=True, quoting=csv.QUOTE_NONE)

        comment_file.close()

        csvfile = open("results_significatives_over.tsv", "w", newline="")

        writer = csv.writer(csvfile, delimiter="\t")
        writer.writerow(['Sidak', 'Bonferroni', 'Holm', 'BenjaminiHochberg', 'BenjaminiYekutieli'])

        number_significatives_per_method = {}

        for method in significative_objects:
            number_significatives_per_method[method] = len(significative_objects[method])

        max_significatives_method = max(number_significatives_per_method, key = number_significatives_per_method.get)

        for index in range(len(significative_objects[max_significatives_method])):
            results = []
            for method in sorted(significative_objects):
                if index in range(len(significative_objects[method])):
                    object_significatives_value = significative_objects[method][index]
                else:
                    object_significatives_value = 'nonsignificant'
                results.append(object_significatives_value)

            writer.writerow([results[4], results[2], results[3],
                             results[0], results[1]])

        csvfile.close()

    def correction_bonferroni(self, df):
        number_of_test = len(df.index)
        pvalue_correction_bonferroni = lambda pvalue: 1 if pvalue * number_of_test > 1 else pvalue * number_of_test

        df['pValueBonferroni'] = df[self.statistic_method].apply(pvalue_correction_bonferroni)

        return df

    def correction_benjamini_hochberg(self, df):
        df.sort_values(by=self.statistic_method, ascending=True, inplace=True)
        number_of_test = len(df.index)
        ranks = np.arange(number_of_test) + 1

        qvalue_BH = df[self.statistic_method] * (number_of_test / (ranks))
        qvalue_BH_desc = qvalue_BH[::-1] # Inverse the order to look at each qvalue with minimum.accumulate().
        qvalue_BH_fixed = np.minimum.accumulate(qvalue_BH_desc)[::-1] # Verify if value violate the initial order, if not replace the pvalue.
        qvalue_BH_fixed = np.minimum(1, qvalue_BH_fixed)
        df['pValueBenjaminiHochberg'] = qvalue_BH_fixed

        return df

    def correction_benjamini_yekutieli(self, df):
        df.sort_values(by='pvalue_hypergeometric', ascending=True, inplace=True)

        df['pValueBenjaminiYekutieli'] = multipletests(df['pvalue_hypergeometric'].tolist(), alpha=0.05, method="fdr_by")[1]

        return df

    def correction_holm(self, df):
        df.sort_values(by=self.statistic_method, ascending=True, inplace=True)

        number_of_test = len(df.index)
        pvalue_max = 0

        for analyzed_object, row in df.iterrows():
            rank = df.index.get_loc(analyzed_object)
            pvalue_correction_holm = row[self.statistic_method] * (number_of_test - rank)
            if pvalue_correction_holm > 1:
                pvalue_correction_holm = 1
            if pvalue_correction_holm > pvalue_max:
                pvalue_max = pvalue_correction_holm
            if pvalue_max > pvalue_correction_holm:
                pvalue_correction_holm = pvalue_max
            if pvalue_correction_holm > self.alpha and pvalue_max < pvalue_correction_holm:
                pvalue_max = pvalue_correction_holm

            df.at[analyzed_object, 'pValueHolm'] = pvalue_correction_holm

        return df

    def error_rate_adjustement_bonferroni(self, df):
        error_rate_adjusted = self.alpha / len(df.index)

        return error_rate_adjusted

    def error_rate_adjustement_sidak(self, df):
        error_rate_adjusted = (1 - math.pow((1 - self.alpha), (1 / len(df.index))))

        return error_rate_adjusted

    def selection_object_with_adjusted_error_rate(self, error_rate, df):
        '''
        Return a list containing all the significatives objects (all the objects having a pvalue lower than the error_rate).
        This selection method is used by Sidak and Bonferroni multiple testing correction.
        '''

        return df[df[self.statistic_method] < error_rate].dropna(0).index.tolist()

    def selection_object_with_adjusted_pvalue(self, method_name, df):
        '''
        Return a list containing all the significatives objects (all the objects having a pvalue lower than the alpha threshold).
        This selection method is used by Holm, Benjamini & Hochberg and Benjamini & Yekutieli multiple testing correction.
        '''
        df.replace('', np.nan, regex=True, inplace=True)

        return df[df['pValue' + method_name] < self.alpha].dropna(0).index.tolist()

    def enrichment_analysis(self):
        logger.info('-------------------------------------Enrichment Analysis-------------------------------------')

        logger.debug('Name of the column of interest: %s', self.column_interest)
        logger.debug('Name of the column of reference: %s', self.column_reference)
        logger.debug('Number of analyzed objects in interest: %s', self.number_of_analyzed_object_of_interest)
        logger.debug('Number of analyzed objects in reference: %s', self.number_of_analyzed_object_of_reference)
        logger.debug('Alpha: %s', self.alpha)

        dataframe_used = self.dataframe

        percentage_calculator = lambda numerator, denominator: (numerator / denominator) * 100

        dataframe_used['PercentageInInterest'] = percentage_calculator(dataframe_used[self.column_interest], 
                                                self.number_of_analyzed_object_of_interest)

        dataframe_used['PercentageInReference'] = percentage_calculator(dataframe_used[self.column_reference],
                                                                                self.number_of_analyzed_object_of_reference)
        logger.debug('input_dataframe: %s', dataframe_used)

        dataframe_used = self.test_on_dataframe(dataframe_used)
        dataframe_used, significative_objects = self.multiple_testing_correction(dataframe_used)

        yes_answers = ['yes', 'y', 'oui', 'o']
        yes_or_no = input("Do you want to write results in file? ")

        if yes_or_no in yes_answers:
            self.writing_output(dataframe_used, significative_objects)

        return dataframe_used


class AnnotationEnrichmentAnalysis(PandasBasedEnrichmentAnalysis):
    '''
    Annotation (GO terms, Enzyme Codes, Interpro) Enrichment Analysis on data
    using Pandas Based Enrichment Analysis.

    This class takes two new attributes:
        -annotation_label_to_numbers: it is a dictionnary containing annotation
    number as key and annotation label as value. It allows a translation of
    annotation id to ease reading results. The dictionnary can be obtained
    with the functions contained in preprocessing.py (for GO terms, EC number
    and InterPro identifiers).
        -annotation_category: it is a string, it will be the name of the
    column which will contain the label of the annotation translated.
    '''
    def __init__(self, dataframe, name_column_interest, name_column_reference,
                 number_of_object_of_interest, number_of_genes_in_reference,
                 alpha, threshold_normal_approximation, annotation_label_to_numbers,
                 annotation_category):
        PandasBasedEnrichmentAnalysis.__init__(self, dataframe, name_column_interest, name_column_reference,
                 number_of_object_of_interest, number_of_genes_in_reference,
                 alpha, threshold_normal_approximation)
        self.output_columns.append(annotation_category)
        self._annotation_id_to_labels = annotation_label_to_numbers
        self.annotation = annotation_category

    @property
    def annotation_id_to_labels(self):
        return self._annotation_id_to_labels

    @annotation_id_to_labels.setter
    def annotation_id_to_labels(self, annotation_dictionnary):
        self._annotation_id_to_labels = annotation_dictionnary

    def tranlsation_id_to_label(self, annotation_numbers, annotation_id_to_labels):
        annotation_labels = []

        for annotation_number in annotation_numbers:
            if annotation_number in annotation_id_to_labels:
                annotation_labels.append(annotation_id_to_labels[annotation_number])

        return annotation_labels

    def multiple_testing_correction(self, df):
        logger.info('-------------------------------------Multiple testing correction with GO translation-------------------------------------')
        df.sort_values([self.statistic_method], inplace=True)

        df = self.correction_bonferroni(df)
        df = self.correction_benjamini_hochberg(df)
        df = self.correction_benjamini_yekutieli(df)
        df = self.correction_holm(df)

        significative_objects = {}
        translation_annotation_id_to_name = self.annotation_id_to_labels

        logger.debug('Annotation ID/Label dictionary: %s', len(translation_annotation_id_to_name))

        for multiple_test_name in self.multiple_test_names:
            if multiple_test_name == 'Sidak':
                error_rate = self.error_rate_adjustement_sidak(df)
            elif multiple_test_name == 'Bonferroni':
                error_rate = self.error_rate_adjustement_bonferroni(df)
            if multiple_test_name in ['Sidak', 'Bonferroni']:
                object_significatives = self.selection_object_with_adjusted_error_rate(error_rate, df)
            elif multiple_test_name in ['Holm', 'BenjaminiHochberg', 'BenjaminiYekutieli']:
                object_significatives = self.selection_object_with_adjusted_pvalue(multiple_test_name, df)

            annotation_label_significatives = self.tranlsation_id_to_label(object_significatives, translation_annotation_id_to_name)
            significative_objects[multiple_test_name] = annotation_label_significatives

        df[self.annotation] = [translation_annotation_id_to_name[annotation] for annotation in df.index if annotation in translation_annotation_id_to_name]

        logger.debug('Dataframe with Annotation labels: %s', df)

        return df, significative_objects


class EnrichmentAnalysisExperimental(PandasBasedEnrichmentAnalysis):
    '''
    Experimental part of the script with SGoF multiple testing correction.
    '''
    def __init__(self, dataframe, name_column_interest, name_column_reference,
                 number_of_object_of_interest, number_of_genes_in_reference,
                 alpha, threshold_normal_approximation):
        PandasBasedEnrichmentAnalysis.__init__(self, dataframe, name_column_interest, name_column_reference,
                 number_of_object_of_interest, number_of_genes_in_reference,
                 alpha, threshold_normal_approximation)
        self.multiple_test_names = ['Sidak', 'Bonferroni', 'Holm', 'SGoF', 'BenjaminiHochberg', 'BenjaminiYekutieli']

    def multiple_testing_correction(self, df):
        logger.info('-------------------------------------Multiple testing correction-------------------------------------')
        df = df.sort_values([self.statistic_method])

        df = self.correction_bonferroni(df)
        df = self.correction_benjamini_hochberg(df)
        df = self.correction_benjamini_yekutieli(df)
        df = self.correction_holm(df)
        df = self.correction_sgof(df)

        significative_objects = {}

        for multiple_test_name in self.multiple_test_names:
            if multiple_test_name == 'Sidak':
                error_rate = self.error_rate_adjustement_sidak(df)
            elif multiple_test_name == 'Bonferroni':
                error_rate = self.error_rate_adjustement_bonferroni(df)
            if multiple_test_name in ['Sidak', 'Bonferroni']:
                object_significatives = self.selection_object_with_adjusted_error_rate(error_rate, df)
            elif multiple_test_name in ['Holm', 'BenjaminiHochberg', 'BenjaminiYekutieli']:
                object_significatives = self.selection_object_with_adjusted_pvalue(multiple_test_name, df)
            elif multiple_test_name == 'SGoF':
                object_significatives = self.selection_object_with_sgof(multiple_test_name, df)

            significative_objects[multiple_test_name] = object_significatives

        logger.debug('Multiple testing correction dataframe: %s', df)

        return df, significative_objects

    def writing_output(self, df, significative_objects):
        '''
        For the second results file (file with significative objects):
        Results are written using sorted(dictionnary), so the list of result corresponds to : Sidak (position 5 in the list), Bonferroni (position 2),
        Holm (position 3), SGoF (position 4), Benjamini & Hochberg (position 0) and Benjamini & Yekutieli (position 1).
        '''
        logger.info('-------------------------------------Write output-------------------------------------')
        df.sort_values(['pValueBenjaminiHochberg'], inplace=True)

        df = df[self.output_columns]

        comment_file = open("results_" + self.object_to_analyze + "_over.tsv", "w")
        comment_file.write("# Number of objects in reference : " + str(self.number_of_analyzed_object_of_reference) +
                                        "\t Number of objects in interest : " + str(self.number_of_analyzed_object_of_interest) +"\n")
        df.to_csv(comment_file, sep="\t", float_format='%.6f', index=True, header=True, quoting=csv.QUOTE_NONE)

        comment_file.close()

        csvfile = open("results_significatives" + self.object_to_analyze + "_over.tsv", "w", newline="")

        writer = csv.writer(csvfile, delimiter="\t")
        writer.writerow([self.object_to_analyze + 'Sidak', self.object_to_analyze + 'Bonferroni', self.object_to_analyze + 'Holm',
        self.object_to_analyze + 'SGoF', self.object_to_analyze + 'BenjaminiHochberg', self.object_to_analyze + 'BenjaminiYekutieli'])

        number_significatives_per_method = {}

        for method in significative_objects:
            number_significatives_per_method[method] = len(significative_objects[method])

        max_significatives_method = max(number_significatives_per_method, key = number_significatives_per_method.get)

        for index in range(len(significative_objects[max_significatives_method])):
            results = []
            for method in sorted(significative_objects):
                if index in range(len(significative_objects[method])):
                    object_significatives_value = significative_objects[method][index]
                else:
                    object_significatives_value = 'nonsignificant'
                results.append(object_significatives_value)

            writer.writerow([results[5], results[2], results[3],
            results[4], results[0], results[1]])

        csvfile.close()

    def correction_sgof(self, df):
        '''
            This python version of the SGoF algorithm has been developped using the algorithm described in Carvajal-Rodriguez et al. (BMC Bioinformatics 10:209, 2009)
            and the MATLAB version developped by Garth Thompson.
            The MATLAB version is accessible at : http://acraaj.webs.uvigo.es/software/matlab_sgof.m
        '''
        df.sort_values("pvalue_hypergeometric", inplace=True)

        number_pvalue = len(df.pvalue_hypergeometric)
        R = (df['pvalue_hypergeometric'] < self.alpha).sum()

        index_column_name = df.index.name
        df.reset_index(inplace=True)

        row_number = 0

        if number_pvalue <= 10:
            mutliple_values = list(stats.binom.sf(range(1, R+2), len(df), self.alpha)[:-1])
            reordered_pvalues = mutliple_values[::-1]

            pvalues_remaining = number_pvalue-R
            df['pValueSGoF'] = ['significant' if pvalue <= self.alpha else np.nan
                                for pvalue in reordered_pvalues] + [np.nan]*pvalues_remaining
            df['pValueSGoFValue'] = reordered_pvalues + [np.nan]*pvalues_remaining
        else:
            if number_pvalue == R:
                R = R - 1
            l_R_value = [number for number in range(1, R+2)]

            l_R_value_divide = np.divide(l_R_value, (number_pvalue * self.alpha))
            l_R_value_log = np.log(l_R_value_divide)
            below_alpha = np.multiply(l_R_value, l_R_value_log)

            l_R_value_minus_pvalue = np.subtract(number_pvalue, l_R_value)
            number_pvalue_multiply_alpha = number_pvalue * (1 - self.alpha)
            l_R_value_minus_divide = np.divide(l_R_value_minus_pvalue, number_pvalue_multiply_alpha)
            l_R_value_minus_value_log = np.log(l_R_value_minus_divide)
            above_alpha = np.multiply(l_R_value_minus_pvalue, l_R_value_minus_value_log)

            william_factor = (1+1/(2*number_pvalue))

            correction_above_alpha = np.divide(above_alpha, william_factor)
            below_above_alpha_add = np.add(below_alpha, correction_above_alpha)
            prob_each_pvalues = np.multiply(below_above_alpha_add, 2)

            g_threshold = stats.chi2.ppf(1 - self.alpha,1)

            reordered_pvalues = prob_each_pvalues[::-1]
            df['pValueSGoF'] = ''

            for corrected_value in reordered_pvalues:
                if len(reordered_pvalues) == 1:
                    if corrected_value >= g_threshold:
                        df.at[row_number, 'pValueSGoF'] = 'significant'
                        df.at[row_number, 'pValueSGoFValue'] = corrected_value
                        row_number = row_number + 1
                    else:
                        df.at[row_number, 'pValueSGoF'] = np.nan
                        df.at[row_number, 'pValueSGoFValue'] = np.nan
                        row_number = row_number + 1
                if len(prob_each_pvalues) > 1:
                    if prob_each_pvalues[-1] >= prob_each_pvalues[-2]:
                        if corrected_value >= g_threshold:
                            df.at[row_number, 'pValueSGoF'] = 'significant'
                            df.at[row_number, 'pValueSGoFValue'] = corrected_value
                            row_number = row_number + 1
                        else:
                            df.at[row_number, 'pValueSGoF'] = np.nan
                            df.at[row_number, 'pValueSGoFValue'] = np.nan
                            row_number = row_number + 1
                    else:
                        df.at[row_number, 'pValueSGoF'] = np.nan
                        df.at[row_number, 'pValueSGoFValue'] = np.nan
                        row_number = row_number + 1
            if R == 0:
                df['pValueSGoF'] = np.nan

            df.replace('', np.nan, inplace=True)

        column_names = df.columns.tolist()
        column_names[0] = index_column_name

        df.columns = column_names
        df.set_index(index_column_name, inplace=True)

        return df

    def selection_object_with_sgof(self, method_name, df):
        df.replace(np.nan, '', regex=True, inplace=True)

        return df[df['pValue' + method_name] == 'significant'].dropna(0).index.tolist()
