import pdfplumber
import camelot
import pandas as pd
import os
import io

pdf_path = "airline_schedules/Aircraft Allocation for 25TH Jan 2026  ISSUE 2.pdf"
filename = os.path.basename(pdf_path).replace(".pdf", "")

# Improved parsing for the date string
date_str = filename.split("Aircraft Allocation for ")[-1].split("ISSUE")[0].strip()
date_object = pd.to_datetime(date_str)

all_tables_2 = camelot.read_pdf(pdf_path, pages="all", flavor="stream")

combined_df = pd.concat([table.df for table in all_tables_2], ignore_index=True)
combined_df.drop(index=[0, 1, 2, 3], inplace=True)



def clean_tables(df):

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
    combined_df["FLT NUMBER"] = combined_df["FLT NUMBER"].str.replace(
        "0:00\n", "", regex=False
    )

    combined_df["DATE TIME"] = pd.to_datetime(
        combined_df["DATE"].dt.strftime("%Y-%m-%d") + " " + combined_df["TIME"]
    )

    return combined_df


cleaned_df = clean_tables(combined_df)

print(cleaned_df.head(10))
