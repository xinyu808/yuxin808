import os
import obspy
from obspy.core.stream import Stream

import repetition_function as rf
from pythonProject.repetition_function import match_dataname

#这里是方便后续导入到Path下全部txt文件名称，方便批量化处理服务的。
if __name__ == "__main__":
    path = os.path.abspath(r"./paz_respond")
    paz = rf.get_paz(path)
    st = Stream()
    #匹配台站参数和数据：
    for sta_info,station in paz:
        try:
            st += match_dataname(station)   #一定要在这一步加入的时候之前就将台站参数导进去，要不然就不好导入了
        except:
            continue