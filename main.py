import argparse
import os
from brat_to_conll import convert_to_conll

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_filename', type=str, required=False, default='entities')
    parser.add_argument('--multi_conll', type=bool, default=False)
    parser.add_argument('--lower_tokens', type=bool, default=False)
    parser.add_argument('--no_accent_marks', type=bool, default=False)
    parser.add_argument('--verbose', type=bool, default=False)
    parser.add_argument(
        '-t', 
        '--types', 
        default=None,
        metavar='TYPE', 
        nargs='*', 
        help='Filter entities to given types')

    args = parser.parse_args()  
    output_filename = args.output_filename
    multiconll = args.multi_conll
    lower_tokens = args.lower_tokens
    no_accent_marks = args.no_accent_marks
    verbose = args.verbose
    entity_types = args.types 
    actual_path = os.path.abspath(os.path.dirname(__file__))
    annotations_filepath = os.path.join(actual_path, 'resources/sample_annotations')
    output_filepath = os.path.join(actual_path, f'resources/conll_format/{output_filename}.conll')
    convert_to_conll(annotations_filepath, output_filepath, entity_types, multiconll, lower_tokens, no_accent_marks, verbose)