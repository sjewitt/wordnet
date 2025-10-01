'''
Created on 11 Jan 2023

@author: silasj@grange.taxonomics.co.uk

ref:
https://www.nltk.org/howto/WordnetAPI.html
'''
# from nltk.stem import *
from nltk.corpus import stopwords
from nltk.corpus import wordnet as wn
from nltk.corpus.reader.wordnet import WordNetError
from nltk.stem.porter import PorterStemmer
from nltk.stem.snowball import SnowballStemmer
# import spacy

import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity          #cos
from sklearn.feature_extraction.text import CountVectorizer     #count

import tensorflow as tf
import tensorflow_hub as hub

# roberta, #pipenv install sentence-transformers
from sentence_transformers import SentenceTransformer, util

from libs.wordnet_database import Database


class WordnetAPI():
    '''
    Class containing various word analysis tools, as provided by the NLTK Wordnet extension, and some experimental phrase comparison
    utilities.
    '''

    # nlp = spacy.load('en_core_web_md')  #load on class instantiation
    pos_lookup = {
        'n':'noun',
        'v':'verb',
        'a':'adjective',
        'r':'adverb'
        }

    stemmer_lookup = {
        'po':'Porter',
        'sp':'Snowball (Porter)',
        'se':'Snowball (English)'
        }

    comparison_type_lookup = {
        'path' : 'Path',
        'wup' : 'Wu-Palmer',
        'lch' : 'Leacock-Chodorow'
        }
    custom_stopword_list = ['would','de-identified']
    stop_words = {} #a set

    embed = None    #for TF type

    def __init__(self, database_name):
        ''' Constructor '''
        # tensorflow data - load on startup:
        # self.embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
        
        WordnetAPI.stop_words = set(stopwords.words('english'))
        # self.db = Database()
        self.db = Database(database_name)

    def tf_embed(self):
        self.embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
        return {'status':'ok'}
    
    def get_jobs(self):
        return self.db.get_jobs()   #NOTE: This also needs to call the get_comparison_range db function

    def get_similar_terms(self,job_uuid, term,similarity_threshold, comparison_type):
        '''
        Call database function to retrieve prior processed terms that are similar to
        TERM, based on similarity score previously calculated for this comparison job
        (identified by JOB_UUID) within a supplied SIMILARITY_THRESHOLD.
        '''
        return self.db.get_similar_terms(job_uuid, term, similarity_threshold, comparison_type)
    
    def get_comparison_range(self,job_uuid):
        ''' call database function to return the comparison score range for specified job. This should assist with  '''
        return self.db.get_comparison_range(job_uuid)

    def get_filtered_terms(self, job_uuid, term,similarity_threshold):
        ''' get a list of terms where like provided term. Used to populate the autocomplete on the get_similar_terms page '''
        return self.db.get_filtered_terms(job_uuid, term,similarity_threshold)

    def get_synsets(self, word=None,retrieve_hyp=True):
        ''' wrapper function to return a JSON array of synsets for supplied word '''
        data = self._retrieve_synsets(word)
        out = {'source_word':word, 'synsets':[]}
        for synset in data['synsets']:
            out['synsets'].append(self.extract_json_from_synset(synset, retrieve_hyp))
        return out

    def get_synset_by_name(self, synset_name=None,retrieve_hyp=True):
        ''' wrapper function to return a JSON array of synsets for supplied word '''
        synset = self._retrieve_synset(synset_name)
        return self.extract_json_from_synset(synset, retrieve_hyp)

    def get_synset_count(self,word=None):
        ''' return a count of synsets for supplied word '''
        try:
            data = self._retrieve_synsets(word)
            return {'status':'ok','source_word':word,'synset_count':len(data['synsets'])}
        except Exception as ex:
            return {'status':'error','message':str(ex)}

    def _retrieve_synsets(self,word):
        ''' internal utility function to return a list of synsets for supplied word '''
        synsets = []
        if word:
            synsets = wn.synsets(word)
        return {'word':word,'synsets':synsets}

    def _retrieve_synset(self,synset_name):
        ''' internal utility function to return a single synset by name '''
        if synset_name:
            return wn.synset(synset_name)
        return {}

    def extract_json_from_synset(self,synset,retrieve_hyp=True):
        ''' build a structured list output format for a given synset. Can be extended as needed '''
        output = {}
        output['name'] = synset.name()
        output['definition'] = synset.definition()
        output['examples'] = synset.examples()
        output['part_of_speech'] = WordnetAPI.pos_lookup.get(synset.pos(),None)
        output['lemmas'] = self.get_lemma_strings(synset.lemmas())

        if retrieve_hyp:
            output['hypernyms'] = self.get_synset_hyps(synset.hypernyms())      # a word that is more generic than a given word (a sandwich is a kind of snack)
            output['hyponyms'] = self.get_synset_hyps(synset.hyponyms())        # a word that is more specific than a given word (a sandwich has many types e.g. a BLT)
            output['meronyms'] = self.get_synset_hyps(synset.part_meronyms())   # a word that names a part of a larger whole (bread is part of a sandwich)
            output['holonyms'] = self.get_synset_hyps(synset.part_holonyms())   # a word that names the whole of which a given word is a part (a meal includes a sandwich)

        return output

    def compare(self,data1,data2,comparison_type):
        ''' return a dict wrapper comparing the specified synset indexes for the two supplied
        root words. Note that this function does NOT check that the synset index for supplied word
        is out of range - this needs to be checked by the calling client '''
        try:
            synset1 = wn.synsets(data1[0])[data1[1]]
            synset2 = wn.synsets(data2[0])[data2[1]]
            return {
                'source_word_1': data1[0],
                'source_word_2': data2[0],
                'comparison_type':WordnetAPI.comparison_type_lookup[comparison_type],
                'synset1':self.extract_json_from_synset(synset1, False),    #don't spider out to hypernyms or hyponyms
                'synset2':self.extract_json_from_synset(synset2, False),    #don't spider out to hypernyms or hyponyms
                'similarity' : self.get_similarity_by_type(synset1, synset2, comparison_type)
                }
        except IndexError as err:
            return {'status':'error','message':str(err)}

    def compare_by_name(self,s1,s2,comparison_type):
        '''
        determine similarity, as measured by COMPARISON_TYPE, of supplied pair of SYNSETS
        '''
        synset1 = wn.synset(s1)
        synset2 = wn.synset(s2)
        try:
            return {
                    'comparison_type':WordnetAPI.comparison_type_lookup[comparison_type],
                    'synset1':self.extract_json_from_synset(synset1, False),    #don't spider out to hypernyms or hyponyms
                    'synset2':self.extract_json_from_synset(synset2, False),    #don't spider out to hypernyms or hyponyms
                    'similarity' : self.get_similarity_by_type(synset1, synset2, comparison_type)
                }
        except WordNetError as err:
            print(err)
            return None

    def test_relationship(self,relationship_type, test_synset, root_synset):
        '''
        determine whether TEST_SYNSET has RELATIONSHIP_TYPE to ROOT_SYNSET
        '''
        # load the root synset object
        root_synset_object = self.get_synset_by_name(root_synset, True)

        # and test whether test_synset (a name) exists as a property of root_synset[relationship_type]:
        for entry in root_synset_object[relationship_type]:
            if entry['name'] == test_synset:
                return True
        return False

    def stem(self,word,stemmer='se'):
        '''
        Return the stem of supplied word.

        See https://www.nltk.org/howto/stem.html
        stemmer types
        'snowball_english' -> 'se'
        'porter'           -> 'po'
        'snowball_porter'  -> 'sp'
        '''
        out = {'source_word':word, 'stemmed_word':None, 'stemmer_key':stemmer}
        if word and stemmer in ['po','sp','se']:
            out['stemmer_name'] = WordnetAPI.stemmer_lookup[stemmer]
            if stemmer == 'po':
                out['stemmed_word'] = PorterStemmer().stem(word)
            if stemmer == 'sp':
                out['stemmed_word'] = SnowballStemmer("porter").stem(word)
            if stemmer == 'se':
                out['stemmed_word'] = SnowballStemmer("english").stem(word)
        else:
            out['status'] = 'warning'
            warnings = []
            if not word:
                warnings.append('no supplied word to stem')
            if stemmer not in ['po','sp','se']:
                warnings.append(' '.join(['supplied stemmer key -',stemmer,'- does not exist']))
            out['message'] = '; '.join(warnings)
        return out

    def get_similarity_by_type(self,synset1, synset2,comparison_type):
        ''' return the similarity score for a pair of synsets by comparison type.
        See https://www.nltk.org/howto/stem.html '''
        # TODO change to match/case on update to 3.10+:
        # https://docs.python.org/3.10/whatsnew/3.10.html#pep-634-structural-pattern-matching
        try:
            out = -1
            if comparison_type == 'path':
                out = synset1.path_similarity(synset2)
            if comparison_type == 'lch':
                out = synset1.lch_similarity(synset2)
            if comparison_type == 'wup':
                out = synset1.wup_similarity(synset2)
            return {'status':'ok','comparison_type':comparison_type, 'comparison':out}
        except WordNetError as err:
            return {'status':'error', 'message': str(err)}

    def get_synset_hyps(self,synsets):
        ''' utility method to process an array of synsets - specifically, those returned as hypernyms or hyponyms of the root synset.
        passes False to the extract_json_from_synset() method to suppress further spidering '''
        out = []
        for synset in synsets:
            out.append(self.extract_json_from_synset(synset, False))
        return out

    def get_lemma_strings(self,lemmas):
        ''' return a list of lemma name srtings '''
        out = []
        for lemma in lemmas:
            out.append(lemma.name())
        return out

    def is_stopword(self,word):
        ''' return boolean whether supplied word is in the nltk corpus stopword list, or error if no word supplied
        see https://pythonspot.com/nltk-stop-words/'''
        if word:
            # updated to use NLTK stopword list and custom list as well as WN stopword list
            is_stopword = False
            if word in WordnetAPI.stop_words or word in WordnetAPI.custom_stopword_list:
                is_stopword = True

            # out = {'status':'ok','word':word,'is_stop_word':(word in WordnetAPI.stop_words)}
            out = {'status':'ok','word':word,'is_stop_word' : is_stopword}
            return out
        return {'status':'error', 'message':'word is not defined. This API endpoint requires GET request with `?word=yourword`'}

    def get_processed_list(self,words, remove_stopwords, perform_stem, stemmer):
        '''
        process a list of words for removal of stopwords and/or stemming
        '''
        out = {'source_data':words,'perform_stem':perform_stem}
        if remove_stopwords:
            #https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions
            words = [word for word in words if word not in WordnetAPI.stop_words]
        if perform_stem:
            words = [self.stem(word,stemmer) for word in words]
        out['processed_list'] = words
        return out

    def phrase_similarity(self, p1, p2,data_summary=False,phrase_comparison_type='pw', word_comparison_type='wup'):
        '''
        entry point for phrase compare. Initially, this will only be pairwise, max similarity, but hooks
        to allow later extension are in the args

        p1 and p2 are arrays of words - assume pre-procesing has already been done as per the UI
        '''
        _out = {
            'phrase1':p1,
            'phrase2':p2,
            'phrase_comparison_type':phrase_comparison_type,
            'word_comparison_type':word_comparison_type,
        }
        if phrase_comparison_type == 'pw':  #pairwise
            _result = self.phrase_similarity_pairwise(p1, p2, word_comparison_type)
            _out['result'] = _result
            _out['status'] = _result['status']
            _out['message'] = _result['message']
            return _out
        if phrase_comparison_type == 'cos': #cosine
            _result = self.phrase_similarity_cosine(p1, p2)
            _out['result'] = _result
            _out['status'] = _result['status']
            _out['message'] = _result['message']
            return _out
        if phrase_comparison_type == 'count': #count
            _result = self.phrase_similarity_count(p1, p2)
            _out['result'] = _result
            _out['status'] = _result['status']
            _out['message'] = _result['message']
            return _out
        if phrase_comparison_type == 'tf': #tensorflow
            _result = self.phrase_similarity_tf(p1, p2)
            _out['result'] = _result
            _out['status'] = _result['status']
            _out['message'] = _result['message']
            return _out
        if phrase_comparison_type == 'rb': #roberta
            _result = self.phrase_similarity_rb(p1, p2)
            _out['result'] = _result
            _out['status'] = _result['status']
            _out['message'] = _result['message']
            return _out
        return {'status':'warning','message':'cannot determine comparison method!'}

    def phrase_similarity_pairwise(self, p1, p2,word_comparison_type):
        '''
        Return a similarity score based on the highest WORD similarity score found between the
        two input phrases, excluding - ideally - stopwords.

        first, pairwise compare each term, then, for each word, I need a routine that accepts
        a pair of words and determines the highest similarity for the synsets of each word
        There may of course be > 1, so this gets recursive too.
        '''
        result = {'status':'ok','message':'ok','method':'pairwise'}

        try:
            max_similarity = -1
            closest_match_synset_pair = []
            root_words_for_matches = []
            for p1_word in p1:
                # get synset(s) for p1_word
                p1_word_synsets = wn.synsets(p1_word)   #we want actual Synset objects, notthe JSON abstraction
                if not p1_word_synsets:
                    raise WordNetError(f"No synsets found for '{p1_word}'. consider whether stemming is inappropriate")
                for p2_word in p2:
                    # now get the synset(s) for p2_word
                    p2_word_synsets = wn.synsets(p2_word)   #we want actual Synset objects, notthe JSON abstraction
                    # and compare each synset from p1 with synsets from p2
                    for p1_word_synset in p1_word_synsets:
                        for p2_word_synset in p2_word_synsets:
                            if not p2_word_synsets:
                                raise WordNetError(f"No synsets found for '{p2_word}'. consider whether stemming is inappropriate")
                            current_result = self.get_similarity_by_type(p1_word_synset,p2_word_synset,word_comparison_type)

                            # keep track of where we areNote for lch comparison, we need to check for POS errors:
                            try:
                                # this needs improving - if lch, the POS is taken into account, and the current structure of the data is
                                # inconsistent if the WN api throws back an incompatible POS error
                                if current_result['comparison'] > max_similarity:
                                    max_similarity = current_result['comparison']
                                    # and set the synsets that triggered this:
                                    root_words_for_matches = [p1_word,p2_word]
                                    closest_match_synset_pair = [p1_word_synset,p2_word_synset]
                            except KeyError as ex:
                                raise WordNetError(f'{current_result["message"]}, Error: {str(ex)}')

            # TODO: use 'data_summary' to include or exclude complexity here:
            print(closest_match_synset_pair)
            if closest_match_synset_pair:
                result['calculated_similarity'] = max_similarity
                result['synsets'] = [
                    {
                        'synset': self.get_synset_by_name( closest_match_synset_pair[0].name(), False),
                        'root_word':root_words_for_matches[0]
                    },
                    {
                        'synset': self.get_synset_by_name(closest_match_synset_pair[1].name(), False),
                        'root_word':root_words_for_matches[1]
                    }]

            else:
                result['message'] = 'Comparison list is empty. Please check the pre-processed words for being actual words... Stemming may be inappropriate'
                result['status'] = 'error'

        except WordNetError as err:
            result['status'] = 'error'
            result['message'] = str(err)
        except IndexError as err:
            result['status'] = 'error'
            result['message'] = str(err)
        except KeyError as err:
            result['status'] = 'error'
            result['message'] = str(err)

        return result

    def phrase_similarity_cosine(self,p1, p2):
        '''
        determine phrase similarity by the 'cosine' method.
        See, e.g.: https://newscatcherapi.com/blog/ultimate-guide-to-text-similarity-with-python
        '''
        # print('procesing cosine...')
        result = {'status':'ok','message':'ok','method':'cosine'}
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform([p1,p2])
        similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
        # https://spacy.io/
        # headlines = [p1,p2] # need strings here TODO:
        #
        # # this is generic and will generate an arbitrary matrix of phrases, but...
        # docs = [WordnetAPI.nlp(headline) for headline in headlines]
        # print(docs[0].vector)
        # # 'docs' is a list of length 2 as we are always only passing two phrases, so:
        # similarity = docs[0].similarity([docs[1]])
        result['calculated_similarity'] = similarity

        return result

        # # MARIUSZ TESTS
        # # Define the text
        # # text1 = "board games"
        # # text2 = "consol games"
        # # text1 = p1
        # # text2 = p2
        #
        # # text = [text1, text2]
        #
        # # Convert the text to tf-idf vectors
        # tfidf_vectorizer = TfidfVectorizer()
        # tfidf_matrix = tfidf_vectorizer.fit_transform([p1,p2])
        #
        # # Apply k-means clustering to the tf-idf vectors
        # kmeans = KMeans(n_clusters=2, random_state=0)
        # kmeans.fit(tfidf_matrix)
        #
        # # Determine the cluster assignments for the text
        # clusters = kmeans.predict(tfidf_matrix)
        #
        # # Compare the cluster assignments for the two pieces of text
        # print(clusters[0] == clusters[1])
        #
        # # Compare the similarity of the two pieces of text using cosine similarity
        # similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])
        # print(similarity[0][0])
        #
        # return {'status':'ok','method':'cosine_similarity','similarity' : similarity[0][0]}

    def phrase_similarity_count(self,p1,p2):
        result = {'status':'ok','message':'ok','method':'ocunt'}
        vect = CountVectorizer().fit_transform([p1, p2])
        sim = cosine_similarity(vect[0], vect[1])[0][0]
        result['calculated_similarity'] = sim
        return result

    def phrase_similarity_tf(self,p1,p2):
        """This function download pretrained model from tensorflow_hub and turn text into vector then 
        calculate similarity of both phrases.
        Note: that it is a number between -1 and 1. When it is a negative number between -1 and 0, 
        0 indicates orthogonality and values closer to -1 indicate greater similarity. 
        The values closer to 1 indicate greater dissimilarity. This makes it usable as a loss function 
        in a setting where you try to maximize the proximity between predictions and targets. 
        If either y_true or y_pred is a zero vector, cosine similarity will be 0 regardless of the 
        proximity between predictions and targets."""
        result = {'status':'ok','message':'ok','method':'tensorflow'}
        
        # done up front
        embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")   #do this up front!
        # phrase1_embedding = self.embed([p1])
        # phrase2_embedding = self.embed([p2])
        phrase1_embedding = embed([p1])
        phrase2_embedding = embed([p2])
        similarity = tf.keras.losses.CosineSimilarity()(phrase1_embedding, phrase2_embedding)
        result['calculated_similarity'] = np.float64(similarity.numpy())
        return result

    def phrase_similarity_rb(self,p1,p2):
        """  """
        result = {'status':'ok','message':'ok','method':'roberta'}
        
        # done up front??
        # Initialize the model
        model = SentenceTransformer('stsb-roberta-large')
        
        # encode sentences to get their embeddings
        emb1 = model.encode(p1, convert_to_tensor=True)
        emb2 = model.encode(p2, convert_to_tensor=True)
        
        # compute similarity scores of two embeddings with Pytorch library
        cosine_score = util.pytorch_cos_sim(emb1, emb2)
        print(cosine_score)
        print(cosine_score.numpy())
        print(cosine_score.numpy()[0][0])
        print(type(cosine_score.numpy()[0][0]))
        print(np.float64(cosine_score.numpy()[0][0]))
        result['calculated_similarity'] = np.float64(cosine_score.numpy()[0][0])
        
        # may need to do this:
        # result['calculated_similarity'] = np.float64(cosine_score)
        
        
        # return cosine_score.item()
        # result['calculated_similarity'] = np.float64(similarity.numpy())
        return result

