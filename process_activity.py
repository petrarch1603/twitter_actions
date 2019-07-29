import csv
import my_helper
import re
import my_secrets
import time
import tweepy


my_csv = 'data_discover_followers/processing_queue.csv'


class _ProtoActivity:
    def __init__(self, raw_url, activity_type, text_content=''):
        self.raw_url = raw_url
        self.activity_type = activity_type
        self.text_content = text_content
        self.id = re.search('(?<=status/)(.*)$', raw_url)[0]
        self.author = re.search('(?<=.com/).*(?=/status)', raw_url)[0]


class CommentActivity(_ProtoActivity):

    def __init__(self, raw_url, activity_type, text_content):
        _ProtoActivity.__init__(self, raw_url, activity_type, text_content)
        self.status = self._comment()

    def _comment(self):
        if self.author.lower() == 'mapporntweet':
            return api.update_status(status=self.text_content,
                                     in_reply_to_status_id=self.id)
        else:
            return api.update_status(status=self.text_content + ' @' + self.author,
                                     in_reply_to_status_id=self.id)


class LikeActivity(_ProtoActivity):

    def __init__(self, raw_url, activity_type):
        _ProtoActivity.__init__(self, raw_url, activity_type)
        self.status = self._like()

    def _like(self):
        return api.create_favorite(id=self.id)


class RetweetActivity(_ProtoActivity):

    def __init__(self, raw_url, activity_type):
        _ProtoActivity.__init__(self, raw_url, activity_type)
        self.status = self._retweet()

    def _retweet(self):
        return api.retweet(id=self.id)


def init():
    auth = tweepy.OAuthHandler(my_secrets.consumer_key(), my_secrets.consumer_secret())
    auth.set_access_token(my_secrets.access_token(), my_secrets.access_secret())
    return tweepy.API(auth)


with open(my_csv, 'r+', encoding='utf-8') as f:
    reader = csv.reader(f)
    master_list = list(reader)

api = init()
api.wait_on_rate_limit_notify = True


def main_process_activity():
    time_interval = int(3600/int(len(master_list)))
    problem_list = []
    for i in master_list:
        print('Next!')
        try:
            my_remaining = my_helper.get_remaining(api)
            print(my_remaining)
            assert my_remaining > 1
            time.sleep(time_interval)
            if i[1] == 'comment':
                my_comment = CommentActivity(i[0], i[1], i[2])
                print(str(my_comment.status))
            elif i[1] == 'like':
                my_like = LikeActivity(i[0], i[1])
                print(str(my_like.status))
            elif i[1] == 'retweet':
                my_retweet = RetweetActivity(i[0], i[1])
                print(str(my_retweet.status))
        except Exception as e:
            print('Problem encountered: ' + str(e) + '\n ' + str(i))
            problem_list.append(i)

    with open(my_csv, 'w+') as f2:
        writer = csv.writer(f2)
        writer.writerows(problem_list)

    return print('Finished processing activity!')
