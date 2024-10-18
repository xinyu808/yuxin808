import os
import re
import obspy
from obspy.core.stream import Stream


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
def cut_pzvalues(section_header,lines):
    #这里用于匹配poles和zeros的规则。
    section_pattern = re.compile(rf'{section_header}\s+\d+\n((\s+\S+\s+\S+\s+\n)+)')
    match = section_pattern.search(lines)
    if match:
        values = []
        for line in match.group(1).strip().split('\n'):
            parts = line.strip().split()
            real_part = float(parts[0])
            imag_part = float(parts[1])
            values.append((real_part, imag_part))
        return values
    else:
        return []

def cut_pazvalue(lines):
    #提取SENSITIVITY值
    sensitivity_pattern = re.compile(r'SENSITIVITY\s+:\s+(\S+)')
    sensitivity_match = sensitivity_pattern.search(lines)
    sensitivity = float(sensitivity_match.group(1))

    #提取CONSTANT值
    constant_pattern = re.compile(r'CONSTANT\s+(\S+)')
    constant_match = constant_pattern.search(lines)
    constant = float(constant_match.group(1))

    #提取POLES和ZEROS值
    zeros = cut_pzvalues('ZEROS',lines)
    poles = cut_pzvalues('POLES',lines)
    return sensitivity,constant,zeros,poles

#匹配文件名，方便我们打开对应的data数据文件
def match_dataname(station):
    os.chdir(r"./data")
    #建立正则化规则
    dataname_pattern = re.compile(r"\S{3}"+station+r"\S{2,4}BHZ.*")
    # 根据名字打开文件：
    for file in os.listdir():
        if dataname_pattern.match(file):
            st = obspy.read(file)
    os.chdir(r"..")
    return st   #传出的是一个数据流

# #这个函数专门用来添加仪器参数
# def