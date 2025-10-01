''' REST wrapper for simple Wordnet API '''

import cherrypy

class WordnetREST:

    def __init__(self,WordnetAPI):
        self.WordnetAPI = WordnetAPI
        print('init')

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        return({'status':'ok','message':'Wordnet API root'})

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def synsets(self,**kwargs):
        ''' return synsets and first level parent hypernyms (more general term) and first level child hyponyms (more specific). see https://www.nltk.org/howto/WordnetAPI.html#synsets '''
        print('synset')
        if kwargs.get('word',None):
            return self.WordnetAPI.get_synsets(kwargs.get('word',None))
        elif kwargs.get('synset_name',None):
            return self.WordnetAPI.get_synset_by_name(kwargs.get('synset_name',None))


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def synset(self,**kwargs):
        ''' return synset and first level parent hypernyms (more general term) and first level child hyponyms (more specific). see https://www.nltk.org/howto/WordnetAPI.html#synsets '''
        print('get synset by name')
        if kwargs.get('synset_name',None):
            if kwargs.get('summary',False):
                return self.WordnetAPI.get_synset_by_name(kwargs.get('synset_name',None), False)
            return self.WordnetAPI.get_synset_by_name(kwargs.get('synset_name',None))
        return {'status':'ok','message':'please supply synset name'}



    @cherrypy.expose
    @cherrypy.tools.json_out()
    def synset_count(self,**kwargs):
        ''' return synset count for supplied root word.  see https://www.nltk.org/howto/WordnetAPI.html#synsets '''
        return self.WordnetAPI.get_synset_count(kwargs.get('word',None))
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def synsets_pair_summary(self,**kwargs):
        ''' extract a summary of synsets for a pair of words. Used for the synset compare page to generate the initial
        list of synsets to actually compare '''
        word1 = kwargs.get('word1',False)
        word2 = kwargs.get('word2',False)
        if word1 and word2:
            synset1 = self.WordnetAPI.get_synsets(word1,False)
            synset2 = self.WordnetAPI.get_synsets(word2,False)
            return {'status':'ok', 'synset1':synset1,'synset2':synset2}
        return {'status':'warning','message':'please provide both words'}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def synset_similarity(self,**kwargs):
        ''' compare two synsets for similarity by one of three methods (Path, Leacock-Chodorow, Wu-Palmer). See  https://www.nltk.org/howto/WordnetAPI.html#similarity '''
        word1 = kwargs.get('word1',False)
        word2 = kwargs.get('word2',False)
        comp_type = kwargs.get('comparison_type','path')
        if not comp_type in ['path','wup','lch']:
            comp_type='wup'    #default
        if word1 and word2:
            # assume index zero?
            # also TODO: catch duplicated params errors!
            index1 = int(kwargs.get('index1',0))
            index2 = int(kwargs.get('index2',0))
            return self.WordnetAPI.compare((word1,index1),(word2,index2),comp_type)
        return []
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def synset_similarity_by_name(self,**kwargs):
        ''' compare two synsets for similarity by one of three methods (Path, Leacock-Chodorow, Wu-Palmer). See  https://www.nltk.org/howto/WordnetAPI.html#similarity '''
        s1 = kwargs.get('synset1',False)
        s2 = kwargs.get('synset2',False)
        comp_type = kwargs.get('comparison_type','path')
        if not comp_type in ['path','wup','lch']:
            comp_type='wup'    #default
        if s1 and s2:

            return self.WordnetAPI.compare_by_name(s1,s2,comp_type)
        return []
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def word_stem(self,**kwargs):
        ''' stem a word (may be a case for adding a POST option here to allow multiple words in one go).
        THIS NEEDS TESTING PROPERLY! The example given in the above ref includes 'flies' which is stemmed to 'fli' - which is wrong...
        'porter'                                        -> 'po'
        'snowball_porter'                               -> 'sp'
        'snowball_english' <-- defaulting to this one   -> 'se'
        see https://www.nltk.org/howto/stem.html.
        '''
        word = kwargs.get('word',None)
        stemmer = kwargs.get('stemmer','se')
        return self.WordnetAPI.stem(word, stemmer)
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def is_stop_word(self,**kwargs):
        ''' test a word for being a stopword, in the NLTK corpus
        see https://pythonspot.com/nltk-stop-words/ '''
        word = kwargs.get('word',None)
        return self.WordnetAPI.is_stopword(word)
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_processed_list(self,**kwargs):
        ''' 
        word = list of words to process 
        remove_stopwords = strip out any stopwords found in supplied list when matched against the NLTK stopword list
        stem = retrieve the word stem
        stemmer = using this stem method
        '''
        # words=[],remove_stopwords=True,perform_stem=True,stemmer='se'
        # https://builtin.com/data-science/python-conditional-statement
        # true_expression if conditional else false_expression
        words = kwargs.get('words',[]).split(',') if kwargs.get('words',False) else [] 
        remove_stopwords = False if kwargs.get('remove_stopwords',True)=='false' else True #remove stopwords unless we say otherwise 
        perform_stem = False if kwargs.get('perform_stem',True) == 'false' else True       #perform stemming unless we say otherwise 
        stemmer = kwargs.get('stemmer','se')
        return self.WordnetAPI.get_processed_list(words,remove_stopwords,perform_stem,stemmer)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def phrase_similarity(self,**kwargs):
        ''' pairwise comparison of words in phrases.
        Keep track of highest comparison - probably also need to
        keep track of POS? There is a risk that non-stopword, but
        common between phrases will overwhelm the relationship
        score erroneously. EDIT: Discussion with Liam indicates
        that is OK '''
        phrase_comparison_type = kwargs.get('phrase_ct','pairwise') #adding cosine (see https://newscatcherapi.com/blog/ultimate-guide-to-text-similarity-with-python)
        data_summary = False
        if kwargs.get('summary','false') == 'true':
            data_summary = True
            
        p1 = kwargs.get('p1','')
        p2 = kwargs.get('p2','')
        if phrase_comparison_type == 'pw':
            p1 = p1.split(' ')
            p2 = p2.split(' ')
        # to account for possible refinement of phrase comparison later on
        
        word_comparison_type=kwargs.get('word_ct','wup')
        return self.WordnetAPI.phrase_similarity(p1, p2, data_summary, phrase_comparison_type, word_comparison_type)
        

    # relationship tests
    # These look for direct relationships, but see https://www.nltk.org/api/nltk.corpus.reader.wordnet.html 
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def is_hyponym_of(self,**kwargs):
        s1 = kwargs.get('test_synset',False)
        s2 = kwargs.get('root_synset',False)
        if s1 and s2:
            # does s1 exist as a direct hyponym of s2?
            return {
                'synset_to_test':s1,
                'test':'is_hyponym_of',
                'root_synset':s2,
                'result':self.WordnetAPI.test_relationship('hyponyms',s1, s2)}
        return {'status':'warning', 'message':'please supply both synset names'}
            
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def is_hypernym_of(self,**kwargs):
        s1 = kwargs.get('test_synset',False)
        s2 = kwargs.get('root_synset',False)
        if s1 and s2:
            # does s1 exist as a direct hypernym of s2?
            return {
                'synset_to_test':s1,
                'test':'is_hypernym_of',
                'root_synset':s2,
                'result':self.WordnetAPI.test_relationship('hypernyms',s1, s2)}
        return {'status':'warning', 'message':'please supply both synset names'}
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def is_meronym_of(self,**kwargs):
        s1 = kwargs.get('test_synset',False)
        s2 = kwargs.get('root_synset',False)
        if s1 and s2:
            # does s1 exist as a direct meronym of s2?
            return {
                'synset_to_test':s1,
                'test':'is_meronym_of',
                'root_synset':s2,
                'result':self.WordnetAPI.test_relationship('meronyms',s1, s2)}
        return {'status':'warning', 'message':'please supply both synset names'}
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def is_holonym_of(self,**kwargs):
        s1 = kwargs.get('test_synset',False)
        s2 = kwargs.get('root_synset',False)
        if s1 and s2:
            # does s1 exist as a direct holonym of s2?
            return {
                'synset_to_test':s1,
                'test':'is_holonym_of',
                'root_synset':s2,
                'result':self.WordnetAPI.test_relationship('holonyms',s1, s2)}
        return {'status':'warning', 'message':'please supply both synset names'}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_jobs(self): # TODO: will paginate eventually
        # HACKY! to account for BLOB data not being serialisable (due to the float32 vs float64 thing)
        
        # a comprehension ideally...
        raw_result = self.WordnetAPI.get_jobs()   #a database call, nay include BLOBs in comparison_score
        for job in raw_result:
            print(str(type(job['max'])))
            if isinstance(job['max'],bytes):
                job['max']=None
            if isinstance(job['min'],bytes):
                job['min']=None
        return raw_result
    
    # test of database retrieval of calculated similar things:
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_similar_terms(self, **kwargs):
        job_uuid = kwargs.get('job_uuid',None)
        term = kwargs.get('term',None)
        similarity_threshold = kwargs.get('limit',0)
        comparison_type = kwargs.get('comparison_type','pw')   #may want to decide on the default here...
        return_val = self.WordnetAPI.get_similar_terms(job_uuid,term,similarity_threshold,comparison_type)
        return return_val
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_comparison_range(self,**kwargs):
        ''' return a comparison range for the selected job '''
        job_uuid = kwargs.get('job_uuid',None)
        return self.WordnetAPI.get_comparison_range(job_uuid)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_filtered_terms(self, **kwargs):
        job_uuid = kwargs.get('job_uuid',None)
        term = kwargs.get('term',None)
        similarity_threshold = kwargs.get('limit',0)
        raw_response = self.WordnetAPI.get_filtered_terms(job_uuid,term,similarity_threshold)
        return_val = {'raw_response':raw_response}
        return_val['length'] = len(raw_response)
        if len(raw_response) > 2000000: #TEST!!
            return_val['status'] = 'warning'
            return_val['message'] = 'filtered length exceeds 50 items'
        else:
            res = list()
            # this loop will never be more than 50 Need to lowercase these
            for entry in raw_response:
                if term.lower() in entry['TERM_1'].lower() and not entry['TERM_1'] in res:
                    res.append(entry['TERM_1'])
                if term.lower() in entry['TERM_2'].lower() and not entry['TERM_2'] in res:
                    res.append(entry['TERM_2'])
            return_val['filtered'] = res
            return_val['status'] = 'ok'
            return_val['message'] = 'ok'
            # https://stackoverflow.com/questions/7271482/getting-a-list-of-values-from-a-list-of-dicts
            # return_val['filtered'] = []
        # need to construct a list of terms for jquery to use:
        
        return return_val 
    
    
    # utilities (from treecreeper)
    def getdefault(self,_req):
        if hasattr(_req,'json'):
            return(_req.json)
        return({})
    
