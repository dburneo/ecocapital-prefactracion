import json, urllib.request
import requests
import uuid
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


with urllib.request.urlopen("https://xinternet.co/prefact/json/Tags/GET/tags/salidas.json") as url:
    dataCategory = json.loads(url.read().decode(), parse_int=True)

with urllib.request.urlopen("https://xinternet.co/prefact/Json/CalculatorsJobs/POST/calculator/entrada.json") as url:
    dataClientsBill = json.loads(url.read().decode(), parse_int=True)


class PreFact(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(selft, request):
        # content = {'Message hello Developer'}

        def actCategory(tag):
            for cat in dataCategory['tags']:
                if cat['name'] == tag:
                    actPrice_per_unit = cat['price_per_unit']
                    currency = cat['currency']
                    return actPrice_per_unit, currency

        dataBills = {"job_uuid": str(uuid.uuid4()),
            "status": "finished",
            "output": {"bills": []},
            }

        for client in dataClientsBill['input']['clients']:
            key = client['geoinformation'].keys()
            value = client['geoinformation'].values()
            geo = dict(zip(key, value))
            ent = client['entries'] # Contine los cargos del cliente actual

            # Procesamiento de las entradas

            varTotal_value =  0     # Acumulado cantidad recogida por categoría
            varTotal = 0            # Total a pagar
            varPrice_per_unit = 0   # Precio x categoría
            chargesProceess = []
            contaChargesProcess = 0
            actPrice_per_unit = 0

            for i in ent:
                """ Buscar ent (entry) en cargos (charges). Si existe acumular o sumar. Sino: crear o agregar. """

                sw = True
                if contaChargesProcess > 0:     # Verificar si la categoría ya está en los cargos
                    for kv in chargesProceess:
                        if i['tag'] == kv['tag']:
                            varTotal_value = float(kv['total_value']) + float(i['value'])
                            kv['total_value'] = str(varTotal_value)
                            varPrice_per_unit, currency = actCategory(i['tag'])
                            kv['total_price'] = str(round((float(varPrice_per_unit) * varTotal_value), 1))
                            kv["currency"] = currency
                            sw = False
                            break
                
                if sw:
                    chargesProceess.append({})
                    chargesProceess[contaChargesProcess]['total_value'] = i['value']
                    chargesProceess[contaChargesProcess]['unit'] = i['units']
                    chargesProceess[contaChargesProcess]['tag'] = i['tag']
                    varPrice_per_unit, currency = actCategory(i['tag'])   # Buscar los valores de la categoría actual.
                    chargesProceess[contaChargesProcess]["total_price"] = str(round((float(varPrice_per_unit) * float(chargesProceess[contaChargesProcess]['total_value'])), 1))
                    chargesProceess[contaChargesProcess]["currency"] = currency

                    contaChargesProcess += 1

            # Total cargos cliente
            for c in chargesProceess:
                varTotal += float(c['total_price'])

            dataBills["output"]["bills"].append({"start_date": dataClientsBill['start_date'],
                "end_date": dataClientsBill['end_date'],
                "client": {
                    "id": client['id'],
                    "name": client['name'],
                    "code_eco": client['code_eco'],
                    "code_acc": client['code_acc'],
                    "type": client['type'],
                    "status": client['status'],
                    "geoinformation": geo,
                    },
                "charges": chargesProceess,
                "total": str(round(varTotal, 1)),
                "currency": currency
                })

        return Response(dataBills)
