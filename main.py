import argparse
import os
from brat_to_conll import convert_to_conll

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str, required=False, default='entities')
    parser.add_argument('-t', '--types', default=None, metavar='TYPE', nargs='*', help='Filter entities to given types')
    parser.add_argument('-n', '--multiconll', default=False, action='store_true', help='Create multiconll file')
    args = parser.parse_args()  
    output_filename = args.name
    entity_types = args.types 
    multiconll = args.multiconll
    actual_path = os.path.abspath(os.path.dirname(__file__))
    annotations_filepath = os.path.join(actual_path, 'resources/annotations')
    output_filepath = os.path.join(actual_path, f'resources/conll_format/{output_filename}.conll')
    convert_to_conll(annotations_filepath, output_filepath, entity_types, multiconll)