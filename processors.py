import pdfplumber
import camelot
import pandas as pd
import os
import io
import re

pdf_path = "airline_schedules/Aircraft Allocation for 25TH Jan 2026  ISSUE 2.pdf"
filename = os.path.basename(pdf_path).replace(".pdf", "")

def combine_tables(file, filename):

    pattern = r"(\d{1,2})[A-Z]{2}\s([A-Za-z]+)\s(\d{4})"

    match = re.search(pattern, filename)

    if match:
        clean_date_str = f"{match.group(1)} {match.group(2)} {match.group(3)}"

    # Improved parsing for the date string


    date_object = pd.to_datetime(clean_date_str)

    all_tables_2 = camelot.read_pdf(file, pages="all", flavor="hybrid")

    combined_df = pd.concat([table.df for table in all_tables_2], ignore_index=True)
    combined_df.drop(index=[0, 1, 2, 3], inplace=True)
    combined_df = combined_df.drop(combined_df.columns[0], axis=1)

    return combined_df, date_object



def clean_tables_maldivian(df, date_object):

    df = pd.DataFrame(df)

    if df.shape[1] < 6:
        return None
    # df = all_tables[2]
    df = df.iloc[:, :6].copy()
    # Remove the first row, as it's often an unwanted header captured by tabula
    # df = df.iloc[1:].copy()
    df.columns = ["FLT NUMBER", "REG", "FROM", "TO", "STD", "STA"]
    df["DATE"] = date_object
    new_order = ["DATE", "FLT NUMBER", "REG", "FROM", "TO", "STD", "STA"]
    df = df[new_order]

    df["STA"] = df["STA"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["STA"] = pd.to_datetime(df["STA"].str.zfill(4), format="%H%M", errors="coerce").dt.strftime("%H:%M")

    df["STD"] = df["STD"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["STD"] = pd.to_datetime(df["STD"].str.zfill(4), format="%H%M", errors="coerce").dt.strftime("%H:%M")

    takeoff_df = df[df["FROM"] == "MLE"].copy()

    takeoff_order = ["DATE", "FLT NUMBER", "REG", "FROM", "TO", "STD", "DIRECTION"]
    takeoff_df["DIRECTION"] = "TAKEOFF"
    takeoff_df = takeoff_df[takeoff_order]
    takeoff_df.rename(columns={"STD": "TIME"}, inplace=True)

    landing_df = df[df["TO"] == "MLE"].copy()
    landing_order = ["DATE", "FLT NUMBER", "REG", "FROM", "TO", "STA", "DIRECTION"]
    landing_df["DIRECTION"] = "LANDING"
    landing_df = landing_df[landing_order]
    landing_df.rename(columns={"STA": "TIME"}, inplace=True)

    combined_df = pd.concat([takeoff_df, landing_df], ignore_index=True)
    # Corrected line: assign the result back to the column
    combined_df["FLT NUMBER"] = combined_df["FLT NUMBER"].str.replace("0:00\n", "", regex=False)

    combined_df["DATE TIME LOCAL"] = pd.to_datetime(combined_df["DATE"].dt.strftime("%Y-%m-%d") + " " + combined_df["TIME"])
    combined_df["DATE TIME UTC"] = combined_df["DATE TIME LOCAL"] - pd.Timedelta(hours=5)
    combined_df["AIRLINE"] = "MALDIVIAN"
    combined_df["SPECIES"] = "SEAPLANE"

    return combined_df



#test_df = combine_tables(pdf_path)
#combined_df, date_object = test_df

#cleaned_df = clean_tables_maldivian(combined_df, date_object)

#print(cleaned_df.head(10))
