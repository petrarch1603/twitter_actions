import calendar
import Database
import datetime
import my_helper

current_time = str(datetime.datetime.now().timestamp())
with open('data_discover_followers/last_time.txt') as f:
    my_number = float(f.read())
    previous = int(round(my_number,0))

print(f'Current Time is: {current_time}')
print(f'Previous Time is: {previous}')


api = my_helper.api_init()

mentions = api.mentions_timeline(count=100)


def get_day_of_week_var(target_dt_obj):
    if target_dt_obj.date() == datetime.datetime.now().date():
        return "today"
    else:
        return calendar.day_name[target_dt_obj.weekday()]


old_created = mentions[-1].created_at

oldest = f"Oldest Mention: {get_day_of_week_var(old_created)} at {old_created.time().isoformat()}"

def clean_mentions(raw_mentions):
    prc_mentions_list = []
    for raw in raw_mentions:
        my_created_at = (my_helper.datetime_from_utc_to_local(raw.created_at)).timestamp()
        if my_created_at > previous:
            print(f'This one was created at: {my_created_at}')
            prc_mentions_list.append(raw)
    return prc_mentions_list


print(oldest)
print(len(mentions))
mentions = clean_mentions(mentions)
print(f"Clean Mentions: {len(mentions)}")

for count, i in enumerate(mentions):
    print(i.created_at.timestamp())
    print(previous)
    print("\n" * 5)
    print(i.text)

    url = f"https://twitter.com/{i.user.screen_name}/status/{i.id}"
    comment = input("To reply push R, to like push L\n\n").lower()
    if comment == '':
        continue
    my_dict = {'link': url,
               'row_date': datetime.datetime.now()}
    if comment == 'r':
        print("Reply Process\n\n")
        my_dict['text'] = input("What would you like to reply with?\n\n")
        my_dict['directive'] = 'comment'
    elif comment == 'l':
        print("Like Process")
        my_dict['directive'] = 'like'
        my_dict['text'] = ''
    my_action = Database.ActionRow(my_dict)  # Create a Row Object
    print(f"Adding to database:\n"
          f"Link: {my_dict['link']}\n"
          f"Directive: {my_dict['directive']}\n"
          f"Text: {my_dict['text']}\n"
          f"Unique_ID: {my_action.unique_id}")
    confirmation = input("Does this look okay? Hit x to cancel")
    if confirmation.lower() == 'x':
        continue
    Database.ActionDB().add_to_db(row_dict=my_action.get_dict())  # Add to Database
    print(f"Rate Limit: {my_helper.get_remaining(api)}")
    count = count + 1
    my_helper.update_progress(float(format(count / len(mentions), '.2f')))

with open('data_discover_followers/last_time.txt', 'w') as f:
    f.write(current_time)

print(f"Rate Limit: {my_helper.get_remaining(api)}")
print("script finished!")
