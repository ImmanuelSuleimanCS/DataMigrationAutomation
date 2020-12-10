#!/usr/bin/env python
# coding: utf-8

# # INTRODUCTION
#     # Use pandas to automate data migration and report creation
#     # You work for a company that has offices in different cities across the us
#     # they have sales data for 1 10 year period
#     # and need you to do the following
# 
# ##### 1.	Create heatmaps
#          a.	Year by region
#          b.	Year by property
#          c.	Year by month
#          d.	City by year
# ##### 2.	Create graphs with a row for each year and a column for each region
#          a.	Profit/loss
#          b.	ROI by quarter
#          c.	ROI by month
#          d.	ROI by property type
# ##### 3.	Save records to json file by year
#          a.	Group by regional manager and city rep
# ##### 4.	Main skills used
#          a.	Use os module to navigate folder
#          b.	Use merge function to join tables(dataframe)
#          c.	Use XlsxWriter to save tables and charts to a file
#          d.	Use json library to write to json

# # PART ONE
# ## IMPORT STATEMENTS AND READING IN MULTIPLE FILES

# In[ ]:


import pandas as pd
import datetime 
import os
import json
import seaborn as sns
import calendar

Start=datetime.datetime.now()


# In[ ]:


BasePath=os.getcwd()
BasePath


# In[ ]:


def Dir(name):
    path=f"{BasePath}\{name}"
    os.makedirs(f"{BasePath}\{name}",exist_ok=True)
    return path


# In[ ]:


def GetFiles(path,ext):
    os.chdir(f"{BasePath}\{path}")
    df=pd.concat([pd.read_csv(file) for file in os.listdir() if os.path.splitext(file)[1]==ext])
    return df


# In[ ]:


df=GetFiles("Sales Data",".txt")


# In[ ]:


df


# In[ ]:


refFile=f"{BasePath}\City-Region Ref.xlsx"
Ref=pd.read_excel(refFile, sheet_name=None)
City,Manager,Rep=[Ref[tab] for tab in Ref]


# # PART TWO
# ## GROOM AND MERGE DATA WITH REF TABLES

# In[ ]:


def CityState(df):
    state=df["State"]
    city=df["City"]
    return f"{city}, {state}"

df["City"]=df.apply(CityState, axis=1)


# In[ ]:


City=City.apply(lambda x:x.astype(str).str.upper())
Manager=Manager.apply(lambda x:x.astype(str).str.upper())
Rep=Rep.apply(lambda x:x.astype(str).str.upper())


# In[ ]:


def OuterJoin(df1,df2,index1,index2):
    df1=df1.set_index(index1)
    df2=df2.set_index(index2)
    DF=df1.merge(df2, how="outer", left_index=True, right_index=True)
    DF=DF.reset_index().rename(columns={"index":index1})
    return DF


# In[ ]:


df=OuterJoin(df,City,"City","City")
df=OuterJoin(df,Manager,"Region","Region")
df=OuterJoin(df,Rep,"City","City")


# In[ ]:


def ConvertNum(value):
    value=value.replace("$","").replace(",","")
    value=float(value)
    return value


# In[ ]:


df["Investment"]=df['Investment'].apply(ConvertNum)
df["Revenue"]=df['Revenue'].apply(ConvertNum)


# In[ ]:


df["Date"]=pd.to_datetime(df["Date"])


# In[ ]:


df["year"]=df["Date"].apply(lambda x:x.year)
df["month"]=df["Date"].apply(lambda x:x.month)
df["quarter"]=df["Date"].apply(lambda x:x.quarter)


# In[ ]:


df["Net"]=df["Revenue"]-df["Investment"]
df["Net"]=df["Net"].round(3)


# In[ ]:


def ROI(df):
    return round(df["Net"]/df["Investment"],3)

df["ROI"]=df.apply(ROI, axis=1)


# In[ ]:


df["Profit/Loss"]=df["ROI"].apply(lambda x:"Profit" if x > 0 else "Loss")


# # PART THREE
# ## DEFINE HEATMAP AND SUMMARY FUNCTIONS

# In[ ]:


def HeatMap(df,indexes,columns,value=None, axis=None):
    Heatmap=pd.pivot_table(df, values=value,index=indexes,
                           columns=columns).round(3)
    Heatmap=Heatmap.style.background_gradient(cmap=sns.light_palette("green",
                                                                    as_cmap=True), axis=axis)
    return Heatmap


# In[ ]:


yearRegion=HeatMap(df,["year"],["Region"],value="ROI",axis=1)
yearProperty=HeatMap(df,["year"],["Property Type"],value="ROI",axis=1)
yearMonth=HeatMap(df,["year"],["month"],value="ROI",axis=1)
cityYear=HeatMap(df,["City"],["year"],value="ROI",axis=0)


# In[ ]:


def GetSummary(subtype=None):
    d1={}
    for year in df["year"].unique():
        for region in df["Region"].unique():
            DF = df[(df["year"]==year) & (df["Region"]==region)]
            if subtype=="A":
                DF=DF.groupby(["quarter","Profit/Loss"])["Profit/Loss"].count()
                DF=DF.unstack().fillna(0).astype(int)
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
            elif subtype=="D":
                DF=DF.groupby(["Property Type"])["ROI"].mean().to_frame().round(3)
                
            d1[f"{year}-{region}"]=DF
    return d1


# # PART FOUR
# ## DEFINE FUNCTIONS TO INSERT TABLES AND CHARTS

# In[ ]:


def InsertTable(dictionary,writer,title):
    row=0
    for i,x in enumerate(dictionary):
        DF=dictionary[x]
        sLen=len(DF[DF.columns[0]])
        DF.to_excel(writer,sheet_name=title,
                   startrow=row,
                   startcol=0)
        row=(row+sLen+2)


# In[ ]:


# https://pandas-xlsxwriter-charts.readthedocs.io/introduction.html
def InsertCharts(dictionary,worksheet,workbook,sheet_name):
    chart_list=[]
    row=1
    columns=0
    for i,x in enumerate(dictionary):
        title=f"{x}"
        DF=dictionary[x]
        sLen=len(DF.iloc[0])+1
        rLen=len(DF.index)
        chart=workbook.add_chart({"type":"column"})
        for col_num in range(1,sLen):
            chart.add_series({"name":[sheet_name,columns,col_num],
                             "categories": [sheet_name,row,0,(rLen+row-1),0],
                             "values": [sheet_name,row,col_num,(rLen+row-1), col_num],
                             "overlap": -5,
                             "data_labels": {"value":True,
                                             "font":{"name":"Calibri","bold":True,"size":10}}
                             })
        chart.set_x_axis({"name":"","major_gridlines":{"visible":False}})
        chart.set_y_axis({"name":"","major_gridlines":{"visible":False}})
        chart.set_title({"name":title})
        chart.set_legend({"position":"bottom"})
        
        chart.set_size({"width":700,"height":477.252})
        chart_list.append(chart)
        row=row+rLen+2
        columns=columns+rLen+2
        
        rowNum=1
        count=0
        
        cellDict={1:"A",2:"L",3:"W",
                 4:"AH",5:"AS",6:"BD",7:"BO"}
        
        for i,x in enumerate(chart_list):
            count += 1
            worksheet.insert_chart(cellDict[count]+str(rowNum), chart_list[i],
                                   {"x_scale":1,"y_scale":1})
            if count == 7:
                count=0
                rowNum += 24


# # PART FIVE
# ## DEFINE FUNCTIONS TO SAVE DATA TO EXCEL FILE

# In[ ]:


def SaveData(dList,savePath):
    with pd.ExcelWriter(f"{savePath}\ROI Summary.xlsx") as writer:
        tablist=["Region","Property","Month","City"]
        hList=[yearRegion,yearProperty,yearMonth,cityYear]
        for a,b in zip(hList,tablist):
            a.to_excel(writer, sheet_name=b)
            
        workbook=writer.book
        DB_List=[]
        DB_List.append(workbook.add_worksheet("Profit_Loss by quarter"))
        DB_List.append(workbook.add_worksheet("ROI by quarter"))
        DB_List.append(workbook.add_worksheet("ROI by month"))
        DB_List.append(workbook.add_worksheet("ROI by property type"))
        for x in DB_List:
            x.set_zoom(36)
            
        RefList=["A","B","C","D"]
        
        for a,b,c in zip(dList,DB_List,RefList):
            InsertTable(a,writer,c)
            InsertCharts(a,b,workbook,c)


# # PART SIX
# ## DEFINE FUNCTION TO SAVE RECORDS TO JSON FILES

# In[ ]:


exportcolumns=['City', 'Region', 'State', 'Investment',
               'Revenue', 'Date', 'Property Type', 'month',
               'quarter', 'Net', 'ROI', 'Profit/Loss']
totalRows=0
year={}
for x in df["year"].unique():
    manager={}
    for y in df["Regional Manager"].unique():
        rep={}
        for z in df["City Rep"].unique():
            DF = df[(df["year"]==x) & (df["Regional Manager"]==y) & (df["City Rep"]==z)]
            DF["Date"]=DF["Date"].astype(str)
            if DF.shape[0]>0:
                totalRows+=DF.shape[0]
                DF=DF[exportcolumns]
                rep[z]=DF.to_dict(orient="records")
                manager[y]={"City Reps":rep}
                year[str(x)]=manager


# In[ ]:


DF=pd.DataFrame(year.items(), columns=["Year","Regional Manager"])


# In[ ]:


def SaveToJson(df,destination):
    for x in df["Year"].unique():
        json=df[df["Year"]==x]
        json=json.to_json(orient="records")
        with open (f"{destination}\Real Estate Sales Data - {x}.json", "w") as f:
            f.write(json)


# # PART SEVEN

# ## CALL FUNCTIONS TO SAVE CHARTS/TABLES TO FILE

# In[ ]:


dList=[GetSummary(subtype="A"),GetSummary(subtype="B"),
      GetSummary(subtype="C"),GetSummary(subtype="D")]
SaveData(dList,Dir("Output-ROI"))


# ## CALL FUNCTION TO SAVE RECORDS TO JSON FILES

# In[ ]:


SaveToJson(DF,Dir("Output-Json"))


# In[ ]:


End=datetime.datetime.now()


# In[ ]:


print(f"{End-Start}")


# In[ ]:


print(totalRows)
df.shape[0]

