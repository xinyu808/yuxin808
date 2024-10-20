import os
import obspy
from obspy.core.stream import Stream
import repetition_function as rf
import matplotlib.pyplot as plt
from pythonProject.repetition_function import match_dataname,section_plot
from obspy.core.util import AttribDict

#这里是方便后续导入到Path下全部txt文件名称，方便批量化处理服务的。
if __name__ == "__main__":
    # path = os.path.abspath(r"./paz_respond")
    # paz = rf.get_paz(path)
    st = Stream()
    # #匹配台站参数和数据：
    # for sta_info,station in paz:
    #     try:
    #         st += match_dataname(station,sta_info)   #一定要在这一步加入的时候之前就将台站参数导进去，要不然就不好导入了
    #     except:
    #         continue
    # st.simulate(paz_remove="self")    ############这里我们去除台站相应参数失败了，图像很怪#############
    #   对读取到的数据进行滤波区分：
    st += rf.load_data(os.path.abspath(r"./data"))#可以在这里更改传入路径
    st_band = st.copy()
    st_band.filter('bandpass', freqmin=0.5, freqmax=1.0, corners=3, zerophase=True)
    #  绘制section图,导入进行滤波处理后的图：
    section_plot(st_band)