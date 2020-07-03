import depeng.read_email as rm
import os

s = [0,1,2,3,4,5,6,7,8,9]
print(s[1:-1])
path ='../../spam'
fle = "b'7'.eml"
abs_file = os.path.join(path,fle)
with open(abs_file,'rb') as fp:
    print(rm.extract(fp,fp.name))
    fp.close()
