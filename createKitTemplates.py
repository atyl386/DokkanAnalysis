import shutil
src = r'C:\Users\Tyler\Documents\DokkanAnalysis\DokkanKitTemplate.xlsx'
dir = r'C:\Users\Tyler\Documents\DokkanAnalysis\DokkanKits'
for i in range(112,200):
    filename = str(i)+".xlsx"
    dst = dir+"\\"+filename
    shutil.copyfile(src,dst)