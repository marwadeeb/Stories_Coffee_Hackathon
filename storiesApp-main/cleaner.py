import pandas as pd
import numpy as np
import re


def to_number(x):
    """Parse a messy string value into a float. Returns NaN if unparseable."""
    if pd.isna(x):
        return np.nan
    s = str(x).replace(",", "").strip()
    s = re.sub(r"[^0-9\.\-]", "", s)
    if s.count(".") > 1:
        parts = s.split(".")
        s = parts[0] + "." + "".join(parts[1:])
    if s in ["", ".", "-", "-.", ".-"]:
        return np.nan
    try:
        return float(s)
    except Exception:
        return np.nan


def clean_monthly(file):
    """
    Cleans the monthly sales report (REP_S_00134_SMRY.csv).
    Accepts a file path or file-like object.
    Returns: monthlyClean DataFrame with Year, Branch Name, Jan-Dec, Annual Total.
    """
    mon0 = pd.read_csv(file, header=None, dtype=str)

    # Find the row that contains "January" — that is the real header
    headerIdx = mon0.index[
        mon0.apply(lambda r: r.astype(str).str.contains("January", na=False).any(), axis=1)
    ][0]

    monthlyClean = mon0.iloc[headerIdx:].copy()
    monthlyClean.columns = monthlyClean.iloc[0]
    monthlyClean = monthlyClean.iloc[1:].reset_index(drop=True)

    # Drop any repeated header rows
    rowText = monthlyClean.astype(str).agg(" ".join, axis=1).str.lower()
    monthlyClean = monthlyClean[~rowText.str.contains(r"\bjanuary\b", na=False)].reset_index(drop=True)

    # Extract Year and Branch Name from first two columns
    monthlyClean["Year"] = monthlyClean.iloc[:, 0]
    monthlyClean["Branch Name"] = monthlyClean.iloc[:, 1]
    monthlyClean["Year"] = monthlyClean["Year"].ffill()

    # Handle case where duplicate column names cause a DataFrame to be returned
    branch1 = monthlyClean.loc[:, "Branch Name"]
    if isinstance(branch1, pd.DataFrame):
        branch1 = branch1.iloc[:, 0]

    year_col = monthlyClean["Year"]
    if isinstance(year_col, pd.DataFrame):
        year_col = year_col.iloc[:, 0]

    # Keep only Jan-Sep columns that exist (Oct-Dec are in a separate section)
    monthCols = [
        c for c in ["January", "February", "March", "April", "May", "June",
                    "July", "August", "September"]
        if c in monthlyClean.columns
    ]

    monthlyClean = pd.concat(
        [year_col, branch1.rename("Branch Name"), monthlyClean[monthCols]],
        axis=1
    )

    # Find and merge Oct–Dec which are stored in a separate section of the CSV
    octHeaderIdx = mon0.index[
        mon0.apply(lambda r: r.astype(str).str.contains("October", na=False).any(), axis=1)
    ][0]

    oct0 = mon0.iloc[octHeaderIdx:].copy()
    oct0 = oct0.iloc[:, :6]

    oct = oct0.iloc[1:].copy()
    oct.columns = ["Year", "Branch Name", "October", "November", "December", "Total By Year"]
    oct = oct[oct["October"].astype(str).str.strip().str.lower() != "october"].reset_index(drop=True)
    oct["Year"] = oct["Year"].ffill()

    octMerge = oct[["Year", "Branch Name", "October", "November", "December"]].copy()
    monthlyClean = monthlyClean.merge(octMerge, on=["Year", "Branch Name"], how="left")

    # Convert all month columns to numeric
    allMonthCols = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    for c in allMonthCols:
        if c in monthlyClean.columns:
            monthlyClean[c] = monthlyClean[c].map(to_number)

    monthlyClean["Annual Total"] = monthlyClean[allMonthCols].sum(axis=1)

    return monthlyClean


def clean_products(file):
    """
    Cleans the product profitability report (rep_s_00014_SMRY.csv).
    Accepts a file path or file-like object.
    Returns: prodItems DataFrame with product-level profit metrics.
    """
    prod0 = pd.read_csv(file, header=None, dtype=str)

    prodHeaderIdx = prod0.index[
        prod0.apply(lambda r: r.astype(str).str.contains("Product Desc", na=False).any(), axis=1)
    ][0]

    prod = prod0.iloc[prodHeaderIdx + 1:].copy()
    prod.columns = [
        "Product Desc", "Qty", "Total Price", "Blank1",
        "Total Cost", "Total Cost %", "Total Profit", "Blank2",
        "Total Profit %", "Blank3"
    ]

    # Tag each row by its type (branch header, service type, category, section, or actual product)
    isQty = prod["Qty"].notna()
    desc = prod["Product Desc"].astype(str).str.strip()

    isBranch = desc.str.startswith("Stories")
    isService = desc.isin(["TAKE AWAY", "TABLE"])
    isCategory = desc.isin(["BEVERAGES", "FOOD"])
    is_section = (~isQty) & (~isBranch) & (~isService) & (~isCategory) & desc.ne("nan") & desc.ne("")

    prod["Branch"] = None
    prod["Service Type"] = None
    prod["Category"] = None
    prod["Section"] = None

    prod.loc[isBranch, "Branch"] = prod.loc[isBranch, "Product Desc"]
    prod.loc[isService, "Service Type"] = prod.loc[isService, "Product Desc"]
    prod.loc[isCategory, "Category"] = prod.loc[isCategory, "Product Desc"]
    prod.loc[is_section, "Section"] = prod.loc[is_section, "Product Desc"]

    prod["Branch"] = prod["Branch"].ffill()
    prod["Service Type"] = prod["Service Type"].ffill()
    prod["Category"] = prod["Category"].ffill()
    prod["Section"] = prod["Section"].ffill()

    # Keep only actual product rows
    prodItems = prod[isQty].copy()
    prodItems = prodItems[prodItems["Qty"].astype(str).str.strip().str.lower() != "qty"].copy()

    # Convert numeric columns
    numCols = ["Qty", "Total Price", "Total Cost", "Total Cost %", "Total Profit", "Total Profit %"]
    for c in numCols:
        prodItems[c] = (
            prodItems[c]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace(r"[^0-9\.\-]", "", regex=True)
        )
        prodItems[c] = pd.to_numeric(prodItems[c], errors="coerce")

    # Derived metrics
    prodItems["RevenueFixed"] = prodItems["Total Cost"].fillna(0) + prodItems["Total Profit"].fillna(0)
    prodItems["ProfitMargin"] = np.where(
        prodItems["RevenueFixed"] > 0,
        prodItems["Total Profit"] / prodItems["RevenueFixed"],
        np.nan
    )

    prodItems = prodItems.drop(columns=["Blank1", "Blank2", "Blank3", "Total Price"])

    return prodItems


def clean_category(file):
    """
    Cleans the category report (rep_s_00673_SMRY.csv).
    Accepts a file path or file-like object.
    Returns: df_cleaned DataFrame with Beverages/Food profit by branch.
    """
    df = pd.read_csv(file, header=None, dtype=str)

    # Find the first row that contains "Category" — that is the real header
    headerIdx = df.index[
        df.apply(lambda r: r.astype(str).str.contains(r"\bCategory\b", na=False).any(), axis=1)
    ][0]

    # Slice from the header row down, skip the header row itself
    data = df.iloc[headerIdx + 1:].reset_index(drop=True)

    # The category CSV has the same blank-column structure as the product CSV:
    # Category, Qty, Total Price, Blank1, Total Cost, Total Cost %, Total Profit, Blank2, Total Profit %, Blank3
    # Taking only 7 columns would map Blank1 → "Total Cost", shifting everything right.
    # So take 10 columns, name them with blanks, then drop the blank columns.
    data = data.iloc[:, :10].copy()
    data.columns = [
        "Category", "Qty", "Total Price", "Blank1",
        "Total Cost", "Total Cost %",
        "Total Profit", "Blank2",
        "Total Profit %", "Blank3"
    ]
    data = data.drop(columns=["Blank1", "Blank2", "Blank3"])

    # Remove rows where Category is a leaked header/date/report-code value.
    # These are rows that look like "Category", "22-Jan-26", "REP_S_00673", "Page …", etc.
    junk_mask = (
        data["Category"].astype(str).str.strip().str.lower().isin(["category", "nan", ""])
        | data["Category"].astype(str).str.contains(r"^\d{2}-[A-Za-z]{3}-\d{2}", na=False)
        | data["Category"].astype(str).str.contains(r"REP_S_", na=False, case=False)
        | data["Category"].astype(str).str.contains("Page", na=False)
        | data["Category"].astype(str).str.contains("Total By Branch", na=False, case=False)
    )
    data = data[~junk_mask].reset_index(drop=True)

    data["Category"] = data["Category"].astype(str).str.strip()

    # Extract branch via forward fill, then drop the branch-name-only rows
    data["Branch"] = data["Category"].where(data["Category"].str.startswith("Stories", na=False))
    data["Branch"] = data["Branch"].ffill()
    data = data[~data["Category"].str.startswith("Stories", na=False)].reset_index(drop=True)

    # Drop rows that are fully empty after branch rows are removed
    data = data.dropna(subset=["Qty", "Total Profit"], how="all").reset_index(drop=True)

    # Convert numeric columns
    numCols = ["Qty", "Total Price", "Total Cost", "Total Cost %", "Total Profit", "Total Profit %"]
    for c in numCols:
        data[c] = (
            data[c]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace(r"[^0-9\.\-]", "", regex=True)
        )
        data[c] = pd.to_numeric(data[c], errors="coerce")

    data["RevenueFixed"] = data["Total Cost"].fillna(0) + data["Total Profit"].fillna(0)

    cols = ["Branch"] + [col for col in data.columns if col != "Branch"]
    return data[cols]


def clean_sales(file):
    """
    Cleans the sales group report (rep_s_00191_SMRY-3.csv).
    Accepts a file path or file-like object.
    Returns: sales_cleaned DataFrame with product-level sales by group/division/branch.
    """
    sales = pd.read_csv(file)
    sales_cleaned = sales.drop(index=[0, 2])
    sales_cleaned = sales_cleaned.iloc[:, :-1]

    sales_cleaned = sales_cleaned[
        ~sales_cleaned.astype(str).apply(lambda x: x.str.contains("Page", na=False)).any(axis=1)
    ]

    sales_cleaned.columns = ["Description", "Barcode", "Qty", "Total Amount"]
    sales_cleaned = sales_cleaned.loc[:, ~sales_cleaned.columns.str.contains("Barcode", case=False)]
    sales_cleaned = sales_cleaned[
        ~sales_cleaned["Description"].isin(["Description", "Qty", "Total Amount"])
    ]

    # Extract Group, Division, Branch via forward fill then drop header rows
    for label, prefix in [("Group", "Group:"), ("Division", "Division:"), ("Branch", "Branch:")]:
        sales_cleaned[label] = sales_cleaned["Description"].apply(
            lambda x: x.split(":")[1].strip() if prefix in str(x) else None
        )
        sales_cleaned[label] = sales_cleaned[label].ffill()
        sales_cleaned = sales_cleaned[
            ~(
                sales_cleaned["Qty"].isna()
                & sales_cleaned["Total Amount"].isna()
                & sales_cleaned[label].notna()
            )
        ]

    sales_cleaned = sales_cleaned[~sales_cleaned["Description"].str.contains("Total by", na=False)]

    sales_cleaned["Total Amount"] = sales_cleaned["Total Amount"].replace(
        {",": "", "€": "", "$": "", "£": ""}, regex=True
    )
    sales_cleaned["Qty"] = pd.to_numeric(sales_cleaned["Qty"], errors="coerce")
    sales_cleaned["Total Amount"] = pd.to_numeric(sales_cleaned["Total Amount"], errors="coerce")

    return sales_cleaned
