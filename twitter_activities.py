import Database
import my_helper
import my_secrets
import pprint
import re
import schema
import time
import tweepy


def api_init():
    auth = tweepy.OAuthHandler(my_secrets.consumer_key(), my_secrets.consumer_secret())
    auth.set_access_token(my_secrets.access_token(), my_secrets.access_secret())
    return tweepy.API(auth)

# These objects post to Twitter as soon as they are instantiated. They return a Tweepy
# status object in self.status


class _ProtoActivity:
    def __init__(self, action_row_obj):
        self.link = action_row_obj.link
        self.directive = action_row_obj.directive
        self.text = action_row_obj.text
        self.id = re.search('(?<=status/)(.*)$', self.link)[0]
        self.author = re.search('(?<=.com/).*(?=/status)', self.link)[0]
        self.api = my_helper.api_init()
        if self.remaining_twitter_calls() < 60:
            time.sleep(15)
        assert self.remaining_twitter_calls() > 5

    def remaining_twitter_calls(self):
        return my_helper.get_remaining(self.api)


class CommentActivity(_ProtoActivity):
    def __init__(self, action_row_obj):
        _ProtoActivity.__init__(self, action_row_obj)
        self.status = self._comment()

    def _comment(self):
        try:
            if self.author.lower() == 'mapporntweet':

                tweet = self.api.update_status(status=self.text,
                                               in_reply_to_status_id=self.id)
                print(f"Made comment: \n{self.text}"
                      f"in reply to https://twitter.com/MapPornTweet/status/{self.id}")
                return tweet
            else:
                tweet = self.api.update_status(status=self.text + ' @' + self.author,
                                               in_reply_to_status_id=self.id)
                print(f"Made comment: \n{self.text}"
                      f"in reply to https://twitter.com/{self.author}/status/{self.id}")
                return tweet

        except Exception as e:
            print(f"Error encountered in comment status: {e}\n\n\n")
            print(f"Exception Arguments: {Exception.args}")


class LikeActivity(_ProtoActivity):

    def __init__(self, action_row_obj):
        _ProtoActivity.__init__(self, action_row_obj)
        self.status = self._like()

    def _like(self):
        print(f"Like Activity")
        try:
            tweet = self.api.create_favorite(id=self.id)
            print(f"Liked url: https://twitter.com/{self.author}/status/{str(self.id)}")
            return tweet
        except Exception as e:
            print(f"Error encountered in liking status: {e}\n\n\n")
            print(f"Exception Arguments: {Exception.args}")


class RetweetActivity(_ProtoActivity):

    def __init__(self, action_row_obj):
        _ProtoActivity.__init__(self, action_row_obj)
        self.status = self._retweet()

    def _retweet(self):
        try:

            retweet = self.api.retweet(id=self.id)
            print(f"Retweeted https://twitter.com/{retweet.user.screen_name}/status/{retweet.id_str}")
            return retweet
        except Exception as e:
            print(f"Error encountered in liking status: {e}\n\n\n")
            print(f"Exception Arguments: {Exception.args}")


class MapRequest:
    # Get the tweet.
    # Parse it into a dictionary that can be passed on to the database

    def __init__(self, tweepy_status_obj, testing=0):
        self.schema = schema.twitter_requests.keys()
        self.tweepy_status_obj = tweepy_status_obj
        self.unique_id = self.tweepy_status_obj.id

        self.row_date = self.tweepy_status_obj.created_at.date().isoformat()  # This format is necessary for MySQL
        print(self.row_date)
        self.text = self.tweepy_status_obj.text
        self.link = f"https://twitter.com/{tweepy_status_obj.user.screen_name}/status/{self.unique_id}"
        self._json = self.tweepy_status_obj._json
        self.testing = testing

    def _get_dict(self):
        my_dict = {}
        for i in self.schema:
            try:
                my_dict[i] = getattr(self, i)
            except AttributeError:  # Some key, value pairs will not be set yet. This will silently pass over them.
                pass
        return my_dict

    def get_db_row(self):
        return Database.RequestRow(self._get_dict())


def _get_list_of_requests(hashtag, api=api_init(), testing=0, count=100):
    db = Database.RequestDB(testing=testing)
    my_list = []
    remaining = my_helper.get_remaining(api)
    assert remaining > 1
    for tweet in tweepy.Cursor(api.search,
                               q=hashtag,).items(count):
        if not db.check_if_in_db(str(tweet.id)):
            my_list.append(MapRequest(tweet, testing=testing))
    print(f"Found {len(my_list)} new tweets")
    remaining = my_helper.get_remaining(api)
    print(f"{remaining} Twitter calls left.")
    return my_list


def _add_list_of_requests_to_db(list_of_reqs, testing=0):
    if len(list_of_reqs) == 0:
        return print(f"No rows added to database")
    db = Database.RequestDB(testing=testing)
    print(f"Adding {len(list_of_reqs)} rows to database.")
    for obj in list_of_reqs:
        obj = obj.get_db_row()  # Convert into a DB row object
        db.add_to_db(row_dict=obj.get_dict())
    print(f"Finished adding to database.")


def process_requests(hashtag="#mappornrequest", testing=0, count=100):
    my_list = _get_list_of_requests(hashtag=hashtag, testing=testing, count=count)
    _add_list_of_requests_to_db(list_of_reqs=my_list, testing=testing)


def respond_to_requests(count=10, testing=0):
    new_requests = Database.RequestDB(testing=testing).get_unresponded_list()[:count]
    if len(new_requests) == 0:
        print("No new requests")
        return
    for request in new_requests:
        my_resp_dict = {'row_date': request.row_date,
                        'link': request.link,
                        'testing': request.testing
                        }
        pprint.pprint(request.text)
        time.sleep(1)
        my_response = input("How would you like to respond to this request? Press x to void it.\n\n")
        if my_response == '':
            print("Request Skipped.")
            continue
        elif my_response.lower() == 'x':
            print("Request voided.")
            Database.RequestDB(testing=testing).update_row_to_responded(unique_id=request.unique_id)
            continue
        my_like_dict = my_resp_dict  # Copy the dictionary into two rows.
        # This way there will be a like action and comment action

        my_like_dict['directive'] = 'like'
        my_resp_dict['directive'] = 'comment'
        my_resp_dict['text'] = my_response
        my_resp_row = Database.ActionRow(action_dict=my_resp_dict)
        my_like_row = Database.ActionRow(action_dict=my_like_dict)
        Database.ActionDB(testing=testing).add_to_db(my_resp_row.get_dict())
        Database.ActionDB(testing=testing).add_to_db(my_like_row.get_dict())
        Database.RequestDB(testing=testing).update_row_to_responded(unique_id=request.unique_id)
        time.sleep(1)
        print("Response Added to Database.")
