'''
Created on 6 Feb 2023

@author: silasj@grange.taxonomics.co.uk
'''
import os
import sqlite3

class Database(object):
    '''
    Utilities to open, execute and close a SQLite DB and query
    NOTE: Queryvars is a List(), even if length 1
    (lifted from SQLite Scrappy)
    '''

    FETCH_ALL = 1
    FETCH_ONE = 2

    def __init__(self, db_name='comparison.db'):
        '''
        check for and create database file
        '''
        path = os.path.abspath(os.getcwd())
        if not os.path.isdir(path + '/database/'):
            print('Creating database directory path...')
            os.makedirs(path + '/database/')
        # self.dbname = path + '/database/' + db_name
        self.dbname = f'{path}/database/{db_name}'
        create_jobs_sql = "CREATE TABLE if not exists JOBS (job_uuid TEXT NOT NULL UNIQUE, comparison_type TEXT NOT NULL, INPUT_FILE_1 TEXT NOT NULL, INPUT_FILE_2  TEXT NOT NULL, PROCESSOR TEXT NOT NULL DEFAULT 'unknown', PRIMARY KEY('job_uuid'))"
        create_comparisons_sql = 'CREATE TABLE if not exists COMPARISONS (id INTEGER NOT NULL UNIQUE, JOB_UUID TEXT NOT NULL, COMPARISON_SCORE NUMERIC, TERM_1 TEXT, DESCRIPTION_1 TEXT, TERM_2 TEXT, DESCRIPTION_2 TEXT, PRIMARY KEY("id" AUTOINCREMENT))'
        
        # Check if database exists in /database/ directory - if not, create new database with name [dbname]
        # TODO: need to ensure consistency as per Scrappy (tables updating, missing tables etc.)
        # if not os.path.isfile(self.dbname):
        #     print('Database does not exist in database path')
        #     print('Creating new database {}...'.format(self.dbname))
        #
        #     conn = sqlite3.connect(self.dbname)
        #     c = conn.cursor()
        #     print('Creating tables...')
        #     c.execute(create_jobs_sql)
        #     c.execute(create_comparisons_sql)
        # else:
        #     # If database exists, simply establish connection and create cursor
        #     conn = sqlite3.connect(self.dbname)
        #     c = conn.cursor()
        
        conn = sqlite3.connect(self.dbname)
        c = conn.cursor()
        print('Creating tables...')
        result = c.execute(create_jobs_sql)
        result = c.execute(create_comparisons_sql)
        
        

    def executeUpdateSql(self, sql, queryvars=None,_ok_msg='update successful'):
        try:
            conn = sqlite3.connect(self.dbname)
            c = conn.cursor()
            c.execute(sql,queryvars)
            conn.commit()
            conn.close()
            return({'status':'ok','message':_ok_msg})
        except sqlite3.Error as err:
            conn.close()
            return({'status':'error','message':'update, Sqlite3: '+str(err)})
        except Exception as err:
            conn.close()
            return({'status':'error','message':'update, Other: '+str(err)})

    def executeInsertSql(self, sql, queryvars=None,_ok_msg='insert successful'):
        try:
            conn = sqlite3.connect(self.dbname)
            c = conn.cursor()
            c.execute(sql,queryvars)
            conn.commit()
            conn.close()
            return({'status':'ok','message':_ok_msg})
        except sqlite3.Error as err:
            conn.close()
            return({'status':'error','message':'insert, Sqlite3: '+str(err)})
        except Exception as err:
            conn.close()
            return({'status':'error','message':'insert, Other: '+str(err)})

    def executeSelectSql(self, sql, queryvars=None, fetchAction=FETCH_ALL):
        try:
            conn = sqlite3.connect(self.dbname)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            if queryvars:
                res = c.execute(sql, queryvars)
            else:
                res = c.execute(sql)

            if fetchAction == Database.FETCH_ALL:
                results = [dict(row) for row in res.fetchall()]
            elif fetchAction == Database.FETCH_ONE:
                results = res.fetchone()
                if results:
                    results = dict(results)
            conn.close()
            return(results)
        except sqlite3.Error as err:
            conn.close()
            return({'status':'error','message':'select, Sqlite3: '+str(err)})

        except Exception as err:
            conn.close()
            return({'status':'error','message':'select, Other: '+str(err)})

    def executeDeleteSql(self, sql, queryvars=None):
        try:
            conn = sqlite3.connect(self.dbname)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            if queryvars:
                res = c.execute(sql, queryvars)
            else:
                res = c.execute(sql)
            conn.commit()
            conn.close()
            return({'status':'ok','message': 'deletion performed OK' })
        except sqlite3.Error as err:
            conn.close()
            return({'status':'error','message':'update, Sqlite3: '+str(err)})

        except Exception as err:
            conn.close()
            return({'status':'error','message':'update, Other: '+str(err)})

    def get_jobs(self):
        # sql = 'select job_uuid, comparison_type, input_file_1, input_file_2, processor from JOBS'
        sql = ' '.join([
            'select j.job_uuid, j.comparison_type, j.input_file_1, j.input_file_2, j.processor,',
            '(select max(c.COMPARISON_SCORE) as max from COMPARISONS c where c.job_uuid=j.job_uuid ) as max,',
            '(select min(c.COMPARISON_SCORE) as min from COMPARISONS c where c.job_uuid=j.job_uuid ) as min',
            'from jobs j'
            ])
        # make fieldnames lowercase:
        result = self.executeSelectSql(sql, None, Database.FETCH_ALL) 
        # https://stackoverflow.com/questions/55701139/how-to-convert-the-dictionary-values-to-lower-case-in-list-comprehension
        # result = [{k.lower():v for k,v in d.items()} for d in result]
        # return self.executeSelectSql(sql, None, Database.FETCH_ALL) 
        return [{k.lower():v for k,v in d.items()} for d in result]

    def add_job_row(self,job_uuid, comparison_type,file_1, file_2, processor='unknown'):
        sql = 'insert into JOBS (job_uuid, comparison_type, input_file_1, input_file_2, processor) values (?, ?, ?, ?, ?)' 
        return self.executeInsertSql(sql, (job_uuid,comparison_type,file_1, file_2, processor), 'job added to jobs table') 

    def add_comparison_row(self,job_uuid,comparison_score,term_1,description_1,term_2,description_2):
        sql = 'insert into comparisons (job_uuid, comparison_score, term_1, description_1, term_2, description_2) values (?, ?, ?, ?, ?, ?)'
        return self.executeInsertSql(sql, (job_uuid,comparison_score,term_1,description_1,term_2,description_2), 'comparison row inserted') 

    def get_similar_terms(self,job_uuid,term,similarity_threshold,comparison_type):
        # SEE https://stackoverflow.com/questions/973541/how-to-set-sqlite3-to-be-case-insensitive-when-string-comparing
        ''' do query to test for TERM in both fields: '''
        if comparison_type=='tf':
            # SQL needs to select < and sort ASC
            query = "select * from COMPARISONS where job_uuid=? and comparison_score < ? and (term_1=? COLLATE NOCASE or term_2=? COLLATE NOCASE) order by comparison_score asc"
        else:
            query = "select * from COMPARISONS where job_uuid=? and comparison_score > ? and (term_1=? COLLATE NOCASE or term_2=? COLLATE NOCASE) order by comparison_score desc"
        result = self.executeSelectSql(query, (job_uuid, similarity_threshold, term, term), Database.FETCH_ALL)
        return result
    
    def get_comparison_range(self,job_uuid):
        if job_uuid:
            query = "select max(COMPARISON_SCORE) as max, min(COMPARISON_SCORE) as min from COMPARISONS where job_uuid=?"
            result = self.executeSelectSql(query, (job_uuid, ), Database.FETCH_ONE)
            return result
        return {'status':'warning','message':'no job_uuid supplied'}
    
    def get_filtered_terms(self,job_uuid, term,similarity_threshold):
        query = "select * from comparisons where job_uuid=? and comparison_score > ? and (term_1 like ? COLLATE NOCASE or term_2 like ? COLLATE NOCASE)"
        term = f'%{term}%'
        result = self.executeSelectSql(query, (job_uuid ,similarity_threshold, f'%{term}%', f'%{term}%'), Database.FETCH_ALL)
        return result
        
        
        
    
