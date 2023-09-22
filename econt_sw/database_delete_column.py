from testing.sqlite3_database import *
import argparse
# show_all_plan(database_name='tray_1_database', table_name = 'tray_1_database')
parser = argparse.ArgumentParser()
parser.add_argument('--column', '-c', type=int, default=-9999, help='Colunm number number')
args = parser.parse_args()
column = args.column
delete_one_row(row=column, database_name='Econt_database', table_name='Econt_database')
show_all_plan(database_name='Econt_database', table_name = 'Econt_database')

