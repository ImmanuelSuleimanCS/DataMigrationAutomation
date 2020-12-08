# Use pandas to automate data migration and report creation

# You work for a company that has offices in different cities across the us
# they have sales data for 1 10 year period
# and need you to do the following

# 1.	Create heatmaps
#     a.	Year by region
#     b.	Year by property
#     c.	Year by month
#     d.	City by year
# 2.	Create graphs with a row for each year and a column for each region
#     a.	Profit/loss
#     b.	ROI by quarter
#     c.	ROI by month
# 3.	Save records to json file by year

# 1.	Main skills used
#     a.	Use os module to navigate folder
#     b.	Use merge function to join tables(dataframe)
#     c.	Use XlsxWriter to save tables and charts to a file
#     d.	Use json library to write to json


# write import statement
import pandas as pd
import datetime
import os
import json
import seaborn as sns
import calendar

start=datetime.datetime.now()

# define function to concat all specified files types
def getFiles(path,ext):
    os.chdir(path)
    df=pd.concat([pd.read_csv(file) for file in os.listdir() if os.path.splitext(file)[1]==ext])
    return df

# specify file path with file that you want to read
path=r"PLACE FILEPATH HERE!"
# call getfiles function
df=getFiles(path,".txt")

# specify ref file
refFile=rr"PLACE FILEPATH HERE!"
# read in ref file as ordered dict
Ref=pd.read_excel(refFile, sheet_name=None, encoding="utf8")
# unpack ref files into dataframes
City,Manager,Rep=[Ref[tab] for tab in Ref]

# define function to combine city and state
def combineCityState(df):
    state=df["State"]
    city=df["City"]
    return f"{city}, {state}"

df["City"]=df.apply(combineCityState, axis=1)

# convert ref tables to upper string
# https://stackoverflow.com/questions/39512002/convert-whole-dataframe-from-lower-case-to-upper-case-with-pandas
City=City.apply(lambda x:x.astype(str).str.upper())
Manager=Manager.apply(lambda x:x.astype(str).str.upper())
Rep=Rep.apply(lambda x:x.astype(str).str.upper())

def MergeIndex(df1,df2,index1,index2):
    df1=df1.set_index(index1)
    df2=df2.set_index(index2)
    mergedDF=df1.merge(df2, how="outer",left_index=True, right_index=True)
    mergedDF=mergedDF.reset_index().rename(columns={"index":index1})
    return mergedDF

df=MergeIndex(df,City,"City","City")
df=MergeIndex(df,Manager,"Region","Region")
df=MergeIndex(df,Rep,"City","City")

# convert currency string to float
# one line conversion
# df["Investment"].apply(lambda x:float(x.replace("$","").replace(",","")))

def convertNum(value):
    value=value.replace("$","").replace(",","")
    value=float(value)
    return value

df["Investment"]=df["Investment"].apply(convertNum)
df["Revenue"]=df["Revenue"].apply(convertNum)

# convert date to datetime object
df["Date"]=pd.to_datetime(df["Date"])

# get year, month, and quarter from datetime object
df["year"]=df["Date"].apply(lambda x:x.year)
df["month"]=df["Date"].apply(lambda x:x.month)
df["quarter"]=df["Date"].apply(lambda x:x.quarter)

df["Net"]=df["Revenue"]-df["Investment"]

# function to get return ROI
def ROI(df):
    a=df["Investment"]
    b=df["Net"]
    roi=round((b/a),3)
    return roi
df["ROI"]=df.apply(ROI,axis=1)
df["Profit/Loss"]=df["ROI"].apply(lambda x:"Profit" if x > 0 else "Loss")


# define function to return color coded heatmap
def HeatMap(df,iList,cList,axis=None):
    HeatMap=pd.pivot_table(df, values="ROI",
              index=iList,
              columns=cList).round(3)
    HeatMap=HeatMap.style.background_gradient(cmap=sns.light_palette("green", as_cmap=True), axis=1)
    return HeatMap

# get heatmap objects
yearRegion=HeatMap(df,["year"],["Region"])
yearProperty=HeatMap(df,["year"],["Property Type"])
yearMonth=HeatMap(df,["year"],["month"])
cityYear=HeatMap(df,["City"],["year"],axis=0)

# 1.	define a loop that run through each unique year and region
# 2.	use groupby function to get count of profit/loss by quarter
# 3.	get pivot table of avg ROI by quarter and region
# 4.	get pivot table of avg ROI by month and region
# 5.	get string month value from number

def getSummary(subtype=None):
    d1={}
    for year in df["year"].unique():
        for region in df["Region"].unique():
            DF=df[(df["year"]==year) & (df["Region"]==region)]
            if subtype=="A":
                DF=DF.groupby(["quarter","Profit/Loss"])["Profit/Loss"].count().unstack().fillna(0).astype(int)
                DF=DF[["Profit","Loss"]]
            elif subtype=="B":
                DF=pd.pivot_table(DF, values="ROI",
                               index=["quarter"],
                                  columns="Region").round(3)
            elif subtype=="C":
                DF=pd.pivot_table(DF, values="ROI",
                               index=["month"],
                                  columns="Region").round(3)
                DF.index=DF.index.map(lambda x:calendar.month_abbr[x])
            d1[f"{year}-{region}"]=DF
    return d1

def InsertTable(_DICTIONARY,_WRITER,title):
    row=0
    for i,x in enumerate(_DICTIONARY):
        tempDF=_DICTIONARY[x]
        
        #watch out here
        #get the length of the first field
        #tempDF.columns[0] return the first column name
        #tempDF[tempDF.columns[0]] return a series
        #len(tempDF[tempDF.columns[0]]) returns the length of the series
        sLen=len(tempDF[tempDF.columns[0]])
        
        tempDF.to_excel(_WRITER,
                        sheet_name = title
                        ,startrow=row, startcol=0)
        row=(row+sLen+2)

def InsertChart(_DICTIONARY,
                _WORKSHEET,
                WORKBOOK,
                _SheetName):
    chart_List=[]
    _Row=1
    _Columns=0
    for i,x in enumerate(_DICTIONARY):
        title=f"{x}"
        tempDF=_DICTIONARY[x]
        qaz=tempDF.iloc[0]
        sLen=len(qaz)+1
        rLen=len(list(_DICTIONARY[x].index))
        chart = WORKBOOK.add_chart({'type': 'column'})
        for col_num in range(1, sLen):
            chart.add_series({
                'name':       [_SheetName, _Columns, col_num],
                'categories': [_SheetName, _Row, 0, (rLen+_Row-1), 0],
                'values':     [_SheetName, _Row, col_num, (rLen+_Row-1), col_num],
                'overlap':    -5,
                'data_labels': {'value': True,
                                'font': {'name': 'Calibri', "bold":True, "size":10}}
            })
            chart.set_x_axis({'name':"", 'major_gridlines': {'visible': False}})
            chart.set_y_axis({'name':"", 'major_gridlines': {'visible': False}})
        chart.set_title ({'name':title})
        chart.set_legend({'position': 'none'})
        chart.set_size({'width': 700, 'height': 477.252})
        chart_List.append(chart)
        _Row =_Row+rLen+2
        _Columns = _Columns+rLen+2
    # ------------------------------------------------------------------------------------
    # Insert the chart into the worksheet.
    num1=1
    num2=5
    _count_=0
    cellDict={1: 'A', 2: 'L', 3: 'W', 4: 'AH', 5: 'AS', 6: 'BD', 7: 'BO'}
    for i,x in enumerate(_DICTIONARY):
        _count_+=1
        _WORKSHEET.insert_chart(cellDict[_count_]+str(num1), chart_List[i],{"x_scale":1,"y_scale":1})
        if _count_ == 7:
            _count_= 0
            num1+=24

# saves charts to file
def SaveCharts(dList,savePath):
    with pd.ExcelWriter(f"{savePath}\ROI.xlsx") as writer:
#         save heatmap
        tabList=["Year Region","Year Property",
                 "Year Month","City Year"]
        hList=[yearRegion,yearProperty,yearMonth,cityYear]
        for a,b in zip(hList,tabList):
            a.to_excel(writer,sheet_name=b)
            
        workbook=writer.book
        DB1=workbook.add_worksheet("Profit_Loss by year")
        DB2=workbook.add_worksheet("ROI by quarter")
        DB3=workbook.add_worksheet("ROI by month")
        
        DBList=[DB1,DB2,DB3]
        for x in DBList:
            x.set_zoom(36)
        RefList=["Ref 1","Ref 2","Ref 3"]
        for a,b,c in zip(dList,DBList,RefList):
            InsertTable(a,writer,c)
            InsertChart(a,b,workbook,c)

# call functions to save everything
savePath=rr"PLACE FILEPATH HERE!"
DictList=[getSummary(subtype="A"),getSummary(subtype="B"),getSummary(subtype="C")]
SaveCharts(DictList,savePath)

os.chdir(rr"PLACE FILEPATH HERE!")
def saveToJson(subtype=None):
    for x in df["year"].unique():
        js=df[df["year"]==x]
        js["Date"]=js["Date"].astype(str)
        js=js.to_json(orient=subtype)
        with open(f"{subtype.upper()}-{x} Data.json","w") as f:
            f.write(js)

# call function to save to json
saveToJson("records")

end=datetime.datetime.now()
print(f"{end-start}")

