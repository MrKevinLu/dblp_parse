
from xml.sax import handler, make_parser
import json
import re
import time
# from pymsql

# 所有作者信息都在以这些根标签内部
paper_tag  =['article','inproceedings','proceedings','book',
                    'incollection','phdthesis','mastersthesis','www']
# 选择的期刊或者会议
# 包括 CHI，VAST, TVCG, PacificVis， InfoVis，EuroVis，Information Visualization（期刊）
choose_venues = ['conf/chi/','conf/ieeevast/','journals/tvcg/','conf/apvis/','conf/infovis/','conf/vissym/','journals/cgf/','journals/ivs/','conf/jvis/','journals/vc/']



class mHandler(handler.ContentHandler):
    def __init__(self):
        self.topTag = ""
        self.CurrentTag = ""
        self.key = ""
        self.author = []
        self.year = ""
        self.extentYear = []
        self.journal = ""
        self.title = ""
        self.booktitle = ""
        self.year_nodes = {}  # 存储作者和发表量
        self.count = 0  # 存储总的论文数
        self.author_index = {}
        self.init_index = 10000
        self.year_relations = {}
        with open("specialCharacter.json",'r') as fs:
            # 特殊字符
            self.specialC = json.load(fs)

    def startDocument(self):
        print('Document Start')

    def endDocument(self):
        # 将结果数据输出到文件
        print(time.time())
        with open("./result_data/nodes.json","w") as fs:
            # l = list(self.year_nodes.items())
            # l.sort(key=lambda x:x[1], reverse=True)
            json.dump(self.year_nodes,fs,ensure_ascii=False)

        with open("./result_data/relations.json",'w') as fs:
            json.dump(self.year_relations, fs,ensure_ascii=False)

        # 作者姓名与id对应关系
        with open("./result_data/author_index.json",'w') as fs:
            json.dump(self.author_index,fs, ensure_ascii=False)

        print('Document End')
        self.extentYear.sort()
        print("时间范围：",min(self.extentYear),"--",max(self.extentYear))
        print("范围：",self.extentYear)
        print("总文章数：",self.count)
        print("总作者数：",len(self.author_index.keys()))

        # self.extentYear.sort()
        # print(self.extentYear)

    def startElement(self, tag, attrs):

        self.CurrentTag = tag # 当前标签类型

        #　记录下顶级标签类型
        if tag in paper_tag:
            self.topTag = tag
            self.key = attrs["key"]

    def endElement(self, tag):
        # 判断是否类似article的跟标签结束并且发表时间在1988年之后，若结束，则将数据存进模型中
        # print(self.year)
        if tag == self.topTag :
            if self.year !="" and self.year >= 1990 and self.author != []:
                # 一条记录访问结束，插入数据库
                for venue in choose_venues:
                    if self.key.find(venue) > -1:
                        authors = self.author
                        result = self.year_nodes
                        year = self.year
                        author_index = self.author_index
                        # 修正姓名
                        for (i,name) in enumerate(authors):
                            authors[i] = self.exchangeName(name)

                        self.count = self.count+1   # 文章数量
                        # self.relations = self.relations+self.computeRelation(len(self.author))  # 合作数量

                        for name in authors:
                            result[name] = 1 if name not in result else result[name]+1
                            if name not in author_index:
                                author_index[name] = self.init_index
                                self.init_index +=1

                        self.extractRelation(authors, year)  # 抽取关系存入year_relations
                        break
            # 重新初始化
            self.topTag = ""
            self.CurrentTag = ""
            self.author = []
            self.year = ""
            self.journal = ""
            self.title = ""
            self.key = ""
            # print("end tag")

    def characters(self, chrs):
        tag = self.CurrentTag
        if chrs.strip()!="":
            if tag == "author":
                self.author.append(chrs.strip())
            elif tag == "year":
                self.year = int(chrs)
                if (self.year not in self.extentYear) and (self.year>=1990):
                    self.extentYear.append(self.year)
            elif tag == "journal":
                self.journal = chrs
            elif tag == "title":
                self.title = chrs
            elif tag == "booktitle":
                self.booktitle = chrs

    # 拥有特殊字符的名字替换
    def exchangeName(self,name):
        matchStrs = re.findall(r',.{4,9};',name)
        for s in matchStrs:
            if s in self.specialC:
                name = name.replace(s,self.specialC[s])
        return name

    def extractRelation(self,authors,year):
        if len(authors)<=1:
            return 0

        relations = self.year_relations

        for (i,v1) in enumerate(authors):
            for (j,v2) in enumerate(authors):
                if j>i:
                    isExsit = False
                    n_relation = {}
                    n_relation["source"] = v1
                    n_relation["target"] = v2
                    n_relation["weight"] = 1
                    if year not in relations:
                        relations[year] = []
                    else:
                        for relation in relations[year]:
                            source = relation["source"]
                            target = relation["target"]
                            weight = relation["weight"]
                            if self.isExsit(v1,v2,source,target):
                                relation["weight"] = weight+1
                                isExsit = True
                                break
                    if isExsit == False:
                        relations[year].append(n_relation)



    def isExsit(self,v1,v2,source,target):
        flag = True if (v1 == source and v2 == target) or (v1 == target and v2 == source) else False
        return flag


def parseDblpXml():
    handler = mHandler()
    parser = make_parser()
    # parser.setFeature(handler.feature_namespaces, 0)

    parser.setContentHandler(handler)
    with open("../dblp.xml",'r') as fs:
        parser.parse(fs)

if __name__ == "__main__":

    start = time.time() # 开始时间
    parseDblpXml()      # 解析xml
    end = time.time()  # 结束时间
    print("运行时间为：",end-start)
