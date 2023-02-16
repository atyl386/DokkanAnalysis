# Purpose of this script is to update existing DokkanKit files with an updated format, determined by the Template File.
# The template file should contain default values for each parameter
# Need to go though all character files with active skill and fill in details (started in 8year folder )
import pandas as pd
import numpy as np
templateDir = r'C:\Users\Tyler\Documents\DokkanAnalysis\DokkanKitTemplate.xlsx'
dstDir = r'C:\Users\Tyler\Documents\DokkanAnalysis\DokkanKits'
srcDir = r'C:\Users\Tyler\Documents\DokkanAnalysis\DokkanKits'
templateDf = pd.read_excel(templateDir)
rows = templateDf.shape[0]
for i in range(8,105):
    filename = str(i)+".xlsx"
    src = srcDir+"\\"+filename
    dst = dstDir+"\\"+filename
    oldDf = pd.read_excel(src)
    oldCols = 11
    newDf = templateDf.copy().set_index('Attribute\\Turn')
    k = 0
    j= 0
    while j < rows:
        #print(newDf.index[j],oldDf.values[j-k][0])
        if (newDf.index[j] == oldDf.values[j-k][0]): # If the same need to get exist values
            newDf.iloc[j,:oldCols-1] = oldDf.values[j-k][1:oldCols]
            if type(oldDf.values[j-k][12])!=str:
                if not(np.isnan(oldDf.values[j-k][12]) and np.isnan(oldDf.values[j-k][13])): # If entries already
                    newDf.iloc[j,oldCols:] = oldDf.values[j-k][oldCols+1:]
            else:
                newDf.iloc[j,oldCols:] = oldDf.values[j-k][oldCols+1:]
        elif oldDf.values[j-k][0] != 'Special':
            k +=1
        else:
            k-=1
            j-=1
        j+=1
        """         if (newDf.index[j]=='SA Mult 12' or newDf.index[j]=='SA Mult 18'):
             newDf.iloc[j,:2] = [1,oldDf.values[j][1]]
        else:
            newDf.iloc[j,:oldCols-1] = oldDf.values[j-k][1:]
        j +=1 """

    newDf.to_excel(dst)