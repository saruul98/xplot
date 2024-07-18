"""
Saruul Nasanjargal (Hannover, 2024)
"""
import os
import time
import numpy as np
from datetime import datetime

FSAMP = 50
NCHAN = 8

# filepath = os.path.join(os.getcwd(), datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + ".txt")
filepath = os.path.join(os.getcwd(), "testdata.txt")
print(filepath)

while True:
    seconds = time.time()
    data = np.random.randn(NCHAN)
    with open(filepath, 'a') as file:
        for item in data:
            file.write(str(item) + ' ')
        file.write('\n')
    # print('time = ', seconds)
    time.sleep(1/FSAMP)
