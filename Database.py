import datetime
import my_helper
import my_secrets
import pymysql
import schema
import time
import twitter_activities

database_path = 'data/twitter_interactions.db'

actions_schema = schema.twitter_actions


def connect_to_req_db(testing=0):
    return RequestDB(testing=testing)


def connect_to_act_db(testing=0):
    return ActionDB(testing=testing)


class _SuperRow:
    def __init__(self, raw_dict, my_schema, table, database):
        self.database = database
        self.schema = my_schema
        self.raw_dict = raw_dict
        self.table = table
        self.link = raw_dict['link']
        self.row_date = raw_dict['row_date']
        if 'unique_id' in raw_dict.keys():
            self.unique_id = str(raw_dict['unique_id'])
        else:
            self.unique_id = str(my_helper.get_unique_id())
        if 'text' in raw_dict.keys():
            self.text = raw_dict['text']
        else:
            self.text = ''

        if 'testing' in raw_dict.keys():
            self.testing = raw_dict['testing']
        else:
            self.testing = 0
        if '_json' in raw_dict.keys():
            self._json = str(raw_dict['_json'])
        else:
            self._json = ''

    def get_dict(self):
        my_dict = {}
        for i in self.schema:
            my_dict[i] = getattr(self, i)
        return my_dict


class RequestRow(_SuperRow):
    def __init__(self, request_dict, request_database=database_path):
        _SuperRow.__init__(self,
                           raw_dict=request_dict,
                           my_schema=schema.twitter_requests.keys(),
                           table='requests',
                           database=request_database)
        if 'responded' in request_dict.keys():
            self.responded = request_dict['responded']
        else:
            self.responded = 0


class ActionRow(_SuperRow):
    def __init__(self, action_dict, action_database=database_path):
        _SuperRow.__init__(self,
                           raw_dict=action_dict,
                           my_schema=schema.twitter_actions.keys(),
                           table='actions',
                           database=action_database)
        self.directive = action_dict['directive']
        if 'executed' in action_dict.keys():
            self.executed = action_dict['executed']
        else:
            self.executed = 0
        if 'action_time_zone' in action_dict.keys():
            self.time_zone = action_dict['time_zone']
        else:
            self.time_zone = my_helper.get_time_zone()
        if self.directive == 'comment':
            assert self.text != ''
        assert len(self.unique_id) > 0

    def post_to_twitter(self):
        self.executed = 1
        if self.testing == 1:
            return "Sub-test Complete"
        if self.directive == 'comment':
            return twitter_activities.CommentActivity(action_row_obj=self).status
        if self.directive == 'retweet':
            return twitter_activities.RetweetActivity(action_row_obj=self).status
        if self.directive == 'like':
            return twitter_activities.LikeActivity(action_row_obj=self).status
        self.executed = 0
        print(f"Error detected in posting to twitter (Database.py)\n Directive is: {self.directive}")


class _SuperDB:
    def __init__(self, table, path, row_class, testing):
        self.table = table
        self.path = path
        self.row_class = row_class
        self.testing = testing
        self.conn = self.connect_to_db()
        self.curs = self.conn.cursor(pymysql.cursors.DictCursor)
        print(f"Connected to Database. Version: {pymysql.__version__}")

    @staticmethod
    def connect_to_db():
        return pymysql.connect(host=my_secrets.database_host(),
                               user=my_secrets.database_user(),
                               password=my_secrets.database_pw(),
                               database=my_secrets.database_name())

    def all_rows_list(self):
        self.curs.execute("SELECT * FROM {}".format(self.table))
        return self._get_row_list(self.curs.fetchall())

    def _get_row_list(self, fetchall_list):
        my_rows = []
        for i in fetchall_list:
            my_rows.append(self.row_class(i))
        return my_rows

    def check_if_in_db(self, unique_id_str):
        q = self.curs.execute("SELECT * FROM {} WHERE unique_id = {}".format(self.table, str(unique_id_str)))
        if q > 0:
            print(f"{unique_id_str} already in database")
            return True
        else:
            return False

    def add_to_db(self, row_dict):
        if self.check_if_in_db(unique_id_str=row_dict['unique_id']):
            return print("Already in DB")
        keys = ','.join(row_dict.keys())
        question_marks = ','.join(list(['%s']*len(row_dict)))
        values = tuple(row_dict.values())
        self.curs.execute('INSERT INTO '+self.table+' ('+keys+') VALUES ('+question_marks+')', values)
        self.conn.commit()


class ActionDB(_SuperDB):
    def __init__(self, table='actions', path=database_path, testing=0):
        _SuperDB.__init__(self, table, path, row_class=ActionRow, testing=testing)
        self.current_gmt_hour = time.gmtime().tm_hour
        self.schema = schema.twitter_actions
        self.subtract_days = 2

    def __len__(self):
        my_query = self.curs.execute(f"SELECT count(*) FROM {self.table} WHERE testing = {self.testing}")
        return my_query.fetchall()[0][0]

    def complete_unexecuted_list(self):
        self.curs.execute(f"SELECT * FROM {self.table} WHERE executed = 0 "
                          f"AND testing = {self.testing}")
        return self._get_row_list(self.curs.fetchall())

    def _selected_unexecuted(self):
        # TODO: clean up this function and get it to work
        # LOW PRIORITY
        # if 2 > self.current_gmt_hour > 8:
        #     rows_list = (self.curs.execute(f"SELECT * FROM {self.table} WHERE executed = 0 "
        #                                                f"AND testing = {self.testing}"
        #                                                f"AND time_zone BETWEEN 0 and 3")).fetchall()
        #
        # else:
        #     rows_list = [x for x in (self.curs.execute(f"SELECT * FROM {self.table} WHERE executed = 0 "
        #                                                f"AND testing = {self.testing} "
        #                                                f"AND time_zone NOT BETWEEN 0 and 3"))]
        raw_list = self.complete_unexecuted_list()
        if len(raw_list) > 100:
            split_date = datetime.datetime.now() - datetime.timedelta(days=self.subtract_days)
            self.curs.execute(f"SELECT * FROM {self.table} WHERE row_date > {split_date.strftime('%Y-%m-%d')} "
                              f"AND testing = {self.testing} and EXECUTED = 0")
            # turn into row objects
            results_list = self._get_row_list(self.curs.fetchall())  # Turn into row objects
        else:
            results_list = raw_list
        print(f"Number of Unexecuted Actions in pool: {len(results_list)}")
        count_limit = int(len(results_list) / 15)  # This is limits the number of activities to execute
        print(f"Executing 25% of Actions: {count_limit}")
        results_list.sort(key=lambda r: r.row_date)  # Sort oldest to newest

        return results_list[:count_limit]

    def _update_row_to_executed(self, unique_id):
        self.curs.execute(f"UPDATE {self.table} SET executed = 1 WHERE unique_id = {str(unique_id)}")
        self.conn.commit()

    def execute_actions(self):
        for row in self._selected_unexecuted():
            # Optional: print status bar
            row.post_to_twitter()
            try:
                assert row.executed == 1
            except AssertionError:
                print(f"Row Unique ID: {row.unique_id}")
            self._update_row_to_executed(unique_id=row.unique_id)
        # self.__init__(testing=self.testing)


class RequestDB(_SuperDB):
    def __init__(self, table='requests', path=database_path, testing=0):
        _SuperDB.__init__(self, table=table, path=path, row_class=RequestRow, testing=testing)
        self.schema = schema.twitter_requests

    def update_row_to_responded(self, unique_id):
        print(unique_id)
        self.curs.execute(f"UPDATE {self.table} SET responded = 1 WHERE unique_id = {str(unique_id)}")
        self.conn.commit()

    def get_unresponded_list(self):
        self.curs.execute(f"SELECT * FROM {self.table} WHERE responded = 0 "
                          f"AND testing = {self.testing}")
        return self._get_row_list(self.curs.fetchall())
