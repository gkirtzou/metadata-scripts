from collections import defaultdict

import lxml.etree as etree
import rdflib
from configparser import ConfigParser
import ast





if __name__ == '__main__':
    Config = ConfigParser()
    Config.read('generate_controlled_vocabularies_as_csv.ini')

    filename_input = Config.get('Input', 'filename_csv')
    filename_output = Config.get('Output', 'filename_csv')

    # Read csv file
    f_input = open(filename_input, 'r')
    content = f_input.read()
    f_input.close()

    d = defaultdict(set)
    for c in content.split('#########'):
        c = c.split(',')
        if len(c) == 2:
            d[c[0].strip()].add(c[1].strip())

        else:
            print(c)

    print(dict)
    # Print csv
    f_output = open(filename_output, 'w')
    for key, value in d.items():
        f_output.write(key + "," + str(value) + '\n')
    f_output.close()
