import codecs
import glob
import os 
import spacy
import es_core_news_lg
from utils import read_file, simplify_entity

def check_files(files_folder):
    """ Function used to check if each text file has the associated annotation ann file.
    
    Parameters:
    files_folder (string): Annotations directory.
    
    Returns:

    """
    text_filepaths = sorted(glob.glob(os.path.join(files_folder, '*.txt')))
    for text_filepath in text_filepaths:
        base_filename = os.path.splitext(os.path.basename(text_filepath))[0]
        annotation_filepath = os.path.join(os.path.dirname(text_filepath), base_filename + '.ann')
        if not os.path.exists(annotation_filepath):
            raise IOError("Annotation file does not exist: {0}".format(annotation_filepath))


def tokenize_by_positions(text, positions):
    """ Description.
    
    Parameters:
    text (string): .
    positions (array): .
    
    Returns:
    output (array): .
    """
    output = []
    tokenizer = es_core_news_lg.load()
    for poss in positions:
        text_tokenized = tokenizer(text[poss[0]:poss[1]])
        for span in text_tokenized.sents:
            sentence = [text_tokenized[i] for i in range(span.start, span.end)]
            for token in sentence:
                token_dict = {}
                token_dict['start_idx'] = token.idx + poss[0]
                token_dict['end_idx'] = token.idx + len(token) + poss[0]
                token_dict['text'] = text[token_dict['start_idx']:token_dict['end_idx']]
                if token_dict['text'].strip() in ['\n', '\t', ' ', '']:
                    continue
                if len(token_dict['text'].split(' ')) != 1:
                    token_dict['text'] = token_dict['text'].replace(' ', '-')
                output.append(token_dict)
    return output
    
def tokenize(text, entities):
    """ Description.
    
    Parameters:
    text (string): .
    entities (array): .
    
    Returns:
    output (array): .
    """
    idx = 0
    no_entity_pos = []
    outer_possitions = [(entity['start_idx'], entity['end_idx']) for entity in entities]
    entity_tokens = tokenize_by_positions(text, outer_possitions)  
    for outer in outer_possitions:
        no_entity_pos.append((idx, outer[0]))
        idx = outer[1]
    no_entity_pos.append((idx, len(text)))
    no_entity_tokens = tokenize_by_positions(text, no_entity_pos)
    tokens = sorted(entity_tokens+no_entity_tokens, key=lambda entity:entity["start_idx"])
    return [tokens]
    
def get_nested_entities(text_path, ann_path, entities = None):
    """ Description.
    
    Parameters:
    text_path (string): .
    ann_path (string): .
    entities (array): .
    
    Returns:
    text (string): .
    entities (array): .
    """
    text_filename = os.path.splitext(os.path.basename(text_path))[0]
    ann_filename =  os.path.splitext(os.path.basename(ann_path))[0]
    assert(text_filename == ann_filename)
    text = read_file(text_path, 'UTF-8')
    annotation = read_file(ann_path, 'UTF-8')
    entities = get_nested_entities_from_ann(annotation)
    return text, entities
    
def get_nested_entities_from_ann(annotation):
    """ Description.
    
    Parameters:
    annotation (string): 
    
    Returns:
    entities (array): 
    """
    entities = []
    for line in annotation.splitlines():
        entity_info = {}
        entity = line.split()
        if entity[0].startswith('T') and not ';' in entity[3]: 
            entity_info['label'] = simplify_entity(entity[1])
            entity_info['start_idx'] = int(entity[2])
            entity_info['end_idx'] = int(entity[3])
            entity_info['text'] = ' '.join(entity[4:])
            entities.append(entity_info)
    return entities

def get_flat_entities(text_path, ann_path, entities = None):
    """ Description.
    
    Parameters:
    text_path (string): .
    ann_path (string): .
    entities (array): .
    
    Returns:
    text (string): .
    entities (array): .
    """
    text_filename = os.path.splitext(os.path.basename(text_path))[0]
    ann_filename =  os.path.splitext(os.path.basename(ann_path))[0]
    assert(text_filename == ann_filename)
    text = read_file(text_path, 'UTF-8')
    annotation = read_file(ann_path, 'UTF-8')
    entities = get_flat_entities_from_ann(annotation)
    return text, entities

def get_flat_entities_from_ann(annotation):
    """ Description.
    
    Parameters:
    annotation (string): 
    
    Returns:
    entities (array): 
    """
    entities = []
    repeated_tokens = []
    for line1 in annotation.splitlines():
        entity_info = {}
        entity = line1.split()
        if entity[0].startswith('T') and not ';' in entity[3]: 
            entity_info['label'] = simplify_entity(entity[1])
            entity_info['start_idx'] = int(entity[2])
            entity_info['end_idx'] = int(entity[3])
            entity_info['text'] = ' '.join(entity[4:])
            is_nested = 0
            is_equal = 0 

            for line2 in annotation.splitlines():
                if line2!=line1:
                    entity2 = line2.split()

                    if entity2[0].startswith('T') and not ';' in entity2[3] and entity_info['start_idx']==int(entity2[2]) and entity_info['end_idx']==int(entity2[3]):
                        is_equal=1

                    if entity2[0].startswith('T') and not ';' in entity2[3] \
                    and ( (entity_info['start_idx']>=int(entity2[2]) and entity_info['end_idx']<int(entity2[3])) or \
                    (entity_info['start_idx']>int(entity2[2]) and entity_info['end_idx']<=int(entity2[3])) or \
                    (entity_info['start_idx']>int(entity2[2]) and entity_info['end_idx']<int(entity2[3]))):
                        is_nested=1
                        break
            
            if is_equal and (entity_info['start_idx'], entity_info['end_idx']) not in repeated_tokens and not is_nested: 
                repeated_tokens.append((entity_info['start_idx'], entity_info['end_idx']))
                entities.append(entity_info) 
                
            if not is_nested and not is_equal: 
                entities.append(entity_info)       
    return entities




def convert_to_conll(files_folder, output_path, entity_types = None, multiconll = False):
    """ Function used to create conll file format from ann-txt annotations.
    
    Parameters:
    files_folder (string): Annotations directory.
    output_path (string): Folder filepath to save conll file.
    entities (list): List of entities to be included in the conll file.
    multiconll (boolean): If true then we include nested entities to conll file.

    Returns:

    """

    check_files(files_folder)
    text_filepaths = sorted(glob.glob(os.path.join(files_folder, '*.txt')))
    output_file = codecs.open(output_path, 'w', 'UTF-8')
    for text_filepath in text_filepaths:
        filename = os.path.splitext(os.path.basename(text_filepath))[0]
        annotation_filepath = os.path.join(os.path.dirname(text_filepath), filename + '.ann')
        text, flat_entities = get_flat_entities(text_filepath, annotation_filepath, entity_types)
        text, nested_entities = get_nested_entities(text_filepath, annotation_filepath, entity_types)
        flat_entities = sorted(flat_entities, key=lambda entity:entity["start_idx"])
        nested_entities = sorted(nested_entities, key=lambda entity:entity["start_idx"])
        sentences = tokenize(text, flat_entities)
        entities = nested_entities if multiconll else flat_entities
        for sentence in sentences:
            inside_entity = {'Disease': 0, 'Abbreviation': 0, 'Finding': 0, 'Procedure': 0, 'Body_Part': 0, 'Family_Member': 0, 'Medication': 0}
            for i, token in enumerate(sentence):
                token['label'] = 'O'
                token_labels = []
                for entity in entities:

                    if token['start_idx'] < entity['start_idx']:
                        continue

                    elif token['end_idx'] < entity['end_idx'] and not inside_entity[entity['label']]:
                        inside_entity[entity['label']] = 1
                        token_labels.append('B-' + entity['label'])

                    elif token['end_idx'] < entity['end_idx'] and inside_entity[entity['label']]:
                        token_labels.append('I-' + entity['label'])

                    elif token['end_idx'] == entity['end_idx'] and not inside_entity[entity['label']]:
                        token_labels.append('B-' + entity['label'])
                        
                    elif token['end_idx'] == entity['end_idx'] and inside_entity[entity['label']]:
                        inside_entity[entity['label']]=0
                        token_labels.append('I-' + entity['label'])
 
                    else: 
                        continue

                if len(token_labels)!=0:
                    output_file.write(f"{token['text']} {' '.join(token_labels)}\n")

                elif token['text']=='.' and i!=len(sentence)-1:
                    output_file.write(f"{token['text']} {token['label']}\n\n")

                else:
                    output_file.write(f"{token['text']} {token['label']}\n")
            output_file.write('\n')
    output_file.close()

