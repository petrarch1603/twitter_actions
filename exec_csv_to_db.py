import Database
import my_helper


my_helper.add_csv_to_database(csv_path='data_discover_followers/processing_queue.csv')

print(f"Remaining Unexecuted Actions = {len(Database.ActionDB().complete_unexecuted_list())}")
