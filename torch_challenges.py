# -*- coding: utf-8 -*-
"""Torch_challenges.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1AJWEH-vOC0NJ14JU17fH23JUfbbAhrwa
"""

!wget https://repo.anaconda.com/miniconda/Miniconda3-py37_4.9.2-Linux-x86_64.sh
!chmod +x Miniconda3-py37_4.9.2-Linux-x86_64.sh
!bash ./Miniconda3-py37_4.9.2-Linux-x86_64.sh -b -f -p /usr/local

!conda install pytorch pytorch-cuda=11.8 -c pytorch-nightly -c nvidia -y

#instalaciones

#!pip3 install torchrec-nightly
!cp /usr/local/lib/lib* /usr/lib/

#tareas pendientes: nuevo archivo CSV, carga de datos dinámica

#importaciones
import os
import torch
import torch.nn as nn
import torch.optim as optim

import torch.distributed as dist
import csv
import ast
from torch.utils.data import Dataset, DataLoader


import sys
sys.path = ['', '/env/python', '/usr/local/lib/python37.zip', '/usr/local/lib/python3.7', '/usr/local/lib/python3.7/lib-dynload', '/usr/local/lib/python3.7/site-packages']

#carga del modelo de Torch
class UserItemDataset(Dataset):
    def __init__(self, user_data, item_data, ratings):
        self.user_data = torch.LongTensor(user_data)
        self.item_data = torch.LongTensor(item_data)
        self.ratings = torch.FloatTensor(ratings) #cambiar esto por varios parametros

    def __len__(self):
        return len(self.ratings)

    def __getitem__(self, idx):
        user = self.user_data[idx]
        item = self.item_data[idx]
        rating = self.ratings[idx] #Parámetros deseados: %desafíos realizados en la habilidad correspondiente
        return user, item, rating

# definimos la clase para recomendar y para ser recomendado
class recommender(nn.Module):
    def __init__(self, num_users, num_items, embedding_dim): #van 3 parámetros
        super(recommender, self).__init__()
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.item_embedding = nn.Embedding(num_items, embedding_dim)
        self.fc = nn.Linear(embedding_dim * 2, 1)

    def forward(self, user, item):
        user_embed = self.user_embedding(user)
        item_embed = self.item_embedding(item)
        concat_embed = torch.cat([user_embed, item_embed], dim=1)
        output = self.fc(concat_embed)
        return output.squeeze()

#cargar base de datos (de verdad)
user_data=[] # ID de grupo
ratings = [] # Respuestas habilidades

with open('boldinnGroups.csv') as csv_file:
  csv_reader = csv.reader(csv_file, delimiter=',')
  line_count = 0
  for row in csv_reader:
        if line_count == 0:
            print(f'Column names are {", ".join(row)}')
            line_count += 1
        else:
            float1 = float(row[0])
            int1 = round(float1)
            user_data.append(int1)
            data2_dict = ast.literal_eval(row[2])
            ratings = list(data2_dict.values())
            line_count += 1
print(f'Processed {line_count} lines.')
for i in ratings: ratings[i] = round(ratings[i])

print(f'\t{user_data} has the criteria {ratings}.')


item_data=[]
# task IDs (usar "code")
with open('boldinnTasks.csv') as csv_file:
  csv_reader = csv.reader(csv_file, delimiter=',')
  line_count = 0
  for row in csv_reader:
    if line_count == 0:
            print(f'Column names are {", ".join(row)}')
            line_count += 1
    else:
            print(f'\t{row[0]} has the criteria {row[4]}')
            item_data.append(round(float(row[4])))
            line_count += 1
  print(f'Processed {line_count} lines.')



#carga de los datos en una lista
dataset = UserItemDataset(user_data, item_data, ratings)
dataloader = DataLoader(dataset, batch_size=10, shuffle=False)

#entrenar recomendador (revisar parametros)
num_users = len(user_data)
num_items = len(item_data)
embedding_dim = 128
#selección del modelo
model = recommender(num_users, num_items, embedding_dim)
#configuracion del criterio y su optimizador
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.5)

print(model)
#print(model.plan)

#solicitud para recomendacion (conectar con el Ruby)
recommendations = []
test_user = torch.LongTensor([0])  # Ingresamos "groupID" (indexado)

for i in item_data:
 test_item = torch.LongTensor([i])  # Ingresamos "code" (indexado)
 #iteraciones del modelo recomendador
 with torch.no_grad():
    recommendations.append(model(test_user, test_item))

#iteraciones del modelo recomendador
#with torch.no_grad():
#    recommendations = model(test_user, test_item)

#output (conectar con el Ruby)
#depurar salida
print(recommendations)

"""**Resultados prueba 1**

Sabemos que:
- Reconoce grupos
- Reconoce "criterio"
- Es estable la respuesta entre solicitudes con el mismo grupo y los ejercicios pertenecientes al mismo criterio

Protocolo de "prueba" para determinar estabilidad es:
- Que reporte un valor de recomendacion similar para ejercicios con igual criterio
- Que reporte un valor de recomendacion similar para grupos con criterios evaluados similarmente

---




Lr 0.01

(inconcluso, por variabilidad en las respuestas de todos los grupos probados)




---




Lr 0.1:
- CRG1 sesga a toda la muestra para cada grupo, revisar problema de muestra no homogénea
- No hay estabilidad en la recomendación todavía, a veces criterio alto da negativo, a veces da positivo, depende del grupo

---

Pendientes:
- Código en paralelo con TorchRec - listo
- Probar con nuevo optimizador
- Revisar entrenamiento

**Resultados prueba 2**


Lr 1:
- No hay mejora con respecto a LR = 0.1
- No hay estabilidad en la recomendación todavía, a veces criterio alto da negativo, a veces da positivo, depende del grupo

---


Lr 0.5:
-
-


---

Pendientes:
- Funcionalidad del código en paralelo con TorchRec
- Probar con MSR

**Resultados prueba 3 (PASS!)**



Lr 0.5:
- Se muestran ahora todos los ejercicios de cada grupo para vizualizar si alguno es recomendado por encima de los otros
- Se prueban los grupos ID 6, 15, 118, 81 & 115
- Se nota que la IA recomienda a cada grupo su criterio MAS BAJO con un puntaje mayor y POSITIVO
  - Resultados mixtos cuando el criterio no tiene suficiente "contraste" con los del alrededor
- No se cambio el metodo de entropia que se plantea como un criterio adecuado para recomendar (con matrices de torch)
- Referirse a las tablas de resultados en la parte inferior

# GroupID 6
[tensor(-0.4657), tensor(-0.4657), tensor(-0.4657), tensor(-0.4657), tensor(-0.4657), tensor(-0.4657), tensor(-0.4657), tensor(-0.4657), tensor(-0.6978), tensor(-0.6978), tensor(-0.6978), tensor(-0.6978), tensor(-0.6978), tensor(-0.6978), tensor(-0.6978), tensor(-0.6978), tensor(-0.5693), tensor(-0.5693), tensor(-0.5693), tensor(-0.5693), tensor(-0.5693), tensor(-0.5693), tensor(-0.5693), tensor(-0.5693), tensor(-0.3472), tensor(-0.3472), tensor(-0.3472), tensor(-0.3472), tensor(-0.3472), tensor(-0.3472), tensor(-0.3472), tensor(-0.3472), tensor(-0.3420), tensor(-0.3420), tensor(-0.3420), tensor(-0.3420), tensor(-0.3420), tensor(-0.3420), tensor(-0.3420), tensor(-0.3420), tensor(-0.8367), tensor(-0.8367), tensor(-0.8367), tensor(-0.8367), tensor(-0.8367), tensor(-0.8367), tensor(-0.8367), tensor(-0.8367), tensor(-0.1435), tensor(-0.1435), tensor(-0.1435), tensor(-0.1435), tensor(-0.1435), tensor(-0.1435), tensor(-0.1435), tensor(-0.1435), tensor(-0.9717), tensor(-0.9717), tensor(-0.9717), tensor(-0.9717), tensor(-0.9717), tensor(-0.9717), tensor(-0.9717), tensor(-0.9717), tensor(-0.3972), tensor(-0.3972), tensor(-0.3972), tensor(-0.3972), tensor(-0.3972), tensor(-0.3972), tensor(-0.3972), tensor(-0.3972), tensor(-0.1042), tensor(-0.1042), tensor(-0.1042), tensor(-0.1042), tensor(-0.1042), tensor(-0.1042), tensor(-0.1042), tensor(-0.1042), tensor(-0.8112), tensor(-0.8112), tensor(-0.8112), tensor(-0.8112), tensor(-0.8112), tensor(-0.8112), tensor(-0.8112), tensor(-0.8112), tensor(-0.0369), tensor(-0.0369), tensor(-0.0369), tensor(-0.0369), tensor(-0.0369), tensor(-0.0369), tensor(-0.0369), tensor(-0.0369), tensor(-0.5522), tensor(-0.5522), tensor(-0.5522), tensor(-0.5522), tensor(-0.5522), tensor(-0.5522), tensor(-0.5522), tensor(-0.5522), tensor(-0.5522), tensor(-0.5522), tensor(-0.5522), tensor(-0.5522), tensor(-0.5522), tensor(-0.5522), tensor(-0.5522), tensor(-0.5522), **tensor(0.6842), tensor(0.6842), tensor(0.6842), tensor(0.6842), tensor(0.6842), tensor(0.6842), tensor(0.6842), tensor(0.6842)**,tensor(-0.8299), tensor(-0.8299), tensor(-0.8299), tensor(-0.8299), tensor(-0.8299), tensor(-0.8299), tensor(-0.8299), tensor(-0.8299), tensor(-1.1181), tensor(-1.1181), tensor(-1.1181), tensor(-1.1181), tensor(-1.1181), tensor(-1.1181), tensor(-1.1181), tensor(-1.1181), tensor(-0.7828), tensor(-0.7828), tensor(-0.7828), tensor(-0.7828), tensor(-0.7828), tensor(-0.7828), tensor(-0.7828), tensor(-0.7828), tensor(-0.4414), tensor(-0.4414), tensor(-0.4414), tensor(-0.4414), tensor(-0.4414), tensor(-0.4414), tensor(-0.4414), tensor(-0.4414), tensor(-0.3405), tensor(-0.3405), tensor(-0.3405), tensor(-0.3405), tensor(-0.3405), tensor(-0.3405), tensor(-0.3405), tensor(-0.3405), tensor(-0.8971), tensor(-0.8971), tensor(-0.8971), tensor(-0.8971), tensor(-0.8971), tensor(-0.8971), tensor(-0.8971), tensor(-0.8971)]
"""

from google.colab import drive
drive.mount('/content/drive')

"""# GroupID 15
[tensor(-0.5015), tensor(-0.5015), tensor(-0.5015), tensor(-0.5015), tensor(-0.5015), tensor(-0.5015), tensor(-0.5015), tensor(-0.5015), tensor(-0.7336), tensor(-0.7336), tensor(-0.7336), tensor(-0.7336), tensor(-0.7336), tensor(-0.7336), tensor(-0.7336), tensor(-0.7336), tensor(-0.6051), tensor(-0.6051), tensor(-0.6051), tensor(-0.6051), tensor(-0.6051), tensor(-0.6051), tensor(-0.6051), tensor(-0.6051), tensor(-0.3830), tensor(-0.3830), tensor(-0.3830), tensor(-0.3830), tensor(-0.3830), tensor(-0.3830), tensor(-0.3830), tensor(-0.3830), tensor(-0.3778), tensor(-0.3778), tensor(-0.3778), tensor(-0.3778), tensor(-0.3778), tensor(-0.3778), tensor(-0.3778), tensor(-0.3778), tensor(-0.8725), tensor(-0.8725), tensor(-0.8725), tensor(-0.8725), tensor(-0.8725), tensor(-0.8725), tensor(-0.8725), tensor(-0.8725), tensor(-0.1793), tensor(-0.1793), tensor(-0.1793), tensor(-0.1793), tensor(-0.1793), tensor(-0.1793), tensor(-0.1793), tensor(-0.1793), tensor(-1.0075), tensor(-1.0075), tensor(-1.0075), tensor(-1.0075), tensor(-1.0075), tensor(-1.0075), tensor(-1.0075), tensor(-1.0075), tensor(-0.4330), tensor(-0.4330), tensor(-0.4330), tensor(-0.4330), tensor(-0.4330), tensor(-0.4330), tensor(-0.4330), tensor(-0.4330), tensor(-0.1400), tensor(-0.1400), tensor(-0.1400), tensor(-0.1400), tensor(-0.1400), tensor(-0.1400), tensor(-0.1400), tensor(-0.1400), tensor(-0.8470), tensor(-0.8470), tensor(-0.8470), tensor(-0.8470), tensor(-0.8470), tensor(-0.8470), tensor(-0.8470), tensor(-0.8470), tensor(-0.0727), tensor(-0.0727), tensor(-0.0727), tensor(-0.0727), tensor(-0.0727), tensor(-0.0727), tensor(-0.0727), tensor(-0.0727), tensor(-0.5880), tensor(-0.5880), tensor(-0.5880), tensor(-0.5880), tensor(-0.5880), tensor(-0.5880), tensor(-0.5880), tensor(-0.5880), tensor(-0.5880), tensor(-0.5880), tensor(-0.5880), tensor(-0.5880), tensor(-0.5880), tensor(-0.5880), tensor(-0.5880), tensor(-0.5880), **tensor(0.6484), tensor(0.6484), tensor(0.6484), tensor(0.6484), tensor(0.6484), tensor(0.6484), tensor(0.6484), tensor(0.6484)**, tensor(-0.8657), tensor(-0.8657), tensor(-0.8657), tensor(-0.8657), tensor(-0.8657), tensor(-0.8657), tensor(-0.8657), tensor(-0.8657), tensor(-1.1539), tensor(-1.1539), tensor(-1.1539), tensor(-1.1539), tensor(-1.1539), tensor(-1.1539), tensor(-1.1539), tensor(-1.1539), tensor(-0.8185), tensor(-0.8185), tensor(-0.8185), tensor(-0.8185), tensor(-0.8185), tensor(-0.8185), tensor(-0.8185), tensor(-0.8185), tensor(-0.4772), tensor(-0.4772), tensor(-0.4772), tensor(-0.4772), tensor(-0.4772), tensor(-0.4772), tensor(-0.4772), tensor(-0.4772), tensor(-0.3763), tensor(-0.3763), tensor(-0.3763), tensor(-0.3763), tensor(-0.3763), tensor(-0.3763), tensor(-0.3763), tensor(-0.3763), tensor(-0.9329), tensor(-0.9329), tensor(-0.9329), tensor(-0.9329), tensor(-0.9329), tensor(-0.9329), tensor(-0.9329), tensor(-0.9329)]

# Group ID 118
[tensor(-0.3016), tensor(-0.3016), tensor(-0.3016), tensor(-0.3016), tensor(-0.3016), tensor(-0.3016), tensor(-0.3016), tensor(-0.3016), tensor(-0.5337), tensor(-0.5337), tensor(-0.5337), tensor(-0.5337), tensor(-0.5337), tensor(-0.5337), tensor(-0.5337), tensor(-0.5337), tensor(-0.4052), tensor(-0.4052), tensor(-0.4052), tensor(-0.4052), tensor(-0.4052), tensor(-0.4052), tensor(-0.4052), tensor(-0.4052), tensor(-0.1831), tensor(-0.1831), tensor(-0.1831), tensor(-0.1831), tensor(-0.1831), tensor(-0.1831), tensor(-0.1831), tensor(-0.1831), tensor(-0.1779), tensor(-0.1779), tensor(-0.1779), tensor(-0.1779), tensor(-0.1779), tensor(-0.1779), tensor(-0.1779), tensor(-0.1779), tensor(-0.6726), tensor(-0.6726), tensor(-0.6726), tensor(-0.6726), tensor(-0.6726), tensor(-0.6726), tensor(-0.6726), tensor(-0.6726), **tensor(0.0206), tensor(0.0206), tensor(0.0206), tensor(0.0206), tensor(0.0206), tensor(0.0206), tensor(0.0206), tensor(0.0206)**, tensor(-0.8077), tensor(-0.8077), tensor(-0.8077), tensor(-0.8077), tensor(-0.8077), tensor(-0.8077), tensor(-0.8077), tensor(-0.8077), tensor(-0.2331), tensor(-0.2331), tensor(-0.2331), tensor(-0.2331), tensor(-0.2331), tensor(-0.2331), tensor(-0.2331), tensor(-0.2331), **tensor(0.0599), tensor(0.0599), tensor(0.0599), tensor(0.0599), tensor(0.0599), tensor(0.0599), tensor(0.0599), tensor(0.0599)**, tensor(-0.6471), tensor(-0.6471), tensor(-0.6471), tensor(-0.6471), tensor(-0.6471), tensor(-0.6471), tensor(-0.6471), tensor(-0.6471), **tensor(0.1272), tensor(0.1272), tensor(0.1272), tensor(0.1272), tensor(0.1272), tensor(0.1272), tensor(0.1272), tensor(0.1272)**, tensor(-0.3881), tensor(-0.3881), tensor(-0.3881), tensor(-0.3881), tensor(-0.3881), tensor(-0.3881), tensor(-0.3881), tensor(-0.3881), tensor(-0.3881), tensor(-0.3881), tensor(-0.3881), tensor(-0.3881), tensor(-0.3881), tensor(-0.3881), tensor(-0.3881), tensor(-0.3881), **tensor(0.8483), tensor(0.8483), tensor(0.8483), tensor(0.8483), tensor(0.8483), tensor(0.8483), tensor(0.8483)**, tensor(0.8483), tensor(-0.6658), tensor(-0.6658), tensor(-0.6658), tensor(-0.6658), tensor(-0.6658), tensor(-0.6658), tensor(-0.6658), tensor(-0.6658), tensor(-0.9540), tensor(-0.9540), tensor(-0.9540), tensor(-0.9540), tensor(-0.9540), tensor(-0.9540), tensor(-0.9540), tensor(-0.9540), tensor(-0.6187), tensor(-0.6187), tensor(-0.6187), tensor(-0.6187), tensor(-0.6187), tensor(-0.6187), tensor(-0.6187), tensor(-0.6187), tensor(-0.2773), tensor(-0.2773), tensor(-0.2773), tensor(-0.2773), tensor(-0.2773), tensor(-0.2773), tensor(-0.2773), tensor(-0.2773), tensor(-0.1764), tensor(-0.1764), tensor(-0.1764), tensor(-0.1764), tensor(-0.1764), tensor(-0.1764), tensor(-0.1764), tensor(-0.1764), tensor(-0.7330), tensor(-0.7330), tensor(-0.7330), tensor(-0.7330), tensor(-0.7330), tensor(-0.7330), tensor(-0.7330), tensor(-0.7330)]

# GroupID 81 (DUMMY!)
[**tensor(0.3141), tensor(0.3141), tensor(0.3141), tensor(0.3141), tensor(0.3141), tensor(0.3141), tensor(0.3141), tensor(0.3141), tensor(0.0820), tensor(0.0820), tensor(0.0820), tensor(0.0820), tensor(0.0820), tensor(0.0820), tensor(0.0820), tensor(0.0820), tensor(0.2105), tensor(0.2105), tensor(0.2105), tensor(0.2105), tensor(0.2105), tensor(0.2105), tensor(0.2105), tensor(0.2105), tensor(0.4326), tensor(0.4326), tensor(0.4326), tensor(0.4326), tensor(0.4326), tensor(0.4326), tensor(0.4326), tensor(0.4326), tensor(0.4378), tensor(0.4378), tensor(0.4378), tensor(0.4378), tensor(0.4378), tensor(0.4378), tensor(0.4378), tensor(0.4378)**, tensor(-0.0569), tensor(-0.0569), tensor(-0.0569), tensor(-0.0569), tensor(-0.0569), tensor(-0.0569), tensor(-0.0569), tensor(-0.0569), **tensor(0.6363), tensor(0.6363), tensor(0.6363), tensor(0.6363), tensor(0.6363), tensor(0.6363), tensor(0.6363), tensor(0.6363)**, tensor(-0.1919), tensor(-0.1919), tensor(-0.1919), tensor(-0.1919), tensor(-0.1919), tensor(-0.1919), tensor(-0.1919), tensor(-0.1919), **tensor(0.3826), tensor(0.3826), tensor(0.3826), tensor(0.3826), tensor(0.3826), tensor(0.3826), tensor(0.3826), tensor(0.3826), tensor(0.6756), tensor(0.6756), tensor(0.6756), tensor(0.6756), tensor(0.6756), tensor(0.6756), tensor(0.6756), tensor(0.6756)**, tensor(-0.0314), tensor(-0.0314), tensor(-0.0314), tensor(-0.0314), tensor(-0.0314), tensor(-0.0314), tensor(-0.0314), tensor(-0.0314), **tensor(0.7429), tensor(0.7429), tensor(0.7429), tensor(0.7429), tensor(0.7429), tensor(0.7429), tensor(0.7429), tensor(0.7429), tensor(0.2276), tensor(0.2276), tensor(0.2276), tensor(0.2276), tensor(0.2276), tensor(0.2276), tensor(0.2276), tensor(0.2276), tensor(0.2276), tensor(0.2276), tensor(0.2276), tensor(0.2276), tensor(0.2276), tensor(0.2276), tensor(0.2276), tensor(0.2276), tensor(1.4640), tensor(1.4640), tensor(1.4640), tensor(1.4640), tensor(1.4640), tensor(1.4640), tensor(1.4640), tensor(1.4640)**, tensor(-0.0501), tensor(-0.0501), tensor(-0.0501), tensor(-0.0501), tensor(-0.0501), tensor(-0.0501), tensor(-0.0501), tensor(-0.0501), tensor(-0.3383), tensor(-0.3383), tensor(-0.3383), tensor(-0.3383), tensor(-0.3383), tensor(-0.3383), tensor(-0.3383), tensor(-0.3383), tensor(-0.0029), tensor(-0.0029), tensor(-0.0029), tensor(-0.0029), tensor(-0.0029), tensor(-0.0029), tensor(-0.0029), tensor(-0.0029), **tensor(0.3384), tensor(0.3384), tensor(0.3384), tensor(0.3384), tensor(0.3384), tensor(0.3384), tensor(0.3384), tensor(0.3384), tensor(0.4393), tensor(0.4393), tensor(0.4393), tensor(0.4393), tensor(0.4393), tensor(0.4393), tensor(0.4393), tensor(0.4393**), tensor(-0.1173), tensor(-0.1173), tensor(-0.1173), tensor(-0.1173), tensor(-0.1173), tensor(-0.1173), tensor(-0.1173), tensor(-0.1173)]

# GroupID 115 resultados mixtos
[**tensor(0.0092), tensor(0.0092), tensor(0.0092), tensor(0.0092), tensor(0.0092), tensor(0.0092), tensor(0.0092), tensor(0.0092)**, tensor(-0.2229), tensor(-0.2229), tensor(-0.2229), tensor(-0.2229), tensor(-0.2229), tensor(-0.2229), tensor(-0.2229), tensor(-0.2229), tensor(-0.0943), tensor(-0.0943), tensor(-0.0943), tensor(-0.0943), tensor(-0.0943), tensor(-0.0943), tensor(-0.0943), tensor(-0.0943), **tensor(0.1277), tensor(0.1277), tensor(0.1277), tensor(0.1277), tensor(0.1277), tensor(0.1277), tensor(0.1277), tensor(0.1277), tensor(0.1329), tensor(0.1329), tensor(0.1329), tensor(0.1329), tensor(0.1329), tensor(0.1329), tensor(0.1329), tensor(0.1329)**, tensor(-0.3618), tensor(-0.3618), tensor(-0.3618), tensor(-0.3618), tensor(-0.3618), tensor(-0.3618), tensor(-0.3618), tensor(-0.3618), tensor(0.3314), tensor(0.3314), tensor(0.3314), tensor(0.3314), tensor(0.3314), tensor(0.3314), tensor(0.3314), tensor(0.3314), tensor(-0.4968), tensor(-0.4968), tensor(-0.4968), tensor(-0.4968), tensor(-0.4968), tensor(-0.4968), tensor(-0.4968), tensor(-0.4968), **tensor(0.0777), tensor(0.0777), tensor(0.0777), tensor(0.0777), tensor(0.0777), tensor(0.0777), tensor(0.0777), tensor(0.0777), tensor(0.3707), tensor(0.3707), tensor(0.3707), tensor(0.3707), tensor(0.3707), tensor(0.3707), tensor(0.3707), tensor(0.3707)**, tensor(-0.3363), tensor(-0.3363), tensor(-0.3363), tensor(-0.3363), tensor(-0.3363), tensor(-0.3363), tensor(-0.3363), tensor(-0.3363), **tensor(0.4380), tensor(0.4380), tensor(0.4380), tensor(0.4380), tensor(0.4380), tensor(0.4380), tensor(0.4380), tensor(0.4380)**, tensor(-0.0773), tensor(-0.0773), tensor(-0.0773), tensor(-0.0773), tensor(-0.0773), tensor(-0.0773), tensor(-0.0773), tensor(-0.0773), tensor(-0.0773), tensor(-0.0773), tensor(-0.0773), tensor(-0.0773), tensor(-0.0773), tensor(-0.0773), tensor(-0.0773), tensor(-0.0773), **tensor(1.1591), tensor(1.1591), tensor(1.1591), tensor(1.1591), tensor(1.1591), tensor(1.1591), tensor(1.1591), tensor(1.1591)**, tensor(-0.3550), tensor(-0.3550), tensor(-0.3550), tensor(-0.3550), tensor(-0.3550), tensor(-0.3550), tensor(-0.3550), tensor(-0.3550), tensor(-0.6432), tensor(-0.6432), tensor(-0.6432), tensor(-0.6432), tensor(-0.6432), tensor(-0.6432), tensor(-0.6432), tensor(-0.6432), tensor(-0.3078), tensor(-0.3078), tensor(-0.3078), tensor(-0.3078), tensor(-0.3078), tensor(-0.3078), tensor(-0.3078), tensor(-0.3078), **tensor(0.0335), tensor(0.0335), tensor(0.0335), tensor(0.0335), tensor(0.0335), tensor(0.0335), tensor(0.0335), tensor(0.0335), tensor(0.1344), tensor(0.1344), tensor(0.1344), tensor(0.1344), tensor(0.1344), tensor(0.1344), tensor(0.1344), tensor(0.1344)**, tensor(-0.4222), tensor(-0.4222), tensor(-0.4222), tensor(-0.4222), tensor(-0.4222), tensor(-0.4222), tensor(-0.4222), tensor(-0.4222)]

#Tareas pendientes siguiente etapa
- incluir nivel del ejercicio y consultar qué niveles (0, 1, 2 y 3) de un cierto criterio ya están hechos por el usuario
- Armar la ruta con los dos criterios recomendados como más bajos y dos que figuren como altos a partir de datos de la IA y filtros básicos
- Conectar la recomendación de criterio con alguna solicitud real

[tensor(0.5030), tensor(0.5030), tensor(0.5030), tensor(0.5030), tensor(0.5030), tensor(0.5030), tensor(0.5030), tensor(0.5030), tensor(0.2492), tensor(0.2492), tensor(0.2492), tensor(0.2492), tensor(0.2492), tensor(0.2492), tensor(0.2492), tensor(0.2492), tensor(0.3028), tensor(0.3028), tensor(0.3028), tensor(0.3028), tensor(0.3028), tensor(0.3028), tensor(0.3028), tensor(0.3028), tensor(0.4803), tensor(0.4803), tensor(0.4803), tensor(0.4803), tensor(0.4803), tensor(0.4803), tensor(0.4803), tensor(0.4803), tensor(0.6125), tensor(0.6125), tensor(0.6125), tensor(0.6125), tensor(0.6125), tensor(0.6125), tensor(0.6125), tensor(0.6125), tensor(0.6846), tensor(0.6846), tensor(0.6846), tensor(0.6846), tensor(0.6846), tensor(0.6846), tensor(0.6846), tensor(0.6846), tensor(-0.1707), tensor(-0.1707), tensor(-0.1707), tensor(-0.1707), tensor(-0.1707), tensor(-0.1707), tensor(-0.1707), tensor(-0.1707), tensor(-0.1726), tensor(-0.1726), tensor(-0.1726), tensor(-0.1726), tensor(-0.1726), tensor(-0.1726), tensor(-0.1726), tensor(-0.1726), tensor(0.3990), tensor(0.3990), tensor(0.3990), tensor(0.3990), tensor(0.3990), tensor(0.3990), tensor(0.3990), tensor(0.3990), tensor(-0.3849), tensor(-0.3849), tensor(-0.3849), tensor(-0.3849), tensor(-0.3849), tensor(-0.3849), tensor(-0.3849), tensor(-0.3849), tensor(0.0300), tensor(0.0300), tensor(0.0300), tensor(0.0300), tensor(0.0300), tensor(0.0300), tensor(0.0300), tensor(0.0300), tensor(0.2408), tensor(0.2408), tensor(0.2408), tensor(0.2408), tensor(0.2408), tensor(0.2408), tensor(0.2408), tensor(0.2408), tensor(0.5535), tensor(0.5535), tensor(0.5535), tensor(0.5535), tensor(0.5535), tensor(0.5535), tensor(0.5535), tensor(0.5535), tensor(0.5535), tensor(0.5535), tensor(0.5535), tensor(0.5535), tensor(0.5535), tensor(0.5535), tensor(0.5535), tensor(0.5535), tensor(0.2731), tensor(0.2731), tensor(0.2731), tensor(0.2731), tensor(0.2731), tensor(0.2731), tensor(0.2731), tensor(0.2731), tensor(-0.0597), tensor(-0.0597), tensor(-0.0597), tensor(-0.0597), tensor(-0.0597), tensor(-0.0597), tensor(-0.0597), tensor(-0.0597), tensor(0.7816), tensor(0.7816), tensor(0.7816), tensor(0.7816), tensor(0.7816), tensor(0.7816), tensor(0.7816), tensor(0.7816), tensor(0.3532), tensor(0.3532), tensor(0.3532), tensor(0.3532), tensor(0.3532), tensor(0.3532), tensor(0.3532), tensor(0.3532), tensor(0.1721), tensor(0.1721), tensor(0.1721), tensor(0.1721), tensor(0.1721), tensor(0.1721), tensor(0.1721), tensor(0.1721), tensor(0.1376), tensor(0.1376), tensor(0.1376), tensor(0.1376), tensor(0.1376), tensor(0.1376), tensor(0.1376), tensor(0.1376), tensor(-0.2822), tensor(-0.2822), tensor(-0.2822), tensor(-0.2822), tensor(-0.2822), tensor(-0.2822), tensor(-0.2822), tensor(-0.2822)]
"""