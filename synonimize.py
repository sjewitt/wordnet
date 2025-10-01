'''
This will eventuallly need to move to a server-side routine!!!!

test utility to pairwise compare terms in a single input data file
'''

# import sys
# import os

import argparse
# import requests
# import json
from csv import reader
import uuid
import nltk
from nltk.corpus import stopwords

import tensorflow as tf
import tensorflow_hub as hub

from libs.wordnet_api import WordnetAPI

from sentence_transformers import SentenceTransformer, util

from libs.wordnet_database import Database


def main():
    job_uuid = str(uuid.uuid4())
    # Setup argument parser
    parser = argparse.ArgumentParser(description='process terms list with descriptions for synonymity')
    parser.add_argument("-f", "--file", help="file including full path", required=True)
    parser.add_argument("-t", "--term_column", help="zero-indexed term column number", type=int, required=True)                         # this is the thing described
    parser.add_argument("-d", "--data_to_process_column", help="zero-indexed description column number", type=int, required=True)           # this will be analysed
    parser.add_argument("-r", "--raw_description_column", help="zero-indexed raw description column number", type=int, required=True)   # this is the full, unmodified description for display purposes only
    # database name (default to 'comparison.db')
    parser.add_argument("-n", "--database_name", help="name of SQLite database to use (default=comparison.db)", type=str, required=False, default='comparison.db')
    parser.add_argument("-m", "--method", help="phrase compare method - pw, cos, tf and rb (default)", required=False, default='rb')
    parser.add_argument("-c", "--cutoff", help="value considered to be a match for the chosen dataset/method", required=False, type=float, default=0.5)

    # Process arguments
    args = parser.parse_args()

    print(args)

    # custom_stopword_list = ['would','de-identified']
    # stops = stopwords.words('english')
    # print(stops)

    wn = WordnetAPI(args.database_name)

    with open(args.file, encoding='UTF-8') as f:
        print('processing by %s method' % args.method)
        csvreader = reader(f, delimiter='\t')
        # https://stackoverflow.com/questions/14257373/how-to-skip-the-headers-when-processing-a-csv-file-using-python
        next(csvreader, None)

        insert_result = wn.db.add_job_row(job_uuid, args.method, args.file,args.file,'synonimize.py')

        if args.method == 'tf':
            result = wn.tf_embed()
            print(result)
            

        terms1 = []
        terms2 = []
        for row in csvreader:
            processed_list = []

            if args.method == 'pw': # pair-wise 
                for word in row[args.data_to_process_column].split(' '):
                    word = word.replace("'",'').replace('"','').replace(')','').replace('(','').replace('&','').replace('.','').replace(' ','_').replace(',','').replace('’','').lower()
                    print(word)
                    try:
                        if not wn.is_stopword(word)['is_stop_word']:
                            stem = wn.stem(word)['stemmed_word']
                            processed_list.append(word)
                    except:
                        pass
                terms1.append({'data' : processed_list, 'raw_description':row[args.data_to_process_column],'term':row[args.term_column],'display_description':row[args.raw_description_column]})
                terms2.append({'data' : processed_list, 'raw_description':row[args.data_to_process_column],'term':row[args.term_column],'display_description':row[args.raw_description_column]})

            #refactor this!!
            # if args.method == 'cos': #we don't need to split into words, so just append the specified indexes:
            else:
                terms1.append({'data' : row[args.data_to_process_column], 'raw_description':row[args.data_to_process_column],'term':row[args.term_column],'display_description':row[args.raw_description_column]})
                terms2.append({'data' : row[args.data_to_process_column], 'raw_description':row[args.data_to_process_column],'term':row[args.term_column],'display_description':row[args.raw_description_column]})

        counter = 0
        for term1 in terms1:
            counter += 1
            for term2 in terms2[counter:]:
                try:
                    res = wn.phrase_similarity(term1['data'], term2['data'], False,args.method)
                    if res['status'] == 'ok':
                        comp_value = res['result']['calculated_similarity']
                    else:
                        comp_value = res['message']

                    # drop unfiltered data into database:
                    # ,job_uuid,comparison_score,term_1,description_1,term_2,description_2
                    insert_result = wn.db.add_comparison_row(job_uuid, comp_value,term1['term'],term1['display_description'],term2['term'],term2['display_description'])

                    if comp_value > args.cutoff:
                        print('Comparison value: %s \n %s: %s \n %s: %s' % (comp_value,term1['term'],term1['display_description'],term2['term'],term2['display_description']))
                except Exception as ex:
                    # print('%s \n %s: %s \n %s: %s' % (comp_value,term1['term'],term1['display_description'],term2['term'],term2['display_description']))
                    print(ex)

if __name__ == '__main__':
    main()
            #print(row[args.data_to_process_column])
            # TEST OF EXCLUDING REVERSED AND SAME TEMS FOR A SELF-COMPARISON MATRIX (I.E. TESTING WITH ONE INPUT FILE)
            # print(f)
            # for line in f:
            #     print(line.rstrip())
            # now do pairwise compare of these terms - ideally eliminating reverse dupes... TODO: !!
            # see https://stackoverflow.com/questions/33626623/the-most-efficient-way-to-remove-first-n-elements-in-a-list
            # this:
            #
            # data = [
            #     'a','b','c','d','e'
            #    ]
            # counter = 0
            # for x in data:
            #     counter+=1
            #     for y in data[counter:]:
            #     print(x,y)
            # removes processing of ((data.length ^ 2) / 2) + data.length iterations...

