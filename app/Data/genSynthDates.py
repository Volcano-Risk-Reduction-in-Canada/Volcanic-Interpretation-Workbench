a = ['2022-03-02',
     '2022-03-06',
     '2022-03-10',
     '2022-03-14',
     '2022-03-18',
     '2022-03-22',
     '2022-03-26',
     '2022-03-30',
     '2022-04-03',
     '2022-04-07',
     '2022-04-11',
     '2022-04-15',
     '2022-04-19',
     '2022-04-23',
     '2022-04-27',
     '2022-05-01']

b = ['2022-03-02',
     '2022-03-06',
     '2022-03-10',
     '2022-03-14',
     '2022-03-18',
     '2022-03-22',
     '2022-03-26',
     '2022-03-30',
     '2022-04-03',
     '2022-04-07',
     '2022-04-11',
     '2022-04-15',
     '2022-04-19',
     '2022-04-23',
     '2022-04-27',
     '2022-05-01']

c = list(itertools.product(a, b))

c = []

for x in a:
    for y in b:
        if x==y:
            print('Same Date')
        else:
            c.append([x,y])


for i in range(240):
     print(random.random())

where cohMtx.ROW.INDEX == cohDf.ROW.INDEX insert into cohMtx['Coherence'].value from cohDf.['Coherence'].value

cohMtx.loc[:, 'Coherence'] = cohDf['Coherence']

