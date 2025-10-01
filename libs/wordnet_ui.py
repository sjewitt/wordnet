'''
Created on 17 Jan 2023

@author: silasj@grange.taxonomics.co.uk
'''
import cherrypy
from mako.lookup import TemplateLookup
lookup = TemplateLookup(directories=['templates'], output_encoding='utf-8', encoding_errors='replace')

class UserInterface(object):
    '''
    class to expose UI endpoints and corresponding Mako templates. Functionality on temp[lates is JS/AJAX driven
    '''


    def __init__(self):
        '''
        Constructor
        '''

    @cherrypy.expose
    def index(self):
        return(self.renderIt("index.html"))
    
    @cherrypy.expose
    def synsets(self,**kwargs):
        return(self.renderIt("synsets.html",None,kwargs))
    
    @cherrypy.expose
    def synset_similarity(self,**kwargs):
        return(self.renderIt("synset_similarity.html",None,kwargs))
    
    @cherrypy.expose
    def phrase_compare(self):
        return(self.renderIt("phrase_compare.html"))

    @cherrypy.expose
    def get_related_phrases(self):
        return(self.renderIt("get_related_phrases.html"))
    
    #Utility class to display the given template:
    def renderIt(self,template,path=None,kwargs=None):
        tmpl = lookup.get_template(template)
        
        return tmpl.render(mappath=path,args=kwargs)