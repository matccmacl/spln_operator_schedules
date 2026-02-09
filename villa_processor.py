import camelot
import re
import pandas as pd

#filtered_df = df[df['City'] == 'New York']

villa_pdf = 'airline_schedules/villa_air_DHC6  SCHEDULE  09-02-2026.pdf'
villa_filename = villa_pdf.split("/")[-1]


villa_date_pattern = r"([0-9]{2}-[0-9]{2}-[0-9]{4})"
match = re.search(villa_date_pattern, villa_filename)

villa_date = pd.to_datetime(match.group(1)).strftime('%Y-%m-%d')
villa_date = pd.to_datetime(villa_date)
print(villa_date)

villa_tables = camelot.read_pdf(villa_pdf, pages='all', flavor='stream')

villa_all_tables = []

for table in villa_tables:
  # Fix: Use '&' and parentheses to filter out rows where column 3 is '0' OR empty
  filtered_df = table.df[(table.df[3] != '0') & (table.df[3] != '')].drop(index =[2,4]).iloc[:,[2,3,4,5,6,7,8]]
  villa_all_tables.append(filtered_df)
  print(filtered_df)