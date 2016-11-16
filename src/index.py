
from xml.sax import handler, make_parser
import json
import re
import time
import lib.parse_dblp_xml as dblpParse
import lib.stat_measure as sm
import lib.compute_mds as mds

'''
    --- 过滤条件 ---
    CHOOSE_VENUES:需要选择的期刊或者会议的key值（文章key值得前半部分，一般是 journals或者conf + 期刊或者会议简写）
    FILTER_TIME: 解析时的过滤时间，只取时间大于或等于该时间段的文章
    GRAPH_FILTER_CONDITION：抽取网络结构时的过滤条件
'''
CHOOSE_VENUES = dblpParse.CHOOSE_VENUES
FILTER_TIME = 1990
GRAPH_FILTER_CONDITION = sm.FILTER_CONDITION


ATTR_TO_INDEX = sm.ATTR_TO_INDEX    # 所有节点属性

'''
    文件路径
'''
SOUCE_FILE_PATH = "../dblp.xml"                # 需要解析的dblp.xml文件路径
PARSED_FILR_PATH = "../parse_result.json"      # 解析后的文件路径，文件中每条记录是一个list（一篇文章），包含字段 1时间 2作者 3期刊会议信息
GRAPH_PATH = "../result_data/graph.json"            # 抽取的网络结构信息文件路径， 其中包含了边属性，按年存储
NODE_ATTRS_PATH = "../result_data/node_attrs.json"  # 网络节点属性信息文件路径 ，按年存储，属性包含时变属性和非时变属性
SIMILARITY_PATH = "../result_data/similarity.json"  # 每年的节点相似度矩阵文件路径
MDS_PATH = "../result_data/mds.json"                # mds降维结果路径
SPE_CHARA_PATH = "../specialCharacter.json"         # 特殊字符对应文件



if __name__ == "__main__":
    # 解析dblp文件，存入PARSED_FILR_PATH路径，
    # dblpParse.parse(SOUCE_FILE_PATH, PARSED_FILR_PATH,SPE_CHARA_PATH, CHOOSE_VENUES, FILTER_TIME)

    #　从解析后的dblp文件中抽取网络结构，并计算相关节点属性(ATTR_TO_INDEX),生成网络结构文件和节点属性文件
    instance = sm.Statistic(PARSED_FILR_PATH, NODE_ATTRS_PATH, GRAPH_PATH, GRAPH_FILTER_CONDITION)

    # 计算相似度矩阵并j计算mds降维结果，返回降维结果
    # mds_positions = mds.cal_mds(MDS_PATH, SIMILARITY_PATH, GRAPH_PATH, NODE_ATTRS_PATH, ATTR_TO_INDEX)
    # mds.drawMDS(MDS_PATH, 2010)   # 绘图
