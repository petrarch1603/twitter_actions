import Database
import my_helper


my_helper.add_csv_to_database(csv_path='data_discover_followers/processing_queue.csv')

act_db = Database.ActionDB()
