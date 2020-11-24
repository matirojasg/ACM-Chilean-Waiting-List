import codecs
import glob
import os 
import spacy
import es_core_news_lg
from utils import read_file, simplify_entity

def check_files(files_folder, verbose = False):
    """ 
    Check if each text file has its associated annotation file.
    """

    if verbose: print("Checking the annotations files...")
    text_filepaths = sorted(glob.glob(os.path.join(files_folder, '*.txt')))
    for path in text_filepaths:
        base_filename = os.path.splitext(os.path.basename(path))[0]
        annotation_filepath = os.path.join(os.path.dirname(path), base_filename + '.ann')
        if not os.path.exists(annotation_filepath):
            raise IOError("Annotation filepath does not exist: {0}".format(annotation_filepath))
    if verbose: print("DONE: All text files have an associated annotation file.")

def tokenize(text, entities, lower_tokens=False, no_accent_marks=False):
    """ 
    The given text is tokenized prioritizing not to lose entities that ends in the middle of a word.
    This because on many occasions words are stick together in a free text.
    """

    idx = 0
    no_tagged_tokens_positions = []
    tagged_tokens_positions = [(entity['start_idx'], entity['end_idx']) for entity in entities]
    entity_tokens = tokenize_pos_list(text, tagged_tokens_positions, lower_tokens, no_accent_marks)  
    for tagged_token in tagged_tokens_positions:
        no_tagged_tokens_positions.append((idx, tagged_token[0])) # We add text before tagged token
        idx = tagged_token[1] 
    no_tagged_tokens_positions.append((idx, len(text)))           # We add text from last token tagged end possition to end of text.
    no_entity_tokens = tokenize_pos_list(text, no_tagged_tokens_positions, lower_tokens, no_accent_marks)
    tokens = sorted(entity_tokens+no_entity_tokens, key=lambda entity:entity["start_idx"])
    return [tokens]

def tokenize_pos_list(text, pos_list, lower_tokens, no_accent_marks): 
    """ 
    Given a list of pairs of start-end positions in the text, 
    the text within these positions is tokenized and returned in tokens array.
    """

    tokens = []
    tokenizer = spacy.load('es_core_news_lg', disable = ['ner', 'tagger']) # TODO: Add new tokenizers (e.g, Nltk) to compare performance.
    for poss in pos_list:
        text_tokenized = tokenizer(text[poss[0]:poss[1]])
        for span in text_tokenized.sents:
            sentence = [text_tokenized[i] for i in range(span.start, span.end)]
            for token in sentence:
                token_dict = {}
                token_dict['start_idx'] = token.idx + poss[0]
                token_dict['end_idx'] = token.idx + poss[0] + len(token)
                token_dict['text'] = text[token_dict['start_idx']:token_dict['end_idx']]
                if token_dict['text'].strip() in ['\n', '\t', ' ', '']:
                    continue
                if len(token_dict['text'].split(' ')) != 1:
                    token_dict['text'] = token_dict['text'].replace(' ', '-')
                # TODO: Before adding token to token list, process irregular tokens with custom parsing.
                if lower_tokens: token_dict['text'] = token_dict['text'].lower()
                if no_accent_marks: token_dict = remove_accent_mark(token_dict)
                tokens.append(token_dict)
    return tokens

def remove_accent_mark(token_dict):
    try:
        token_dict['text'] = token_dict['text'].replace('á','a')
        token_dict['text'] = token_dict['text'].replace('é','e')
        token_dict['text'] = token_dict['text'].replace('í','i')
        token_dict['text'] = token_dict['text'].replace('ó','o')
        token_dict['text'] = token_dict['text'].replace('ú','u')
        return token_dict
    except:
        return token_dict

    
def get_nested_entities(text_path, ann_path, entities = None):  
    """ 
    Given a text and its annotation file, it returns all inner and outer entities annotated.
    """

    text_filename = os.path.splitext(os.path.basename(text_path))[0]
    ann_filename =  os.path.splitext(os.path.basename(ann_path))[0]
    assert(text_filename == ann_filename)
    text = read_file(text_path, 'UTF-8')
    annotation = read_file(ann_path, 'UTF-8')
    entities = get_nested_entities_from_ann(annotation)
    return text, entities
    
def get_nested_entities_from_ann(annotation):  
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
    """ 
    Given a text and its annotation file, it returns outer entities annotated deleting inner entities.
    """

    text_filename = os.path.splitext(os.path.basename(text_path))[0]
    ann_filename =  os.path.splitext(os.path.basename(ann_path))[0]
    assert(text_filename == ann_filename)
    text = read_file(text_path, 'UTF-8')
    annotation = read_file(ann_path, 'UTF-8')
    entities = get_flat_entities_from_ann(annotation)
    return text, entities

def get_flat_entities_from_ann(annotation):
    entities = []
    repeated_tokens = [] 
    for line in annotation.splitlines():
        is_inner_entity = 0 
        is_equal = 0 
        entity_info = {}
        entity = line.split()
        if entity[0].startswith('T') and not ';' in entity[3]: 
            entity_info['label'] = simplify_entity(entity[1])
            entity_info['start_idx'] = int(entity[2])
            entity_info['end_idx'] = int(entity[3])
            entity_info['text'] = ' '.join(entity[4:])
             
            for other_line in annotation.splitlines():
                entity2 = other_line.split()
                if other_line != line:
                    # If both entity and entity2 contains the same text but they are annotated with different entity types
                    # we arbitrarily maintain the first entity type that was annotated since in many cases 
                    # it is the simplest thing that annotators identified.
                    # TODO: Add some weighting by entity type.

                    if entity2[0].startswith('T') and not ';' in entity2[3] and entity_info['start_idx'] == int(entity2[2]) \
                         and entity_info['end_idx'] == int(entity2[3]):
                        is_equal=1
                        break

                    # In other case we keep the outermost entity in the nested entity sample.
                    if entity2[0].startswith('T') and not ';' in entity2[3] \
                    and ((entity_info['start_idx']>=int(entity2[2]) and entity_info['end_idx']<int(entity2[3])) or \
                    (entity_info['start_idx']>int(entity2[2]) and entity_info['end_idx']<=int(entity2[3])) or \
                    (entity_info['start_idx']>int(entity2[2]) and entity_info['end_idx']<int(entity2[3]))):
                        is_inner_entity=1
                        break
            
            # If entity_info exactly match with another entity but has different entity types
            # it keeps the first annotated one. To know which entity was first annotated we generate
            # repeated_tokens array to keep the entities already added.
            if is_equal and (entity_info['start_idx'], entity_info['end_idx']) not in repeated_tokens and not is_inner_entity: 
                repeated_tokens.append((entity_info['start_idx'], entity_info['end_idx']))
                entities.append(entity_info) 
                
            if not is_inner_entity and not is_equal: 
                entities.append(entity_info)       
    return entities




def convert_to_conll(files_folder, output_path, entity_types = None, multiconll = False, lower_tokens=False, no_accent_marks=False, verbose=False):
    """ 
    Function used to create conll file format from ann-txt annotations.
    """
    check_files(files_folder, verbose)
    text_filepaths = sorted(glob.glob(os.path.join(files_folder, '*.txt')))
    output_file = codecs.open(output_path, 'w', 'UTF-8')
    for path in text_filepaths:
        output_file.write(os.path.basename(path) + '\n')
        filename = os.path.splitext(os.path.basename(path))[0]
        annotation_filepath = os.path.join(os.path.dirname(path), filename + '.ann')
        if multiconll: 
            text, nested_entities = get_nested_entities(path, annotation_filepath, entity_types)
            nested_entities = sorted(nested_entities, key=lambda entity:entity["start_idx"])
        text, flat_entities = get_flat_entities(path, annotation_filepath, entity_types)
        flat_entities = sorted(flat_entities, key=lambda entity:entity["start_idx"])
        sentences = tokenize(text, flat_entities, lower_tokens, no_accent_marks)
        entities = nested_entities if multiconll else flat_entities
        for sentence in sentences:
            inside_entity = {'Disease': 0, 'Abbreviation': 0, 'Finding': 0, 'Procedure': 0, 'Body_Part': 0, 'Family_Member': 0, 'Medication': 0}
            for i, token in enumerate(sentence):
                token_labels = []
                token['label'] = 'O'
                
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

                    elif entity['start_idx']>token['end_idx']:
                        break
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

