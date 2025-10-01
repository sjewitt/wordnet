'''
Module to run the Wordnet REST API Server
'''
import os
import argparse
import cherrypy
from libs.wordnet_api import WordnetAPI
from libs.wordnet_rest_api import WordnetREST
from libs.wordnet_ui import UserInterface

parser = argparse.ArgumentParser(description='Start Wordnet API wrapper')
parser.add_argument('-i','--ipAddress', help='ip address of server [string]', required=True)
parser.add_argument( '-p', '--port', help='port number server [int]', required=True)
# database name (default to 'comparison.db')
parser.add_argument("-n", "--database_name", help="name of SQLite database to use (default=comparison.db)", type=str, required=False, default='comparison.db')

args = parser.parse_args()

# api = WordnetREST()
wn = WordnetAPI(args.database_name)

def main():
    '''
    Startup function
    '''
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static' : {
            'tools.staticdir.on'    : True,
            'tools.staticdir.dir'   : 'static',
            # 'tools.staticdir.index' : 'index.html',
            'tools.gzip.on'         : True
        }
    }

    cherrypy.config.update({
        'server.socket_host': args.ipAddress,
        'server.socket_port': int(args.port)
    })
    
    # REST API root
    cherrypy.tree.mount(WordnetREST(wn),'/api/',conf)

    # UI root
    cherrypy.tree.mount(UserInterface(),'/',conf)

    
    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == '__main__':
    main()
