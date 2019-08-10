import csv
import os


keyword = input('What is the keyword?\n').lower()
print(keyword)

dir_path = 'data_discover_followers/tweet_data/'

match_list = []
for file in os.listdir(dir_path):
    with open(dir_path + str(file), encoding='utf-8') as my_csv:
        csvreader = csv.reader(my_csv)
        for row in csvreader:
            my_text = row[2].lower()
            if keyword in my_text:
                match_list.append([my_text[:60], row[1]])

for i in match_list:
    print(str(i[0]) + ' ' + str(i[1]) + ' \n')
