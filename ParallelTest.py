import multiprocessing
from joblib import Parallel, delayed
from tqdm import tqdm
import time

def myfunction(i, parameters):
    time.sleep(4)
    print(i)
    return i

num_cores = multiprocessing.cpu_count()
print(num_cores)

myList = ["a", "b", "c", "d"]
parameters = ["param1", "param2"]
inputs = tqdm(myList)

if __name__ == "__main__":
    processed_list = Parallel(n_jobs = num_cores)(delayed(myfunction)(i, parameters) for i in inputs)
    print(processed_list)
