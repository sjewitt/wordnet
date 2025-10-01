'''
Created on 9 Jan 2023

@author: silasj@grange.taxonomics.co.uk
'''
import json
from nltk.corpus import WordnetAPI

pos_lookup = {
    'n':'Noun',
    'v':'Verb',
    'a':'Adjective',
    'r':'Adverb'
    }

    
def extract_json_from_synset(synset):
    output = {}
    output['name'] = synset.name()
    output['definition'] = synset.definition()
    output['part_of_speech'] = pos_lookup.get(synset.pos(),None)
    # print(' --> ',output)
    return output
    
    
def synset_similarity(s1, s2, comparison_type=None):
    print(s1.name(),s2.name())
    if comparison_type == 'lch':        # Leacock-Chodorow Similarity
        return s1.lch_similarity(s2)
    if comparison_type == 'wup':
        return s1.wup_similarity(s2)
    return s1.path_similarity(s2)

def print_synsets(synset_list):
    for synset in synset_list:
        print(' --> Name: ',synset.name())
        print(' --> hyponyms: ',synset.hyponyms())
        print(' --> hypernyms: ', synset.hypernyms()) 
        print(' --> Lemmas: ',synset.lemmas())
        synset_json = extract_json_from_synset(synset)
        print('JSON: ', synset_json)    #well it's a dict ATM...
        print('-------------------------------------------------------------------------------------------------------------')

haddock = WordnetAPI.synsets('haddock')
fish = WordnetAPI.synsets('fish')
fly_fishing = WordnetAPI.synsets('fly-fishing')

vertebrate = WordnetAPI.synsets('vertebrate')
chordate = WordnetAPI.synsets('chordate')

print_synsets(vertebrate)
print('###########################################################################################################')

print_synsets(chordate)
print('###########################################################################################################')

#print_synsets(fly_fishing)
#print('###########################################################################################################')
#print_synsets(fish)
#print('###########################################################################################################')
print('similarity test:')
print(synset_similarity(vertebrate[0], chordate[0]))

print('compare chordate hyponyms:')
for hyponym in chordate[0].hyponyms():
    print(synset_similarity(hyponym,vertebrate[0]))

#for fishset in fish:
#    # synset_similarity(fly_fishing[0],fishset)
#    synset_similarity(haddock[0],fishset)


    