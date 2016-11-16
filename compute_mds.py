import json
import os
import time
import numpy as np
from sklearn import manifold
import random
import matplotlib.pyplot as plt


'''
    graphPath: 图结构文件路径
    attrsPath: 节点属性文件路径
    attrs: 属性dict {name：index}
'''

def cal_similarity(graphPath, attrsPath,similarityPath, attrs):
    # 使用切比雪夫距离计算邻接矩阵
    start = time.time()
    print("start compute........")
    graph = {}
    node_attrs = {}
    total_similarity = {}

    if os.path.exists(graphPath) and os.path.exists(attrsPath):
        with open(graphPath, 'r') as fs:
            graph = json.load(fs)
        with open(attrsPath, 'r') as fs:
            node_attrs = json.load(fs)

        times = list(graph.keys())
        times.sort(key=lambda x:int(x))

        for t in times:
            print(t)
            effection = {}
            for i in attrs:
                 effection[i] = 0
            nodes = graph[t]["nodes"]
            simi = [[0 for y in nodes] for x in nodes] # 初始化一个二维列表
            c_node_attrs = node_attrs[t]
            for i,n1 in enumerate(nodes):
                for j,n2 in enumerate(nodes):
                    if i<j:
                        simi[i][j] = simi[j][i] = compute_bettwen(c_node_attrs[n1["name"]], c_node_attrs[n2["name"]],attrs,effection)

            total_similarity[t] = simi

            # print("%s年各指标影响力如下："%t)
            # sum = 0
            # for attr in effection:
            #     sum+=effection[attr]
            # for attr in effection:
            #     percent = round(effection[attr]*100/sum,2)
            #     print(attr,":",percent,"%")
        print("正在写人similarity......")
        with open(similarityPath, 'w') as fs:
            json.dump(total_similarity, fs)
        print("写入similarity成功。.....")
        end = time.time()

        print("end computing: ",end-start)
        return total_similarity

    else:
        print("error: 文件不存在或者读取文件错误！")
        return



'''
    计算两个节点间的相似度
    values_1,values_2:属性值列表
    attrs: 属性dict {name：index}
'''
def compute_bettwen(values_1,values_2, attrs,effection):

    similarity = 0
    for k,i in attrs.items():
        top = abs(values_1[i]-values_2[i])
        bottom = values_1[i]+values_2[i]
        if bottom == 0:
            continue
        else:
            similarity+= round(top/bottom,6)
            # effection[k]+=round(top/bottom,6)
    return similarity

'''
    进行mds降维:二维
'''
def cal_mds(mdsPath, similarityPath, graphPath, attrsPath, attrs):
    start = time.time()
    similarity_m = {}
    positions = {}
    # similarityPath = "./result_data/similarity_demo.json"
    if os.path.exists(similarityPath):
        with open(similarityPath, "r") as fs:
            similarity_m =json.load(fs)
    else:
        similarity_m = cal_similarity(graphPath, attrsPath, similarityPath,attrs)

    times = list(similarity_m.keys())
    times.sort(key=lambda x:int(x))

    mds = manifold.MDS(n_components=2, max_iter=300,
                       dissimilarity="precomputed", n_jobs=1)

    print("开始MDS计算.........")
    for t in times:
        print(t)
        sm = np.asarray(similarity_m[t])
        pos = mds.fit(sm).embedding_
        positions[t] = pos.tolist()

    end = time.time()
    print("结束MDS计算:",end-start)

    with open(mdsPath, 'w') as fs:
        json.dump(positions, fs)
    print("成功写入文件")
'''
    随机生成邻接矩阵
'''
def generateRandomMatrix():
    times = [str(x) for x in range(1995,2000)]
    similarity_m = {}
    for t in times:
        n = random.randint(50,100)
        l = range(n)
        simi = [[0 for y in l] for x in l]
        for i in l:
            for j in l:
                if i<j:
                    simi[i][j]=simi[j][i] = random.uniform(0,2)
        similarity_m[t] = simi
    with open("./result_data/similarity_demo.json", 'w') as fs:
        json.dump(similarity_m,fs)

def drawMDS(path, t):
    t_mds = {}
    with open(path, 'r') as fs:
        t_mds = json.load(fs)
    positions = t_mds[t]

    X = [x[0] for x in positions]
    Y = [x[1] for x in positions]

    plt.figure(1)
    axes = plt.subplot(111)

    axes.scatter(X,Y,c='red',s=20)
    plt.xlabel("x-axis")
    plt.ylabel("y-axis")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    generateRandomMatrix()

    print(times)
