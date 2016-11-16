import json
import numpy as np
import matplotlib.pyplot as plt
import time
import os
import compute_mds as mds

' 统计相关信息 '

__author__ = 'Lu Binbin'

# 节点属性对应序号
ATTR_TO_INDEX = {
    "a_deg": 0,    # 总的节点度，非时变
    "a_pub":1,        # 总的发表量，非时变
    "t_avgW":2,       # 平均边权重，时变
    "t_pub":3,        # 当年发表量，时变
    "t_deg":4,     # 当年的节点度，时变
    "t_dCent":5,   # 度中心性 节点的度/N-1  N为所有节点，时变
    "t_avgC":6,       # 邻居节点的平均度中心性，时变
    "t_cc":7,         # 聚集系数，节点的邻居之间的边与两两相连的边数（n(n-1)/2）的占比，时变
    "t_venue":8       # 文章发表在1.期刊 2.会议 3.both
    # "t_ins":9       # 机构，时变
}

class Statistic(object):
    def __init__(self, parseFile_path,node_attrs_path,graph_path, filter_conditions):
        self.records = []
        self.times = []
        self.author_to_index = {}
        self.graph = {}     # 图结构
        self.filter_node_names = set([])  # 过滤后的作者
        self.node_attrs = {}    # 存储节点属性
        self.author_immu_attrs = {}     # 保存节点的非时变属性：总发表量和合作者数量
        self.parsePath = parseFile_path
        self.graphPath = graph_path
        self.attrsPath = node_attrs_path
        self.filter_conditions = filter_conditions  # 过滤条件

        # 初始化数据
        self.init_data()

    def init_data(self):
        self.getRecords(self.parsePath)
        self.getTimes(self.records)
        self.getAuthorsToIndex(self.records)
        self.get_immutable_attr(self.records)
        self.getGraph()
        self.get_node_attrs()

        # self.generateGraph()

    def getRecords(self, path):
        with open(path,'r') as fs:
            self.records = json.load(fs)
        print("-----成功获取records！-----")

    def getTimes(self, records):
        times = set([])
        for record in records:
            t = str(record[0])
            if t not in times:
                times.add(t)
        l = list(times)
        l.sort(key=lambda x:int(x), reverse=True)
        self.times = l
        print("-----成功获取times！-----")

    def getAuthorsToIndex(self, records):
        init_index = 10000
        t_authors = {}
        for record in records:
            coAuthors = record[1].split(";")
            for name in coAuthors:
                if name == "":
                    print(record)
                if name not in t_authors:
                    t_authors[name] = init_index
                    init_index+=1

        self.author_to_index = t_authors
        if "" in t_authors:
            print(True)
        print("-----成功获取author到index的映射！-----")
        print("-----总的作者数量:%d-----"%len(t_authors.keys()))

    def isMeetCondition(self,author):
        flag = True
        a_immu_attr = self.author_immu_attrs
        conditions = self.filter_conditions
        for c in conditions:
            if a_immu_attr[author][c] < conditions[c]:
                flag = False
                break
        return flag

    def getGraph(self):
        start = time.time()
        path = self.graphPath
        times = self.times
        graph = {}
        if os.path.exists(path):
            with open(path,"r") as fs:
                graph = self.graph = json.load(fs)
        else:
            records = self.records
            graph = self.graph
            filter_names = self.filter_node_names
            # print(times)
            for t in times:
                graph[t] = {"nodes":[],"links":[]}

            for r in records:
                t = str(r[0])
                coAuthors = r[1].split(";")
                venue = r[2]
                nodes = graph[t]["nodes"]
                links = graph[t]["links"]
                filter_authors = []

                for au in coAuthors:
                    if self.isMeetCondition(au):
                        filter_authors.append(au)

                # 获取边
                self.extractRelation(filter_authors, links, venue)

                # 获取节点（包含孤立节点：即度为0）
                # for au in filter_authors:
                #     if au not in nodes:
                #         nodes.append(au)
                #         filter_names.add(au)

                # 获取节点（不包含孤立节点）
                for au in filter_authors:
                    if au not in nodes and len(filter_authors)!=1:
                        nodes.append(au)
                        filter_names.add(au)

            for t in times:
                graph[t]["nodes"] = [{"name":x} for x in graph[t]["nodes"]]

            with open(path, 'w') as fs:
                json.dump(graph,fs,ensure_ascii=False)

        # 打印每年的nodes和links数量
        for t in times:
            N_count = len(graph[t]["nodes"])
            L_count = len(graph[t]["links"])
            print("%s\t%d\t%d"%(t, N_count, L_count))

        end = time.time()
        print("----抽取图结构总共运行时间：%d 秒-----"%(end-start))

    def get_node_attrs(self):
        path = self.attrsPath
        if os.path.exists(path):
            with open(path,'r') as fs:
                self.node_attrs = json.load(fs)
        else:
            start = time.time()
            graph = self.graph
            records = self.records
            times = list(graph.keys())
            times.sort(key=lambda x:x, reverse=True)
            node_attrs = self.node_attrs


            # 初始化node_attrs
            for t in times:
                node_attrs[t] = {}
                for n in graph[t]["nodes"]:
                    name = n["name"]
                    node_attrs[t][name] = [0 for i in ATTR_TO_INDEX.keys()]

            # 计算属性
            self.getImmuAttr(node_attrs)    # 设置非时变属性, a_pub 和 a_deg
            self.get_tDeg(graph, node_attrs)   # 计算节点度
            self.get_tPub(records, node_attrs)   # 计算作者每年发表量
            self.get_tAvgWeight(graph, node_attrs)  # 计算平均边权重
            self.get_tdCent(node_attrs)    # 计算节点中心性 degree/N
            self.getAvgC(graph, node_attrs) # 计算邻居节点的平均度中心性
            self.getCC(graph, node_attrs)   # 计算节点的聚集系数
            self.getTypeVenue(records, node_attrs) # 计算节点发表类型，1 期刊 2 会议 3 混合

            #　写入文件
            with open(path, 'w') as fs:
                json.dump(node_attrs, fs, ensure_ascii=False)
            end = time.time()
            print("-----属性计算时间为：\t",end-start)

            # test
            # name = "Kwan-Liu Ma"
            # for t in times:
            #     c_node_attrs = node_attrs[t]
            #     # name = "Huamin Qu"
            #     if name in c_node_attrs:
            #         values = c_node_attrs[name]
            #         print("%s\t%d\t%d\t%.3f\t%d\t%d\t%.3f\t%.3f\t%.3f\t%d"%(t,values[0],values[1],values[2],values[3],values[4],values[5],values[6],values[7],values[8]))
            #         # print(c_node_attrs[name])
            #         # print("%s\t%d"%(t, c_node_attr[name][ATTR_TO_INDEX['t_deg']]))
            #
            # self.test(graph,name,node_attrs)


    def test(self,graph,name,node_attrs):
        # index = ATTR_TO_INDEX[attr]
        times = self.times
        attrs = {}
        for t in times:

            if name in node_attrs[t]:
                attrs[t] = 0
                nodes = graph[t]["nodes"]
                links = graph[t]["links"]
                n_count = len(node_attrs[t].keys())
                degree = 0
                sumW = 0
                sumBet = 0
                coAuthors = set([])
                # for l in links:
                #     source,target,weight = l["source"], l["target"], l["weight"]
                #     if name == source or name == target:
                #         degree+=1
                #         sumW+=weight
                for l in links:
                    source,target = l["source"], l["target"]
                    if name == source:
                        coAuthors.add(target)
                        degree+=1
                    if name == target:
                        coAuthors.add(source)
                        degree+=1

                for l in links:
                    source,target = l["source"], l["target"]
                    if source in coAuthors and target in coAuthors:
                        sumBet+=1
                if degree > 1:
                    allBet = degree*(degree-1)/2
                    attrs[t] = round(sumBet/allBet,3)
                else:
                    attrs[t] = 0
                print("%s\t%d\t%.3f"%(t,degree,attrs[t]))


    def get_tDeg(self,graph,node_attrs):
        index = ATTR_TO_INDEX['t_deg']
        for t in graph:
            nodes = graph[t]["nodes"]
            links = graph[t]["links"]
            c_node_attrs = node_attrs[t]
            for l in links:
                source = l["source"]
                target = l["target"]
                c_node_attrs[source][index]+=1
                c_node_attrs[target][index]+=1

    def get_tPub(self,records, node_attrs):
        index = ATTR_TO_INDEX['t_pub']
        # for time in node_attrs:
        #     print(time)
        for record in records:
            t = str(record[0])
            authors = record[1].split(";")
            c_node_attrs = node_attrs[t]
            for a in authors:
                if a in c_node_attrs:
                    c_node_attrs[a][index]+=1
                # attrs_values = c_node_attrs[a]
                # attrs_values[index]+=1

    def get_tAvgWeight(self,graph,node_attrs):
        index = ATTR_TO_INDEX["t_avgW"]
        t_deg_index = ATTR_TO_INDEX["t_deg"]
        for t in graph:
            nodes = graph[t]["nodes"]
            links = graph[t]["links"]
            c_node_attrs = node_attrs[t]
            author_to_weight = {}
            for n in node_attrs[t]:
                author_to_weight[n] = 0

            for l in links:
                source,target,weight = l["source"], l["target"], l["weight"]
                author_to_weight[source]+=weight
                author_to_weight[target]+=weight
            for author in node_attrs[t]:
                values = c_node_attrs[author]
                degree = values[t_deg_index]
                if degree > 0:
                    avgWeight = (author_to_weight[author])/degree
                    values[index] = round(avgWeight,3)

    def get_tdCent(self, node_attrs):
        index = ATTR_TO_INDEX["t_dCent"]
        deg_index = ATTR_TO_INDEX['t_deg']

        for t in node_attrs:
            c_node_attrs = node_attrs[t]
            Num_nodes = len(c_node_attrs.keys())
            for author in c_node_attrs:
                values = c_node_attrs[author]
                values[index] = round(values[deg_index]*100/Num_nodes,3)

    def getAvgC(self,graph,node_attrs):
        index = ATTR_TO_INDEX['t_avgC']
        t_deg_index = ATTR_TO_INDEX['t_deg']
        t_dCent_index = ATTR_TO_INDEX['t_dCent']
        for t in graph:
            c_node_attrs = node_attrs[t]
            links = graph[t]["links"]
            author_to_central = {}
            for n in c_node_attrs:
                author_to_central[n] = 0
            for l in links:
                source, target = l["source"],l["target"]
                sCentral = c_node_attrs[source][t_dCent_index]
                tCentral = c_node_attrs[target][t_dCent_index]
                author_to_central[source]+=tCentral
                author_to_central[target]+=sCentral
            for n in c_node_attrs:
                values = c_node_attrs[n]
                degree = values[t_deg_index]
                if degree > 0:
                    values[index] = round(author_to_central[n]/degree,3)

    def getCC(self,graph,node_attrs):
        index = ATTR_TO_INDEX["t_cc"]
        t_deg_index = ATTR_TO_INDEX["t_deg"]
        for t in graph:
            links = graph[t]["links"]
            c_node_attrs = node_attrs[t]
            for n in c_node_attrs:
                values = c_node_attrs[n]    # 某个节点的属性值列表
                degree = values[t_deg_index]
                if degree > 1:  # 只要当度大于1时需要计算，否则聚集系数为0
                    sum = 0     # 记录某个节点的邻居节点之间的边数
                    coAuthors = set([]) # 记录某个节点的所有邻居
                    # 得到coAuthors
                    for l in links:
                        source,target = l["source"],l["target"]
                        if source == n:
                            coAuthors.add(target)
                        if target == n:
                            coAuthors.add(source)
                    # 计算coAuthors中存在的边，即邻居之间的边
                    for l in links:
                        source,target = l["source"],l["target"]
                        if source in coAuthors and target in coAuthors:
                            sum+=1
                    values[index] = round(sum/(degree*(degree-1)/2),3)   # 聚集系数


    def getTypeVenue(self,records,node_attrs):
        index = ATTR_TO_INDEX["t_venue"]
        node_to_venue = {}
        for t in node_attrs:
            node_to_venue[t] = {}
            for n in node_attrs[t]:
                node_to_venue[t][n] = set([])

        for record in records:
            t = str(record[0])
            authors = record[1].split(";")
            key = record[2]
            venue = "J" if key.startswith("journals") else "C"
            for au in authors:
                if au in node_attrs[t]:
                    node_to_venue[t][au].add(venue)
        for t in node_attrs:
            c_node_attrs = node_attrs[t]
            for n in c_node_attrs:
                values = c_node_attrs[n]
                venueList = list(node_to_venue[t][n])
                if len(venueList) == 2:
                    values[index] = 3
                elif venueList[0] == "J":
                    values[index] = 1
                else:
                    values[index] = 2

    def getImmuAttr(self,node_attrs):
        a_pub_index = ATTR_TO_INDEX['a_pub']
        a_deg_index = ATTR_TO_INDEX['a_deg']
        author_immu_attrs = self.author_immu_attrs
        for t in node_attrs:
            for n in node_attrs[t]:
                values = node_attrs[t][n]
                values[a_pub_index] = author_immu_attrs[n]["a_pub"]
                values[a_deg_index] = author_immu_attrs[n]["a_deg"]


    def get_immutable_attr(self, records):
        author_to_pub = {}
        author_to_author = {}
        author_immu_attrs = self.author_immu_attrs
        allAuthors = list(self.author_to_index.keys())
        for name in allAuthors:
            author_to_pub[name] = 0
            author_to_author[name] = set([])
            author_immu_attrs[name] = {"a_pub":0,"t_deg":0}

        for r in records:
            coAuthors = r[1].split(";")
            # 统计总发表量
            for au in coAuthors:
                author_to_pub[au] += 1

            # 统计总的合作者数量
            for (i,au1) in enumerate(coAuthors):
                for (j,au2) in enumerate(coAuthors):
                    author_to_author[au1].add(au2)
                    author_to_author[au2].add(au1)

        # 将数据存入模型
        for name in allAuthors:
            author_immu_attrs[name]['a_pub'] = author_to_pub[name]
            author_immu_attrs[name]['a_deg'] = len(author_to_author[name])



    # 抽取合作关系
    def extractRelation(self,authors,links,venue):
        # 作者数小于2时，不存在边
        if len(authors) < 2:
            return 0
        for (i,v1) in enumerate(authors):
            for (j,v2) in enumerate(authors):
                if j>i:
                    isExsit = False
                    n_relation = {}
                    n_relation["source"] = v1
                    n_relation["target"] = v2
                    n_relation["weight"] = 1
                    n_relation["venues"] = [venue]
                    if links != []:
                        for link in links:
                            source = link["source"]
                            target = link["target"]
                            weight = link["weight"]
                            venues = link["venues"]
                            if (v1 == source and v2 == target) or (v1 == target and v2 == source):
                                link["weight"] = weight+1
                                if venue not in venues:
                                    venues.append(venue)
                                isExsit = True
                                break
                    if isExsit == False:
                        links.append(n_relation)

    def drawSpecialNode(self, author, attrName):
        index = ATTR_TO_INDEX[attrName]
        node_attrs = self.node_attrs
        times = self.times
        times.sort(key=lambda x:int(x))
        drawData = []
        for t in times:
            if author in node_attrs[t]:
                values = node_attrs[t][author]
                drawData.append([t, values[index]])

        for item in drawData:
            print(item[0],attrName,item[1])

        self.draw(drawData, attrName)

    def draw(self, data, attrName):
        times = [x[0] for x in data]
        length = len(times)
        width = 0.5
        X = np.arange(length)+1
        Y = [x[1] for x in data]

        fig = plt.figure()
        plt.subplots_adjust(bottom = 0.15)
        ax = fig.add_subplot(111)

        ax.bar(X-width/2,Y,width,color="green")
        ax.set_xlabel("年份")
        ax.set_ylabel(attrName)
        ax.set_xticks(X)
        ax.set_xticklabels(times,rotation=-60)
        # ax.set_title("nodes change")
        plt.title(attrName+" 随时间演化趋势图")
        plt.grid(True)
        plt.show()

def drawScatterPlot(data):
    times = [x[0] for x in data]
    length = len(times)
    width = 0.3
    X = np.arange(length)+1
    NY = [x[1] for x in data]
    LY = [x[2] for x in data]

    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.bar(X-width/2,NY,width,color="green")
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")
    ax.set_xticks(X)
    ax.set_xticklabels(times)
    # ax.set_title("nodes change")
    # plt.title("bar chart")
    plt.grid(True)

    plt.show()

if __name__ == "__main__":
    start = time.time()

    parse_path = "./result_data/parse_result.json"      # 解析文件路径
    node_attrs_path = "./unfilter_result_data/node_attrs.json"   # 节点属性存放路径
    graph_path = "./unfilter_result_data/graph.json"             # 图结构存放路径（边属性在图结构中）
    similarity_path = "./unfilter_result_data/similarity.json"   # 相似度文件
    mds_path = "./unfilter_result_data/mds.json"                 # 降维结果文件路径
    filter_conditions = {"a_pub":1}                     # 过滤条件

    # 创建实例
    instance = Statistic(parse_path,node_attrs_path,graph_path,filter_conditions)

    # instance.drawSpecialNode("Kwan-Liu Ma", "t_pub")
    mds.cal_mds(mds_path, similarity_path, graph_path, node_attrs_path, ATTR_TO_INDEX)

    # mds.drawMDS(mds_path, "2014")
    end = time.time()
    print("-----总运行时间：%d-----" %(end-start))
