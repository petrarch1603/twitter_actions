import Database
import twitter_activities

my_ht = '#villarica'

twitter_activities.process_requests(hashtag=my_ht, testing=1, count=10)

twitter_activities.respond_to_requests(count=5, testing=1)

act_db = Database.ActionDB(testing=1)

act_db.execute_actions()
