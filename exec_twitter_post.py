import Database
import twitter_activities

my_ht = '#mappornrequest'

twitter_activities.process_requests(hashtag=my_ht)

act_db = Database.ActionDB(testing=0).execute_actions()

