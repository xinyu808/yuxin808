import os
import re
import obspy
from obspy.core.stream import Stream
from obspy.core.util import AttribDict
from obspy.taup import TauPyModel
import matplotlib.pyplot as plt
import numpy as np


#利用生成器依次获得文件内容和文件名方便匹配
def get_paz(path):
    #获取当前路径下所有的文件名存储到path_file里：
    for path_state in os.walk(path):
        path_file = path_state[2]
    #依据文件名读取数据，并生成台站参数，这里我们用迭代器依次生成
    for paz_file in path_file:
        paz_filename = path + "\\" + paz_file
        station = paz_file.split(".")[2]
        with open(paz_filename, "r") as fo:
            lines = fo.read()
            yield lines,station #返回台站的信息和台站的名称

#把台站相关所需要的矫正的参数依次导出：(sensitivity,constant,zeros,poles)
def cut_pz_values(section_header,lines):
    #这里用于匹配poles和zeros的规则。
    section_pattern = re.compile(rf'{section_header}\s+\d+\n((\s+\S+\s+\S+\s?\n)+)')
    match = section_pattern.search(lines)
    if match:
        values = []
        for line in match.group(1).strip().split('\n'):
            parts = line.strip().split()
            real_part = float(parts[0])
            imag_part = float(parts[1])
            values.append(complex(real_part, imag_part))
        return values
    else:
        return []

def cut_pazvalue(lines):
    #提取SENSITIVITY值
    sensitivity_pattern = re.compile(r'SENSITIVITY\s+:\s+(\S+)')
    sensitivity_match = sensitivity_pattern.search(lines)
    sensitivity = float(sensitivity_match.group(1))

    # 提取 CONSTANT 值
    constant_pattern = re.compile(r'CONSTANT\s+(\S+)')
    constant_match = constant_pattern.search(lines)
    constant = float(constant_match.group(1))

    #提取POLES和ZEROS值
    zeros = cut_pz_values('ZEROS',lines)
    poles = cut_pz_values('POLES',lines)
    return sensitivity,constant,zeros,poles

#匹配文件名，方便我们打开对应的data数据文件
def match_dataname(station,lines):
    os.chdir(r"./data")
    #建立正则化规则
    dataname_pattern = re.compile(r"\S{3}"+station+r"\S{2,4}BHZ.*")
    # 根据名字打开文件：
    for file in os.listdir():
        if dataname_pattern.match(file):
            st = obspy.read(file)
            #要在这里对数据进行进一步处理，加入台站信息
            input_paz(st,lines) #   这里我们去掉台站响应参数失败了，为什么
    os.chdir(r"..")
    return st   #传出的是一个数据流

#这个函数专门用来添加仪器参数
def input_paz(st,lines):
    sensitivity, constant, zeros, poles = cut_pazvalue(lines)
    st[0].stats.paz = AttribDict({'poles': poles,
                                  'zeros': zeros,
                                  'sensitivity': constant,
                                  'gain': 1}) #==注意==：这里的gain不知道什么意思

# 这里我们写一个可以一口气读完文件夹所有地震数据的代码，同时之传出Z轴分量：
#这里我们需要接收所要读取文件的路径
def load_data(path):
    for path_state in os.walk(path):
        path_file = path_state[2]
    st = Stream()
    for data_file in path_file:
        data_filename = path + "\\" + data_file
        st+=obspy.read(data_filename)
    #这里可以选择读取输出的方向：
    st = st.select(component="Z")
    return st

#   这里计划用来获取P'P'的到时
#   st_band导入输入的数据，seismic_phase用来输入你想要获取震相类型
def get_tauptime(st_band,seismic_phase):
    #先获取地震的位置
    event_depth = st_band[0].stats.sac.evdp  # 地震深度，单位为千米
    event_latitude = st_band[0].stats.sac.evla  # 地震纬度
    event_longitude = st_band[0].stats.sac.evlo  # 地震经度
    #计算每一个台站的P'P'到时
    model = TauPyModel(model="prem")  # 使用 IASP91 地球模型
    # 计算震中距
    t = np.zeros(len(st_band),)
    num = 0 #   计数器
    for tr in st_band:
        gcarc = tr.stats.sac.gcarc  #导入震中距
        stdp = 10**(-3)*tr.stats.sac.stdp  #m换成km
        # 获取 PKPPKP 相位的理论到达时间
        arrivals = model.get_travel_times(source_depth_in_km=event_depth,
                                          distance_in_degree=gcarc,
                                          phase_list=[seismic_phase],
                                          receiver_depth_in_km=stdp)
        # 直接获取 PKPPKP 相位的理论到达时间
        pkIkppkIkp_arrival = arrivals[0].time if arrivals else None
        if pkIkppkIkp_arrival is not None:
            # 将 PKPPKP 相位的理论到达时间保存到 stats 中
            tr.stats.pkppkp_theory_time = pkIkppkIkp_arrival
            t[num] = pkIkppkIkp_arrival
        else:
            print(f"No PKIKPPKIKP arrival found for station {tr.stats.station}")
        num += 1
    return t.min()

#这里就是专门用来绘制section图的
def section_plot(st_band):
    ev_coord = (st_band[0].stats.sac.evla,st_band[0].stats.sac.evlo)
    #导入台站的必备参数lat与lon
    for tr in st_band:
        tr.stats.coordinates = AttribDict({'latitude': tr.stats.sac.stla,
                                           'longitude': tr.stats.sac.stlo})
    # #   这里我们先要进一步获取到P'P'的到时作为sac 的lh o
    # #   这里由于我们研究的对象是将P'P'作为初始震相
    # seismic_phase = "PKIKPPKIKP"
    # t0 = get_tauptime(st_band,seismic_phase)    #   获得最早到的t0  #   本次我们得知最早到时为2300s左右
    fig = plt.figure()
    st_band.plot(type='section', plot_dx=1, dist_degree=True,
                 ev_coord=ev_coord,recordstart=2100, recordlength=300,
                 time_down=False, linewidth=.25, grid_linewidth=.25, show=False, fig=fig)
    plt.xlim(78.8,83.6)
    plt.show()