import json

RCMImageList = ["RCM1_OK1690945_PK1913667_1_5M3_20211204_015023_HH_SLC.zip",
                "RCM1_OK1957510_PK2044513_1_5M3_20220403_015020_HH_SLC.zip",
                "RCM1_OK1957510_PK2057501_1_5M3_20220415_015020_HH_SLC.zip",
                "RCM1_OK1957510_PK2071103_1_5M3_20220427_015021_HH_SLC.zip",
                "RCM1_OK1957510_PK2084657_1_5M3_20220509_015022_HH_SLC.zip",
                "RCM1_OK1957510_PK2097086_1_5M3_20220521_015022_HH_SLC.zip",
                "RCM1_OK1957510_PK2110801_1_5M3_20220602_015023_HH_SLC.zip",
                "RCM1_OK1957510_PK2126876_1_5M3_20220614_015023_HH_SLC.zip",
                "RCM1_OK1957510_PK2139341_1_5M3_20220626_015025_HH_SLC.zip",
                "RCM2_OK1460936_PK1612616_1_5M3_20210506_015027_HH_SLC.zip",
                "RCM2_OK1539919_PK1704114_1_5M3_20210717_015032_HH_SLC.zip",
                "RCM2_OK1539919_PK1733608_1_5M3_20210810_015033_HH_SLC.zip",
                "RCM2_OK1539919_PK1764340_1_5M3_20210903_015035_HH_SLC.zip",
                "RCM2_OK1784756_PK1784773_1_5M3_20210810_015033_HH_SLC.zip",
                "RCM2_OK1784756_PK1784774_1_5M3_20210717_015032_HH_SLC.zip",
                "RCM2_OK1784756_PK1784775_1_5M3_20210903_015035_HH_SLC.zip",
                "RCM2_OK1802410_PK1943968_1_5M3_20220101_015033_HH_SLC.zip",
                "RCM2_OK1802410_PK1955735_1_5M3_20220113_015033_HH_SLC.zip",
                "RCM2_OK1802410_PK1967883_1_5M3_20220125_015032_HH_SLC.zip",
                "RCM2_OK1802410_PK1979219_1_5M3_20220206_015032_HH_SLC.zip",
                "RCM2_OK1802410_PK1991371_1_5M3_20220218_015031_HH_SLC.zip",
                "RCM2_OK1802410_PK2004370_1_5M3_20220302_015031_HH_SLC.zip",
                "RCM2_OK1802410_PK2016337_1_5M3_20220314_015031_HH_SLC.zip",
                "RCM2_OK1957510_PK2061859_1_5M3_20220419_015032_HH_SLC.zip",
                "RCM3_OK1460936_PK1542640_1_5M3_20210404_015037_HH_SLC.zip",
                "RCM3_OK1460936_PK1577282_1_5M3_20210416_015038_HH_SLC.zip",
                "RCM3_OK1460936_PK1618048_1_5M3_20210510_015039_HH_SLC.zip",
                "RCM3_OK1460936_PK1634298_1_5M3_20210522_015040_HH_SLC.zip",
                "RCM3_OK1460936_PK1647481_1_5M3_20210603_015040_HH_SLC.zip",
                "RCM3_OK1460936_PK1666012_1_5M3_20210615_015041_HH_SLC.zip",
                "RCM3_OK2042899_PK2166542_1_5M3_20220716_015049_HH_SLC.zip",
                "RCM3_OK2042899_PK2181926_1_5M3_20220728_015050_HH_SLC.zip",
                "RCM3_OK2042899_PK2200409_1_5M3_20220809_015050_HH_SLC.zip",
                "RCM3_OK2042899_PK2217084_1_5M3_20220821_015051_HH_SLC.zip",
                "RCM3_OK2042899_PK2234922_1_5M3_20220902_015052_HH_SLC.zip",
                "RCM3_OK2042899_PK2255962_1_5M3_20220914_015052_HH_SLC.zip"]

records = []
for s in RCMImageList:
    date = s.split('_')[5]
    date = f'{date[0:4]}-{date[4:6]}-{date[6:8]}'
    record = {"resource_uri": f"s3://vrrc-rcm-raw-data-store/Meager/5M3/{s}",
              "target": "A4202_Volcano_Garbld",
              "date": f"{date}",
              "source_uri": "",
              "beam": "5M3",
              "status": "success",
              "status_info": "",
              "footprint": {"type": "MultiPolygon",
                            "coordinates": [[[[-123.8076462857, 50.4841133947],
                                              [-123.3779793776, 50.5424154900],
                                              [-123.4486311113, 50.7519778705],
                                              [-123.8803636317, 50.6935295004]
                                              ]]]},
              "percent_overlap": 95.0}
    records.append(record)

json_data = json.dumps(records)
with open("singleLookComplex.json", "w") as outfile:
    json.dump(records, outfile, indent=4, separators=(',', ':'))
