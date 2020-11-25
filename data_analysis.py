import os
import re
import json
import glob
import codecs
import collections
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import spacy
import json
import es_core_news_lg
from utils import simplify_entity, read_file

def CountFrequency(arr): 
    return collections.Counter(arr) 

def get_dental_files(path):
    """
    Get filenames associated to dental specialties.
    """

    DENTAL_SPECIALTIES = ["ENDODONCIA","OPERATORIA","ENDODONCIA","REHABILITACION: PROTESIS FIJA", \
        "CIRUGIA MAXILO FACIAL","ODONTOLOGIA INDIFERENCIADO", "REHABILITACION: PROTESIS REMOVIBLE", \
        "TRASTORNOS TEMPOROMANDIBULARES Y DOLOR OROFACIAL","CIRUGIA BUCAL","PERIODONCIA"]
    
    with open(path, 'r') as f:
        specialties_dict = json.load(f)

    dental_files = [key.split('.')[0] + '.ann' for key, value in specialties_dict.items() if value in DENTAL_SPECIALTIES]
    return dental_files

def get_entities_per_file(path):
  n_entities = 0
  text = read_file(path, 'utf-8')
  for line in text.splitlines():
    annotation = line.split()
    if annotation[0][0] == 'T' and ';' not in annotation[3]:
        n_entities += 1
  return n_entities

def count_entities(dental_files, folder_path):
  """
  Returns total entities (Begin-entity) in three different corpus: Dental, Non dental, Dental + Non Dental
  """

  n_dental_entities = 0
  n_non_dental_entities = 0
  n_total_entities = 0
  ann_filepaths = sorted(glob.glob(os.path.join(folder_path, '*.ann')))
  for path in ann_filepaths: 
      filename = os.path.basename(path)
      if filename in dental_files:
        entities = get_entities_per_file(path)
        n_dental_entities += entities
        n_total_entities  += entities
      if filename not in dental_files:
        entities = get_entities_per_file(path)
        n_non_dental_entities += entities
        n_total_entities  += entities  
  return n_dental_entities, n_non_dental_entities, n_total_entities

   
def get_nested_entities(text):
    """
    Find all nested entities. [Entity1 (Outer entity), Entity2 (Inner entity inside Entity1), Entity3....]
    """
    nested_entities = []
    for line in text.splitlines():    
        outer_entity = line.split()
        nested_entity = []
        if outer_entity[0].startswith('T') and ';' not in outer_entity[3]:
            nested_entity.append(outer_entity[1])
            for other_line in text.splitlines():
                inner_entity = other_line.split()
                if other_line!=line and inner_entity[0].startswith('T') and ';' not in inner_entity[3] \
                     and int(inner_entity[2])>=int(outer_entity[2]) and int(inner_entity[3])<=int(outer_entity[3]):
                    nested_entity.append(inner_entity[1])
        if len(nested_entity)<=1:
          continue
        nested_entities.append(nested_entity)
    return nested_entities


def get_nested_matrix(ann_folder, dental_files):
    """
    Get nested entities matrix where rows entities are contained in columns entities.
    """

    entities = {'Finding': 0,'Procedure': 1,'Family_Member': 2,'Disease': 3, 'Body_Part': 4, 'Medication': 5, 'Abbreviation': 6}
    ann_filepaths = sorted(glob.glob(os.path.join(ann_folder, '*.ann')))
    dental_nested_entities = []
    non_dental_nested_entities = []
    nested_entities = []

    for path in ann_filepaths:
        text = read_file(path, 'UTF-8')
        nested_entities.append(get_nested_entities(text))
        if os.path.basename(path) in dental_files:
            dental_nested_entities.append(get_nested_entities(text)) 
        else:
            non_dental_nested_entities.append(get_nested_entities(text)) 
             

    dental_nested_matrix = get_matrix(dental_nested_entities, entities)
    non_dental_nested_matrix = get_matrix(non_dental_nested_entities, entities)
    nested_matrix = get_matrix(nested_entities, entities)
    return dental_nested_matrix, non_dental_nested_matrix, nested_matrix

def get_matrix(nested_entities_array, entities_dict):
    nested_matrix = np.zeros((7,7), dtype=int)
    for nested_entities in nested_entities_array:
        for nested_sample in nested_entities:
            for inner_entity in nested_sample[1:]:
                nested_matrix[entities_dict[simplify_entity(inner_entity)]][entities_dict[simplify_entity(nested_sample[0])]]+=1 
    return nested_matrix

def write_nested_entities(path, nested_matrix):
    """
    Write in json format the nested entities matrix.
    """

    entities = ['Finding', 'Procedure', 'Family_Member', 'Disease', 'Body_Part', 'Medication', 'Abbreviation']
    nested_dict = {}
    for i, row in enumerate(nested_matrix):
        nested_dict[entities[i]] = row.tolist()

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(nested_dict, f, ensure_ascii=False, indent=4)
 
def get_all_attributes(dental_files):
    """
    It returns the attributes found in the annotations.
    """

    ann_filepaths = sorted(glob.glob(os.path.join('resources/annotations', '*.ann')))
    dental_attributes = []
    non_dental_attributes = []
    attributes = []

    for path in ann_filepaths:
        text = read_file(path, 'utf-8')
        attributes+=get_attributes(text)
        if os.path.basename(path) in dental_files:
            dental_attributes+=get_attributes(text)
        else:
            non_dental_attributes+=get_attributes(text)
    return dental_attributes, non_dental_attributes, attributes

def get_attributes(text):
    attributes = []
    for line in text.splitlines():
        annotation = line.split()
        id_anno = annotation[0]
        if id_anno[0] == 'A':
            attributes.append(annotation[1])
    return attributes

def print_frequency_dict(attributes, type):
    freq = CountFrequency(attributes) 
    entity_frequency = {}
    for key, value in sorted(freq.items(),key=lambda item: item[1]):
        entity_frequency[key]=value
    print(f'{type} attributes: {entity_frequency}') 

def get_all_relations(dental_files):
    """
    It returns the number of relations found in the annotations.
    """
    ann_filepaths = sorted(glob.glob(os.path.join('resources/annotations', '*.ann')))
    n_dental_relations = 0
    n_non_dental_relations = 0
    n_relations = 0
    for path in ann_filepaths:
        text = read_file(path, 'utf-8')
        n_relations+=get_relations(text)
        if os.path.basename(path) in dental_files:
            n_dental_relations+=get_relations(text)
        else:
            n_non_dental_relations+=get_relations(text)   
    return n_dental_relations, n_non_dental_relations, n_relations

def get_relations(text):
    n_relations = 0
    for line in text.splitlines():
        annotation = line.split()
        id_anno = annotation[0]
        if id_anno[0] == 'R':
            n_relations+=1
    return n_relations

def get_tokens_len(text):
  nlp = es_core_news_lg.load()
  tokens = []
  for sent in nlp(text).sents:
    for token in sent:
      tokens.append(token)
  return len(tokens)  


def tokens_per_entity(dental_files):
    dental = False
    no_dental = False
    procedure_tokens = []
    medication_tokens = []
    body_tokens = []
    abb_tokens = []
    family_tokens = []
    disease_tokens = []
    finding_tokens = []
    ann_filepaths = sorted(glob.glob(os.path.join('resources/annotations', '*.ann')))
    for path in ann_filepaths: 
        if dental and path not in dental_files:
            continue
        if no_dental and path in dental_files:
            continue
        with codecs.open(path, 'r', 'UTF-8') as f: 
            for line in f.read().splitlines():
                anno = line.split()
                id_anno = anno[0]
                if id_anno[0] == 'T' and ';' not in anno[3]:
                    entity = simplify_entity(anno[1])
                    if entity == "Procedure":
                        procedure_tokens.append(get_tokens_len(' '.join(anno[4:])))
                    elif entity =="Medication":
                        medication_tokens.append(get_tokens_len(' '.join(anno[4:])))
                    elif entity =="Body_Part":
                        body_tokens.append(get_tokens_len(' '.join(anno[4:])))
                    elif entity =="Abbreviation":
                        abb_tokens.append(get_tokens_len(' '.join(anno[4:])))
                    elif entity =="Family_Member":
                        family_tokens.append(get_tokens_len(' '.join(anno[4:])))
                    elif entity=="Finding":
                        finding_tokens.append(get_tokens_len(' '.join(anno[4:])))
                    elif entity=="Disease":
                        disease_tokens.append(get_tokens_len(' '.join(anno[4:])))
                    else:
                        pass

    final_dict = {}
    final_dict['Procedure']=procedure_tokens
    final_dict['Medication']=medication_tokens
    final_dict['Body_Part']=body_tokens
    final_dict['Abbreviation']= abb_tokens
    final_dict['Family_Member']= family_tokens
    final_dict['Disease']=disease_tokens
    final_dict['Finding']=finding_tokens

    with open('resources/json_files/total_largos.json', 'w', encoding='utf-8') as f:
        json.dump(final_dict, f, ensure_ascii=False, indent=4)


def anno_freq_per_doc(dental_files):
    dental = False
    no_dental = False
    ann_filepaths = sorted(glob.glob(os.path.join('resources/annotations', '*.ann')))
    total_entities_ann = []

    for path in ann_filepaths: 
        if dental and path not in dental_files:
            continue
        if no_dental and path in dental_files:
            continue
        entities_ann = []
        with codecs.open(path, 'r', 'UTF-8') as f: 
            for line in f.read().splitlines():
                anno = line.split()
                id_anno = anno[0]
                if id_anno[0] == 'T' and ';' not in anno[3]:
                    entity = simplify_entity(anno[1])
                    entities_ann.append(entity)
            total_entities_ann.append(entities_ann)
                

    entities_freq = []
    for file in total_entities_ann:
        freq = CountFrequency(file)  
        temporal_array = []                            
        for key, value in freq.items():
            temporal_array.append((key,str(value)))
        entities_freq.append(temporal_array)


    final_dict = {}
    for i, entities in enumerate(entities_freq):
        temporal_dict = {}
        for entity in entities:
            temporal_dict[entity[0]]=entity[1]
        final_dict[ann_filepaths[i]]=temporal_dict 



    with open('resources/json_files/total_conteo.json', 'w', encoding='utf-8') as f:
        json.dump(final_dict, f, ensure_ascii=False, indent=4)



if __name__ == "__main__":
     dental_files = get_dental_files('resources/json_files/specialty_mapper.json')
     print(f'The number of dental annotations is: {len(dental_files)} \n')

     dental_entities, no_dental_entities, total_entities = count_entities(dental_files, 'resources/annotations')

     print(f'Dental corpus entities: {dental_entities}')
     print(f'Non dental corpus entities: {no_dental_entities}')
     print(f'Total corpus entities: {total_entities} \n')

     dental_nested_matrix, non_dental_nested_matrix, nested_matrix = get_nested_matrix('resources/annotations', dental_files)
     write_nested_entities('resources/json_files/dental_nested_matrix.json', dental_nested_matrix)
     write_nested_entities('resources/json_files/non_dental_nested_matrix.json', non_dental_nested_matrix)
     write_nested_entities('resources/json_files/nested_matrix.json', nested_matrix)

     dental_attributes, non_dental_attributes, attributes = get_all_attributes(dental_files)
     print_frequency_dict(dental_attributes, 'Dental')
     print_frequency_dict(non_dental_attributes, 'Non Dental')
     print_frequency_dict(attributes, 'Total')
      
     dental_relations, non_dental_relations, relations = get_all_relations(dental_files)
     print(f'Dental corpus relations: {dental_relations}')
     print(f'Non dental corpus relations: {non_dental_relations}')
     print(f'Total corpus relations: {relations} \n')
     
     #tokens_per_entity(dental_files)
     #anno_freq_per_doc(dental_files)