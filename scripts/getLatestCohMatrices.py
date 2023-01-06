import boto3
import configparser
import os
import yaml


def main():

    config = get_config_params("config.ini")
    s3 = boto3.client('s3')

    os.chdir('../app/Data/')

    with open('beamList.yml') as beamListYML:
        beamList = yaml.safe_load(beamListYML)
    for site in beamList:
        for beam in beamList[site]:
            print(f'Site: {site}, Beam: {beam}')
            if not os.path.exists(f'{site}/{beam}'):
                os.makedirs(f'{site}/{beam}')

            s3.download_file(Bucket=config.get('AWS', 'bucketName'),
                     Key=f'{site}/{beam}/CoherenceMatrix.csv',
                     Filename=f'{site}/{beam}/CoherenceMatrix.csv')

def get_config_params(args):
    """
    Parse Input/Output columns from supplied *.ini file
    """
    configParseObj = configparser.ConfigParser()
    configParseObj.read(args)
    return configParseObj


if __name__ == '__main__':
    main()
