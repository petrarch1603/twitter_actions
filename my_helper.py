import csv
import Database
import datetime
import my_secrets
import re
import sys
import time
import tweepy
import uuid


def api_init():
    auth = tweepy.OAuthHandler(my_secrets.consumer_key(), my_secrets.consumer_secret())
    auth.set_access_token(my_secrets.access_token(), my_secrets.access_secret())
    return tweepy.API(auth)


def get_remaining(api_obj=api_init()):
    assert api_obj.rate_limit_status()['resources']['lists']['/lists/list']['remaining'] > 1
    my_remaining = int(api_obj.last_response.headers['x-rate-limit-remaining'])
    if my_remaining < 10:
        print(f"Only {my_remaining} Twitter Calls Left!")
        time.sleep(15)
    return my_remaining


def datetime_from_utc_to_local(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset


def datetime_converter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


def re_gets_handle(my_text_string):
    my_pattern = '(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z]+[A-Za-z0-9-_]+)'
    return re.search(my_pattern, my_text_string)


def check_if_user_exists(user):
    api = api_init()
    try:
        user_obj = api.get_user(user)
        return user_obj
    except tweepy.error.TweepError:
        return None


def update_progress(progress):
    progress = float(format(progress, '.2f'))
    bar_length = 50  # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(bar_length*progress))
    text = "\rStatus: [{0}] {1}% {2}".format(
        "#"*block + "-"*(bar_length-block), progress*100, status)
    sys.stdout.write(text)
    sys.stdout.flush()


def get_unique_id():
    return str(uuid.uuid1().int)


def get_time_zone():
    # TODO Write this Function!
    return


def check_mentions(single_tweet_line):
    my_handle = re_gets_handle(str(single_tweet_line))
    if my_handle is None:
        return
    my_handle = my_handle.group()
    assert get_remaining() > 5
    if check_if_user_exists(my_handle) is None:
        print(f"WARNING: {my_handle} does not exist!")
        exit()


def test_csv(master_list):
    for num, i in enumerate(master_list):
        num = num + 1
        update_progress(float(format(num / len(master_list), '.2f')))
        try:
            assert len(i) > 0
            assert i[1] == 'comment' or i[1] == 'like' or i[1] == 'retweet'
            if i[1] == 'comment':
                assert len(i[2]) > 0
            assert len(i[0]) > 0
        except AssertionError as e:
            print(e)
            print(num)
            exit()
        check_mentions(i)


def add_csv_to_database(csv_path, testing=0):
    with open(csv_path, 'r+', encoding='utf-8') as f:
        reader = csv.reader(f)
        master_list = list(reader)
    test_csv(master_list)
    list_of_rows = []
    problem_list = []
    for row in master_list:
        try:
            my_dict = {'link': row[0],
                       'directive': row[1],
                       'row_date': datetime.datetime.now()}
            if len(row) == 3:
                my_dict['text'] = row[2]
            list_of_rows.append(Database.ActionRow(my_dict))
        except Exception as e:
            print(f"Problem encountered: {e}")
            problem_list.append(row)
    for i in list_of_rows:
        try:
            Database.ActionDB(testing=testing).add_to_db(row_dict=i.get_dict())
        except Exception as e:
            print(f"Problem encountered: {e}, adding this row to the problem list")
            problem_list.append(i.get_dict())

    print(f"Finished adding all rows to database")
    with open(csv_path, 'w+') as f:
        writer = csv.writer(f)
        writer.writerows([])

    if len(problem_list) > 0:
        with open('data_discover_followers/problem_rows.csv', 'w+') as f:
            writer = csv.writer(f)
            writer.writerows(problem_list)


def check_for_keyword(keyword, test_string):
    if keyword.lower() in test_string.lower():
        return True
    else:
        return False

