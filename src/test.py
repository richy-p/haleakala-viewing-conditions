from os import write
import sys
import glob

class Tee(object):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush() # If you want the output to be visible immediately
    def flush(self) :
        for f in self.files:
            f.flush()

# f = open('out.txt', 'a')
# sys.stdout = Tee(sys.stdout, f)
# print("test5")  # This will go to stdout and the file out.txt

# #use the original
# sys.stdout = sys.__stdout__
# print("This won't appear on file")  # Only on stdout
# f.close()





# def printLog(*args, **kwargs):
#     print(*args, **kwargs)
#     with open('output.out','a') as file:
#         print(*args, **kwargs, file=file)

# printLog('hello world')



# f = open('out.txt', 'a')
# f.write('anotherTest')
# f.flush()
# f.close()

