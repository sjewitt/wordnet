'''
Utility to take two input TSVs of terms to synonymize and output a list (TSV, JSON, database - TBD) ordered by
comparison score to assist manual synonimization.
'''

import argparse
from datetime import datetime
from csv import reader
# import nltk
# import sqlite3
import uuid
# from nltk.corpus import stopwords
import tensorflow as tf
import tensorflow_hub as hub
from libs.wordnet_api import WordnetAPI
# from libs.wordnet_database import Database



def main():
    ''' entry point '''
    job_uuid = str(uuid.uuid4())

    # Setup argument parser
    parser = argparse.ArgumentParser(description='process terms list with descriptions for synonymity')

    # INPUT FILES
    parser.add_argument("-f", "--file1", help="file 1, including full path", required=True)
    parser.add_argument("-g", "--file2", help="file 2, including full path", required=True)

    # SPECIFY COLUMNS TO PROCESS, FILE 1
    # We always need this field because this is the field containing the lexical strings to be compared for similarity:
    parser.add_argument("-d", "--data_to_process_column_1", help="zero-indexed field to process column number", type=int, required=True)

    # This is the thing being described. It might be a meaningful term ('Internal maintenance task') or might be a serial number ('IMT_003')...
    parser.add_argument("-t", "--term_column_1", help="zero-indexed TERM column number", type=int, required=True)

    # This is the description field, used in the output. It is specified explicitly here because the strings being compared (-d) MAY be defined as the 'thing being described' column
    parser.add_argument("-r", "--raw_description_column_1", help="zero-indexed raw description column number", type=int, required=True)

    # database name (default to 'comparison.db')
    parser.add_argument("-n", "--database_name", help="name of SQLite database to use (default=comparison.db)", type=str, required=False, default='comparison.db')

    # SPECIFY COLUMNS TO PROCESS, FILE 2
    # These are all OPTIONAL, and if not specified will inherit the same values specified for FILE_1
    # We always need this field because this is the field containing the lexical strings to be compared for similarity:
    parser.add_argument("-e", "--data_to_process_column_2", help="zero-indexed field to process column number", type=int, required=False, default=-1)

    # This is the thing being described. It might be a meaningful term ('Internal maintenance task') or might be a serial number ('IMT_003')...
    parser.add_argument("-u", "--term_column_2", help="zero-indexed TERM column number", type=int, required=False, default=-1)

    # This is the description field, used in the output. It is specified explicitly here because the strings being compared (-d) MAY be defined as the 'thing being described' column
    parser.add_argument("-s", "--raw_description_column_2", help="zero-indexed raw description column number", type=int, required=False, default=-1)

    # SPECIFY COMPARISON PARAMETERS
    # Optionally specify the comparison method. Defaults to 'cos' ('cos' and 'pw' available currently)
    parser.add_argument("-m", "--method", help="phrase compare method (pw or cos so far)", required=False, default='cos')

    # Optionally specify the cutoff at which a comparison implies a synonymity. Default 0.5.
    parser.add_argument("-c", "--cutoff", help="value considered to be a match for the chosen dataset/method", required=False, type=float, default=0.5)

    # Process arguments
    args = parser.parse_args()

    # instantiate the database object:
    # db = Database(args.database_name)

    #set fields for file 2 if the same as file 1:
    if args.data_to_process_column_2 == -1:
        args.data_to_process_column_2 = args.data_to_process_column_1

    if args.term_column_2 == -1:
        args.term_column_2 = args.term_column_1

    if args.raw_description_column_2 == -1:
        args.raw_description_column_2 = args.raw_description_column_1

    print(args)

    # custom_stopword_list = ['would','de-identified']
    # stops = stopwords.words('english')
    # print(stops)

    wordnet = WordnetAPI(args.database_name)

    with open(args.file1, encoding='UTF-8') as file_1:
        # print('processing by %s method' % args.method)
        print(f'processing by {args.method} method')
        csvreader_1 = reader(file_1, delimiter='\t')

        # https://stackoverflow.com/questions/14257373/how-to-skip-the-headers-when-processing-a-csv-file-using-python
        next(csvreader_1, None) #assume header row (but should be configurable)

        with open(args.file2, encoding='UTF-8') as file_2:
            csvreader_2 = reader(file_2, delimiter='\t')
            
            # we have opened the two files - drop an entry into the JOBS table for this run:
            insert_result = wordnet.db.add_job_row(job_uuid, args.method, args.file1,args.file2,'synonimize2.py')
            
            if args.method == 'tf':
                result = wordnet.tf_embed()
                print(result)
            
            next(csvreader_2, None) #assume header row (but should be configurable)

            terms1 = [] # from file_1
            terms2 = [] # from file_2
            for row_1 in csvreader_1:
                if args.method in ['cos','tf']: #we don't need to split into words, so just append the specified indexes:
                    terms1.append({'source':'file 1', 'data' : row_1[args.data_to_process_column_1], 'raw_description':row_1[args.data_to_process_column_1],'term':row_1[args.term_column_1],'display_description':row_1[args.raw_description_column_1]})
                    # terms2.append({'source':'file 2', 'data' : row_2[args.data_to_process_column_2], 'raw_description':row_2[args.data_to_process_column_2],'term':row_2[args.term_column_2],'display_description':row_2[args.raw_description_column_2]})

            for row_2 in csvreader_2:
                # Going to assume cos comparison for this test
                if args.method in ['cos','tf']: #we don't need to split into words, so just append the specified indexes:
                    # terms1.append({'source':'file 1', 'data' : row_1[args.data_to_process_column_1], 'raw_description':row_1[args.data_to_process_column_1],'term':row_1[args.term_column_1],'display_description':row_1[args.raw_description_column_1]})
                    terms2.append({'source':'file 2', 'data' : row_2[args.data_to_process_column_2], 'raw_description':row_2[args.data_to_process_column_2],'term':row_2[args.term_column_2],'display_description':row_2[args.raw_description_column_2]})

            counter = 0
            # https://www.programiz.com/python-programming/datetime/strftime
            output_file = f'output_{datetime.now().strftime("%d_%m_%Y-%H-%M-%S")}.tsv'
            # with open('output_test.tsv',encoding='UTF-8',mode='w+') as output:
            with open(output_file, encoding='UTF-8',mode='w+') as output:
                output.write('Comparison value:\tTerm 1:\tDescription 1\tTerm 2:\tDescription 2\n')
                for term1 in terms1:

                    for term2 in terms2:    # we do not want to restrict - we are comparing DIFFERENT lists
                        counter += 1
                        try:
                            res = wordnet.phrase_similarity(term1['data'], term2['data'], False,args.method)
                            if res['status'] == 'ok':
                                comp_value = res['result']['calculated_similarity']
                            else:
                                comp_value = res['message']
                            if comp_value > args.cutoff:
                                # print('Comparison value: %s \n %s: %s \n %s: %s' % (comp_value,term1['term'],term1['display_description'],term2['term'],term2['display_description']))
                                print(f'Comparison value: {comp_value} \n {term1["term"]}: {term1["display_description"]} \n {term2["term"]}: {term2["display_description"]}')
                                # output.write(f'Comparison value: {comp_value} \n {term1["term"]}: {term1["display_description"]} \n {term2["term"]}: {term2["display_description"]}\n')
                                output.write(f'{comp_value} \t {term1["term"]} \t {term1["display_description"]} \t {term2["term"]} \t {term2["display_description"]}\n')

                                # and drop into database:
                                insert_result = wordnet.db.add_comparison_row(job_uuid, comp_value, term1["term"].strip(), term1["display_description"].strip(), term2["term"].strip(), term2["display_description"].strip())
                                print(insert_result)
                        except Exception as ex:
                            # print('%s \n %s: %s \n %s: %s' % (comp_value,term1['term'],term1['display_description'],term2['term'],term2['display_description']))
                            # print(f'{comp_value} \n {term1["term"]}: {term1["display_description"]} \n {term2["term"]}: {term2["display_description"]}')
                            print(ex)
    print(f"Processed {counter} pairs")

    # now need to do a sort on this data (can do in spreadsheet, or can do programmatically - need to attach sqlite here...)

if __name__ == '__main__':
    main()
