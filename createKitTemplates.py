import shutil
src = r'C:\Users\Tyler\OneDrive\Documents\Gaming\DokkanKitTemplate.csv'
dir = r'C:\Users\Tyler\OneDrive\Documents\Gaming\DokkanKits'
for i in range(1,100):
    filename = str(i)+".csv"
    dst = dir+"\\"+filename
    shutil.copyfile(src,dst)