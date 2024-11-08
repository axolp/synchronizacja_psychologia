
from datetime import datetime, timedelta

def load_data(path):
    data= []
    with open(path) as file:
        data= [int(line) for line in file]
    return data

def convert_to_h_m_s(starting_time, data):
    time_data= []
    current_time= datetime.strptime(starting_time, "%H:%M:%S")
    for t in data:
        current_time+= timedelta(milliseconds=t)
        time_data.append(current_time)
    return time_data

p1_data= load_data("dane1.txt")
d= convert_to_h_m_s("16:53:21", p1_data)
print(d)