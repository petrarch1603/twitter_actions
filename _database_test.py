import Database
import datetime
import twitter_activities

test_act_db = Database.ActionDB(testing=1)
test_req_db = Database.RequestDB(testing=1)
# sample_a_dict = {'row_date': datetime.datetime.now(),
#                  'link': 'http:sample_a.like.com',
#                  'directive': 'like',
#                  'testing': 1}
#
# sample_b_dict = {'row_date': datetime.datetime.now(),
#                  'link': 'http:sample_b.comment',
#                  'directive': 'comment',
#                  'text': 'I am comment_text_var',
#                  'testing': 1}
#
# sample_c_dict = {'row_date': datetime.datetime.now(),
#                  'link': 'http:sample_c.retweet',
#                  'directive': 'retweet',
#                  'testing': 1}
#
# my_dicts_list = [Database.ActionRow(sample_a_dict),
#                  Database.ActionRow(sample_b_dict),
#                  Database.ActionRow(sample_c_dict)]
# #
# # x = my_dicts_list[0]
#
# for i in my_dicts_list:
#     test_act_db.add_to_db(row_obj=i)



test_act_db.execute_actions()

test_act_db = Database.ActionDB(testing=1)
for i in test_act_db.all_rows_list():
    print(i.executed)
