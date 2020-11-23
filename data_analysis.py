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

def read_dental_files():
    DENTAL_SPECIALTIES = [
    "ENDODONCIA",
    "OPERATORIA",
    "ENDODONCIA",
    "REHABILITACION: PROTESIS FIJA",
    "CIRUGIA MAXILO FACIAL",
    "ODONTOLOGIA INDIFERENCIADO",
    "REHABILITACION: PROTESIS REMOVIBLE",
    "TRASTORNOS TEMPOROMANDIBULARES Y DOLOR OROFACIAL",
    "CIRUGIA BUCAL",
    "PERIODONCIA"]

    with open('resources/specialty_mapper.json', 'r') as f:
        distros_dict = json.load(f)

    dental_files = []

    for key,value in distros_dict.items():
        if value in DENTAL_SPECIALTIES:
            dental_files.append(key.split('.')[0] + '.ann')
    return dental_files

def get_entities_per_file(path):
  entities = 0
  with codecs.open(path, 'r', 'UTF-8') as f:
        text = f.read()
        for line in text.splitlines():
            annotation = line.split()
            if annotation[0][0] == 'T' and ';' not in annotation[3]:
              entities += 1
  return entities

def count_entities(dental_files, folder_path):
  dental_entities = 0
  no_dental_entities = 0
  total_entities = 0
  ann_filepaths = sorted(glob.glob(os.path.join(folder_path, '*.ann')))
  for path in ann_filepaths: 
      filename = os.path.basename(path)
      if filename in dental_files:
        entities = get_entities_per_file(path)
        dental_entities += entities
        total_entities  += entities
      if filename not in dental_files:
        entities = get_entities_per_file(path)
        no_dental_entities += entities
        total_entities  += entities  
  return dental_entities, no_dental_entities, total_entities

def get_outer_inner_entities(text, filepath):
    outer_inner_entities = []
    for line1 in text.splitlines():    
        outer_entity = line1.split()
        inner_entities = []
        if outer_entity[0].startswith('T') and ';' not in outer_entity[3]:
            inner_entities.append([outer_entity[1], ' '.join(outer_entity[4:]), filepath])
            for line2 in text.splitlines():
                inner_entity = line2.split()
                if line2!=line1 and inner_entity[0].startswith('T') and ';' not in inner_entity[3] and int(inner_entity[2])>=int(outer_entity[2]) and int(inner_entity[3])<=int(outer_entity[3]):
                    inner_entities.append([inner_entity[1], ' '.join(inner_entity[4:]), filepath])
        if len(inner_entities)<=1:
          continue
        outer_inner_entities.append(inner_entities)
    return outer_inner_entities 

def get_nested_matrix(ann_folder):
    nested_entities_array = []
    entities = {'Finding': 0,'Procedure': 1,'Family_Member': 2,'Disease': 3, 'Body_Part': 4, 'Medication': 5, 'Abbreviation': 6}
    nested_matrix = np.zeros((7,7), dtype=int)
    ann_filepaths = sorted(glob.glob(os.path.join(ann_folder, '*.ann')))
    
    for path in ann_filepaths: 
        text = read_file(path, 'UTF-8') 
        nested_entities_array.append(get_outer_inner_entities(text, os.path.basename(path))) 

    for nested_entities in nested_entities_array:
        for nested_sample in nested_entities:
            for inner_entity in nested_sample[1:]:
                nested_matrix[entities[simplify_entity(inner_entity[0])]][entities[simplify_entity(nested_sample[0][0])]]+=1 
    return nested_matrix

def write_nested_entities(nested_matrix):
    entities = ['Finding', 'Procedure', 'Family_Member', 'Disease', 'Body_Part', 'Medication', 'Abbreviation']
    nested_dict = {}
    for i, row in enumerate(nested_matrix):
        nested_dict[entities[i]] = row.tolist()

    with open('nested.json', 'w', encoding='utf-8') as f:
        json.dump(nested_dict, f, ensure_ascii=False, indent=4)

def get_atributes(dental_files):
    dental = False
    ann_filepaths = sorted(glob.glob(os.path.join('resources/annotations', '*.ann')))
    atributes = []
    for path in ann_filepaths:
        if dental and path not in dental_files:
            continue
        with codecs.open(path, 'r', 'UTF-8') as f:
            text = f.read()
        for line in text.splitlines():
            annotation = line.split()
            id_anno = annotation[0]
            if id_anno[0] == 'A':
                atributes.append(annotation[1])

    return atributes

def get_relations(dental_files):
    ann_filepaths = sorted(glob.glob(os.path.join('resources/annotations', '*.ann')))
    dental = False
    relations = 0
    for path in ann_filepaths:
        if dental and path not in dental_files:
            continue
        with codecs.open(path, 'r', 'UTF-8') as f:
            text = f.read()
        for line in text.splitlines():
            annotation = line.split()
            id_anno = annotation[0]
            if id_anno[0] == 'R':
                relations+=1
    return relations

 

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

    with open('total_largos.json', 'w', encoding='utf-8') as f:
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



    with open('total_conteo.json', 'w', encoding='utf-8') as f:
        json.dump(final_dict, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
     dental_files = read_dental_files()
     print(f'La cantidad de anotaciones dentales es: {len(dental_files)}')
     dental_entities, no_dental_entities, total_entities = count_entities(dental_files, 'resources/annotations')
     print(f'La cantidad de entidades en corpus dental es: ' + str(dental_entities))
     print(f'La cantidad de entidades en corpus no dental es: ' + str(no_dental_entities))
     print(f'La cantidad de entidades en corpus total es: ' + str(total_entities))
     nested_matrix = get_nested_matrix('resources/annotations')
     #write_nested_entities(nested_matrix)
     relations = get_relations(dental_files)
     print(f'La cantidad de relaciones identificadas es: {relations}')  
     atributes = get_atributes(dental_files)
     freq = CountFrequency(atributes) 
     entity_frequency = {}
     for key, value in sorted(freq.items(),key=lambda item: item[1]):
            entity_frequency[key]=value

     print(f'La cantidad de atributos encontrados es: {entity_frequency}') 
     #tokens_per_entity(dental_files)
     anno_freq_per_doc(dental_files)