from bs4 import BeautifulSoup
import requests
import os
import re

ref = "http://nucleardata.nuclear.lu.se/toi/nuclide.asp?iZA=550134"
page = requests.get(ref)

status = str(page.status_code)

def parse_row(row):
    print(row.replace('<',''))


# data format for Sqlite:
# columns (data type)
# 1. name           (text)
# 2. charge         (int)
# 3. mass           (int)
# 4. t_half(s)      (float)
# 5. html(toi page) (ascii)
# 6. Gamma table    (ascii)
# 7. X-ray table    (ascii)
# 8. Beta table     (ascii)

class TORI_Record():
    def __init__(self, url):
        """
        data format for Sqlite database:
        columns (data type)
        1. name           (text)
        2. charge         (int)
        3. mass           (int)
        4. t_half(s)      (float)
        5. html(toi page) (ascii)
        6. Gamma table    (ascii)
        7. X-ray table    (ascii)
        8. Beta table     (ascii)
        """
        self.url = url

        self.page_flag = False
        self.mass_flag = False
        self.charge_flag=False
        self.name_flag = False
        self.t_h_flag  = False
        self.g_tab_flag= False
        self.x_tab_flag= False
        self.b_tab_flag= False
        #self.half_time = self.get

        any_number_pattern = "(-*)([\d]+)(\.*)([\d]*)(E*)(e*)(D*)(d*)([+]*)([-]*)([\d]*)"
        self.any_number = re.compile(any_number_pattern)

        self.page = requests.get(url)
        self.soup = BeautifulSoup(self.page.content, 'html.parser')
        self.init_()


    def parse_table(self, table):
        rows = table.find_all('tr')
        heads = []
        data = []
        for row in rows:
            head_ = [i.text.split('\xa0') for i in row.find_all('th')]
            data_ = [i.text.split('\xa0') for i in row.find_all('td')]
            heads.append(head_)
            data.append(data_)
        return heads, data


    def __str__(self):
        return self.soup.prettify()


    def init_(self):

        def get_next_data_line(data, i):
            if i >=  len(data):
                return None
            elif len(data[i]) < 3:
                return None
            else:
                d = data[i]
                a1 = d[0][0].replace(',', '.')
                a1 = re.search(self.any_number, a1)
                a1 = float(a1[0])
                a2 = d[1][0].replace(',', '.')
                a2 = re.search(self.any_number, a2)
                a2 = float(a2[0])
                a3 = d[2][0] + d[2][1]
            return a1, a2, a3

        if str(self.page.status_code)[0] != '2':
            print("Error page download: %s"%self.url)
        else:
            tables = self.soup.find_all("table")
            heads = []
            data = []
            for table in tables:
                heads_, data_ = self.parse_table(table)
                for h in heads_:
                    h = str(h).replace(']', '').replace('[', '').replace("'", '').split(', ')  # merge lists
                    heads.append(h)
                for d in data_:
                    data.append(d)
            #print(data)
            i = 0
            while i < len(data):
                h = heads[i]
                #print(h, data[i])
                if "Half life: " in h:
                    self.half_life = data[i]
                    self.charge = heads[i - 2][0]  # [0]
                    self.mass =   heads[i - 3][0]  # [0]
                    self.name =   heads[i - 3][1]  # [1]

                if "Gammas from" in h[0]:
                    print("----------------------------------------------------")
                    gamma = []
                    i += 3     # skip header
                    d = get_next_data_line(data, i)
                    while d is not None:
                        gamma.append(d)
                        i += 1
                        d = get_next_data_line(data, i)
                    i -= 1
                if "X-rays from" in h[0]:
                    print("----------------------------------------------------")
                    xray = []
                    i += 3     # skip header
                    d = get_next_data_line(data, i)
                    while d is not None:
                        xray.append(d)
                        i += 1
                        d = get_next_data_line(data, i)
                    i -= 1
                if "Betas from" in h[0]:
                    print(" ----------------------------------------------------")
                    beta = []
                    i += 3     # skip header
                    d = get_next_data_line(data, i)
                    while d is not None:
                        beta.append(d)
                        i += 1
                        d = get_next_data_line(data, i)
                    i -= 1
                i += 1
            print('gamma', gamma)
            print('xrays', xray)
            print('beta', beta)
            #print(len(heads[1]))
            """
            for i in range(len(tables)):
                table = tables[i]
                rows = table.find_all('tr')
                heads = []
                data =[]
                j = 0
                while j < len(rows):

                    if self.t_h_flag is False:
                        row = rows[j]
                        head_ = [i.text for i in row.find_all('th')]
                        data_ = [i.text for i in row.find_all('td')]
                        heads.append(head_)
                        data.append(data_)
                        if len(head_) > 0:
                            if len(re.findall("Half life: ", head_[0])) > 0:
                                self.half_life = data_[0].split('\xa0')
                                self.t_h_flag = True
                                self.charge = heads[j-2][0]#[0]
                                self.mass   = heads[j-3][0]#[0]
                                self.name   = heads[j-3][1]#[1]
            """
            """
                    if self.g_tab_flag is False:
                        row = rows[j]
                        head_ = [i.text for i in row.find_all('th')]
                        data_ = [i.text for i in row.find_all('td')]
                        heads.append(head_)
                        data.append(data_)
                        if len(head_) > 0:
                            if len(re.findall("Gammas from ", head_[0])) > 0:
                                gamma_table = []
                                self.g_tab_flag = True
                        print(data_)
            """
                    #j += 1

            "X-rays from"
            "Betas from"
            "Gammas from"
            #print(tables[1])



ref = "http://nucleardata.nuclear.lu.se/toi/nuclide.asp?iZA=550134"
t = TORI_Record(ref)
print(t.half_life, t.charge, t.mass,  t.name)
#print(t)

"""
if status[0] == '2': # successfully downloaded
    print("successfully downloaded\n")
    #print(page.content)
    soup = BeautifulSoup(page.content, 'html.parser')
    #print(soup.prettify())
    #table = soup.find('table')
    tables = soup.find_all("table")
    for t in tables:
        rows = t.find_all('tr')
        for row in rows:
            #parse_row(row)
            head_ = [i.text for i in row.find_all('th')]
            data_ = [i.text for i in row.find_all('td')]
            #print(head_, data_)
            if len(head_) > 0:
                if len(re.findall("Half life: ", head_[0]))> 0:
                    print("--------------------------------------------")
    print(len(tables))

    #rows = table.find_all('tr')
    #for row in rows:
    #    print(row)

#soup = BeautifulSoup(page.content, 'html.parser')
#ref = "http://nucleardata.nuclear.lu.se/toi/nuclide.asp?iZA=550134"
#with open(ref) as fp:
#    soup = BeautifulSoup(fp)

#soup = BeautifulSoup("<html>data</html>")
#print(soup)
"""