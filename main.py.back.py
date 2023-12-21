# https://github.com/vaclavdekanovsky/data-analysis-in-examples/blob/master/Maps/Driving%20Distance/Driving%20Distance%20between%20two%20places.ipynb
import pandas as pd
import requests
import json
import datetime
import math
import itertools
from geopy import distance
from geopy.geocoders import Nominatim
from geopy.distance import geodesic as GD
import numpy as np
import streamlit as st
import os
import subprocess

# Imposta la variabile d'ambiente
# os.environ['SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL'] = 'True'
# subprocess.run(['pip', 'install', '-r', 'requirements.txt'])
# Esegui l'installazione delle dipendenze
# subprocess.run(['pip', 'install', 'numpy==1.26.2'])
# subprocess.run(['pip', 'install', 'pandas==2.1.4'])
# subprocess.run(['pip', 'install', 'requests==2.31.04'])
# subprocess.run(['pip', 'install', 'geopy==2.4.1'])
# subprocess.run(['pip', 'install', 'scikit-learn==1.3.2'])
# subprocess.run(['pip', 'install', 'mlrose==1.3.0'])
# subprocess.run(['pip', 'install', 'streamlit==1.29.0'])


loc = None


def init_geolocalize():
    global loc
    loc = Nominatim(user_agent="Geopy Library")

def get_geocode_object(address):
    global loc
    return loc.geocode(address, timeout=4)

def get_full_address(geocode_object):
    return geocode_object.address

def get_lat_lon(geocode_object):
    geo_coords = (geocode_object.latitude, geocode_object.longitude)
    return geo_coords

def get_linear_distance_in_km(start, end):
    return round(GD(start, end).km,2)

def remove_dicts_with_value(input_list, key_to_check, value_to_remove):
    return [item for item in input_list if item.get(key_to_check) != value_to_remove]

def extract_dict_by_key_value(input_list, key_to_check, value_to_find):
    for item in input_list:
        if item.get(key_to_check) == value_to_find:
            return item
    return None  # Ritorna None se non viene trovato nessun dizionario con la chiave e il valore specificati

if __name__ == "__main__":
    st.title("mobile_workshop_231218_v_0.1")
    st.header("Test allocazioni: Dati Di Input")
    init_geolocalize()
    address_numbers = st.number_input("Inserisci il numero di indirizzi da esaminare", min_value=3, max_value=200, value=10, step=1)
    daily_time_slot = st.number_input("Inserisci la fascia oraria di lavoro in ore", min_value=4.0, max_value=12.0, value=8.0, step=0.5)
    percentage_of_time_overrun = st.number_input("Inserisci la % massima di sforamento sull'orario giornaliero", min_value=0, max_value=30, value=15, step=1)
    uploaded_file = st.file_uploader("Seleziona il file .csv di partenza (Verifica che gli indirizzi inseriti siano corretti)", type=["csv"])
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        df_used = df.iloc[:address_numbers, [6, 7, 8, 10]] #Indirizzo, CAP, Città, Ore Intervento
        latitude = []
        longitude = []
        addresses = []
        time_in_addresses = []
        punti = []
        officina_garage_start_point = (40.64038085651474, 14.847294381362609)
        punti_from_officina = []
        punti_from_officina_single_intervento_for_day = []
        points_distance_single_intervento_for_day = []
        error_line = st.error("")
        error_line.empty()
        info_line = st.info("")
        info_line.empty()
        load_err_num = 0

        # Crea un nuovo DataFrame vuoto
        df_display_table = pd.DataFrame(columns=['Indirizzo', 'CAP', 'Città', 'Ore Intervento'])

        for i, row in df_used.iterrows():
            address = str(row['Indirizzo'])+', '+str(row['Città'])+', '+str(row['CAP']) + ', ' + 'ITALIA'
            time = str(row['Ore Intervento'])
            geocode_object = get_geocode_object(address)
            if geocode_object is None:
                info_line.empty()
                error_line.error("error on line " + str(i+1) + " for address: " + str(address))
                load_err_num +=1
            else:
                error_line.empty()
                info_line.info("ok, add line " + str(i+1) + " for address: " + str(address))
                lat_lon = get_lat_lon(geocode_object)
                punti.append(lat_lon)
                latitude.append(lat_lon[0])
                longitude.append(lat_lon[1])
                addresses.append(address)
                time_float = float(time.replace(',', '.'))
                time_in_addresses.append(time_float)
                df_display_table = pd.concat([df_display_table, row.to_frame().T], ignore_index=True)
                # df_display_table.append(row, ignore_index=True)
                # print("append " + str(lat_lon) + " lat: " + str(lat_lon[0]) + " lon: " + str(lat_lon[1]))
        if load_err_num > 0:
            st.warning("[WARNING] Geopy Library non ha individuato " + str(load_err_num) + " indirizzi. Si consiglia di passare alle geo-lib google!")
        df_display_table[['lat', 'lon']] = pd.DataFrame(list(zip(latitude, longitude)))
        print(df_display_table)
        df_web_print = df_display_table.iloc[:,[0,1,2,3]]
        # st.text(df_web_print.to_string(index=False,header=False,col_space=35,justify="right"))
        st.table(df_web_print)
        
        points_distances = []
        points_that_have_activity_beyond_daily_hours = []
        for i in range(len(punti)):
            for j in range(len(punti)):
                if i != j:
                    dist = get_linear_distance_in_km(punti[i], punti[j])
                    time_to_reach = (dist * 2)/60 # 0.5 km al minuto
                    point_distance = {"from":addresses[i],
                                        "to":addresses[j],
                                        "distance":dist,
                                        "time_to_reach": round(time_to_reach,2),
                                        "work_time_from":round(time_in_addresses[i],2),
                                        "work_time_to": round(time_in_addresses[j],2)
                                        }
                    #TODO: ci sono punti in cui si permane per più di 8 ore giornaliere .. questi vanno tolti
                    #dal setting e inseriti a parte, come unica attività della giornata, a prescindere dai tempi
                    if point_distance["work_time_from"] >= daily_time_slot or point_distance["work_time_to"] >= daily_time_slot:
                        if point_distance["work_time_from"] >= daily_time_slot:
                            if point_distance['from'] not in points_that_have_activity_beyond_daily_hours:
                                points_that_have_activity_beyond_daily_hours.append(point_distance['from'])
                                st.error("L'indirizzo " + str(point_distance['from']) + " implica un lavoro che va oltre le " + str(daily_time_slot) + " ore!")
                        else:
                            if point_distance['to'] not in points_that_have_activity_beyond_daily_hours:
                                points_that_have_activity_beyond_daily_hours.append(point_distance['to'])
                                st.error("L'indirizzo " + str(point_distance['to']) + " implica un lavoro che va oltre le " + str(daily_time_slot) + " ore!")
                            point_distance_single_intervento_for_day = {
                                            "to":addresses[j],
                                            "distance":dist,
                                            "time_to_reach": round(time_to_reach,2),
                                            "work_time_to": round(time_in_addresses[j],2)
                            }
                            points_distance_single_intervento_for_day.append(point_distance_single_intervento_for_day)
                    else:
                        points_distances.append(point_distance)
                    # print("[INFO] distanza lineare tra il punto " + str(i) + " e il punto " + str(j) + " è: " + str(dist) + " km")
        
        for i in range(len(punti)):
            dist = get_linear_distance_in_km(officina_garage_start_point, punti[i])
            time_to_reach = (dist * 2)/60 # 0.5 km al minuto
            officina_distance = {"to": addresses[i],
                                "distance":dist, 
                                "time_to_reach": round(time_to_reach,2),
                                "work_time_to": round(time_in_addresses[i],2)}

            if officina_distance["work_time_to"] <= daily_time_slot:
                punti_from_officina.append(officina_distance)
            else:
                punti_from_officina_single_intervento_for_day.append(officina_distance)

        day = 0
        while (len(points_distances) > 0):
            day +=1
            st.header("Programmazione attività giorno " + str(day))
            print("PARTE LA PROGRAMMAZIONE GIORNALIERA DEL GIORNO: " + str(day))
            residual_points_to_work = []
            for p in points_distances:
                if p['to'] not in residual_points_to_work:
                    # st.text(p['to'])
                    residual_points_to_work.append(p['to'])
            
            NUM_H_IN_A_DD = daily_time_slot


            #fist_step: calcolo tempi da officina a max_dist (perchè si suppone di partire dal punto più distante)
            
            max_dist_from_officina = max(punti_from_officina, key=lambda x: x['distance'])
            print("*****")
            print(max_dist_from_officina)
            key_to_check = 'to'
            value_to_remove = max_dist_from_officina['to']
            points_distances = remove_dicts_with_value(points_distances, key_to_check, value_to_remove)
            punti_from_officina = remove_dicts_with_value(punti_from_officina, key_to_check, value_to_remove)
            print("value_to_remove from officina: " + str(value_to_remove))
            punto_attuale_from_officina_time_to_reach = max_dist_from_officina['time_to_reach']

            

            time_in_a_day = 0.0
            time_in_a_day += max_dist_from_officina['time_to_reach']
            print_text = "Dall'officina a " + str(max_dist_from_officina['to'] + " impiego " + str(time_in_a_day) + " ore!")
            st.info("Dall'officina a " + str(max_dist_from_officina['to']))
            time_in_a_day += max_dist_from_officina['work_time_to']
            print_text = "In " + str(max_dist_from_officina['to'] + " resto per " + str(time_in_a_day) + " ore!")
            # st.info(print_text)

            while time_in_a_day <= NUM_H_IN_A_DD:
                can_go_list = []
                if (len(points_distances) > 0):
                    for i, point in enumerate(points_distances):
                        if max_dist_from_officina['to'] == point['from']:
                            print("posso andare a: " +str(point['to']))
                            can_go_list.append(point)
                    next_location = min(can_go_list, key=lambda x: x['time_to_reach'])
                    next_location_alternatives = []
                    while len(can_go_list) > 0:
                        next_location_alternative = min(can_go_list, key=lambda x: x['time_to_reach'] + x['work_time_to'] )
                        next_location_alternatives.append(next_location_alternative)
                        if next_location_alternative in can_go_list:
                            can_go_list.remove(next_location_alternative)
                    
                    time_in_a_day += next_location['time_to_reach']
                    time_in_a_day += next_location['work_time_to']
                    max_dist_from_officina = next_location
                    print_text = "Per andare in " + str(next_location['to']) + " impiego " + str(next_location['time_to_reach']) + " ore!"
                    print(print_text)
                    st.info("Da " + str(next_location['from']) + " Vado in " + str(next_location['to']))
                    print_text = "in " + str(next_location['to'] + " resto per " + str(next_location['work_time_to']) + " ore!")
                    print(print_text)
                    # st.info(print_text)

                    punto_from_officina = extract_dict_by_key_value(punti_from_officina, 'to', next_location['to'])
                    punti_from_officina_alternativi = []
                    for next_location_alternative in next_location_alternatives:
                        punto_from_officina_alternativo = extract_dict_by_key_value(punti_from_officina, 'to', next_location_alternative['to'])
                        punti_from_officina_alternativi.append(punto_from_officina_alternativo)

                    punto_attuale_from_officina = extract_dict_by_key_value(punti_from_officina, 'to', next_location['from'])
                    print("PUNTO FROM OFFICINA")
                    print(punto_from_officina)
                    print("PUNTO ATTUALE FROM OFFICINA:  next_location['from']: " + str(next_location['from']))
                    print(punto_attuale_from_officina)
                    time_from_current_point_to_officina = punto_from_officina['time_to_reach']

                    if (time_in_a_day+time_from_current_point_to_officina > (NUM_H_IN_A_DD + NUM_H_IN_A_DD*(percentage_of_time_overrun/100))):
                        danger_text = "DANGER: se faccio questo lavoro torno a casa dopo " + str(time_in_a_day+time_from_current_point_to_officina) + " ore!"
                        print(danger_text)
                        # st.text(danger_text)
                        danger_text = "DANGER: dato che supera l'orario di lavoro del 15% rientro a casa!"
                        print(danger_text)
                        # st.text(danger_text)
                        hours, minutes = divmod(int((time_in_a_day+time_from_current_point_to_officina) * 60), 60)
                        st.error("ATTENTO: se fai l'intervento in " + str(next_location['to']) + " torneresti a casa dopo " + str(hours) + " ore e " + str(minutes) + " minuti! Questo sfora del "+str(percentage_of_time_overrun)+"% l'orario giornaliero!")
                        total_time_for_day = time_in_a_day-next_location['time_to_reach']-next_location['work_time_to']
                        # total_time_for_day -= punto_attuale_from_officina['time_to_reach']
                        total_time_for_day -= punto_attuale_from_officina_time_to_reach
                        hours, minutes = divmod(int((total_time_for_day) * 60), 60)
                        st.warning("Quindi, lo farai in un altro momento!")
                        print("Quindi, lo farai in un altro momento, così torni a casa dopo " + str(hours) + " ore e " + str(minutes) + " minuti!")
                        
                        # ritorno al punto precedente in termini di tempo e valuto un'alternativa
                        while len(next_location_alternatives) > 0:
                            total_alternative = time_in_a_day - next_location['time_to_reach']
                            total_alternative -= next_location['work_time_to']
                            t1 = next_location_alternatives[0]['time_to_reach']
                            t2 = next_location_alternatives[0]['work_time_to']
                            total_alternative = total_alternative + t1 + t2 + punti_from_officina_alternativi[0]['time_to_reach']
                            if total_alternative < (NUM_H_IN_A_DD + NUM_H_IN_A_DD*(percentage_of_time_overrun/100)):
                                hours, minutes = divmod(int(total_alternative * 60), 60)
                                st.info("ALTERNATIVA: Vado in " + str(next_location_alternatives[0]['to'] + " e torno a casa dopo: " + str(hours)) + " ore e " + str(minutes) + " minuti. Questo non sfora del "+str(percentage_of_time_overrun)+"% l'orario giornaliero!")
                                print("Vado in " + str(next_location_alternatives[0]['to']) + " e torno a casa dopo: " + str(hours) + " ore e " + str(minutes) + " minuti. Questo non sfora del "+str(percentage_of_time_overrun)+"% l'orario giornaliero!")
                                time_in_a_day = total_alternative
                                next_location = next_location_alternatives[0]
                                max_dist_from_officina = next_location
                                # st.success(next_location)
                                points_distances = remove_dicts_with_value(points_distances, 'to', next_location_alternatives[0]['to'])
                                break
                            else:
                                st.info("Non ci sono alternative sul percorso per oggi! Torna in officina!")
                                # st.info("Da " + str(next_location['from']) + " ritorno in officina!")
                                break
                            next_location_alternatives.pop(0)
                            punti_from_officina_alternativi.pop(0)
                    else:
                        key_to_check = 'to'
                        value_to_remove = max_dist_from_officina['to']
                        points_distances = remove_dicts_with_value(points_distances, key_to_check, value_to_remove)
                        
                        if time_in_a_day + time_from_current_point_to_officina <= NUM_H_IN_A_DD:
                            hours, minutes = divmod(int(time_in_a_day * 60), 60)
                            print_text = "finora ho lavorato " + str(hours) + " ore e " + str(minutes) + " minuti!"
                            # st.info(print_text)
                            time_if_return =time_in_a_day+time_from_current_point_to_officina
                            print_text = "se rientro impiego in totale " + str(time_if_return) + " ore"
                            # st.success(print_text)
                            print_text = "dato che sono sotto " + str(NUM_H_IN_A_DD) + " ore, continuo a lavorare"
                            # st.success(print_text)
                        else:
                            time_in_a_day += time_from_current_point_to_officina
                            hours, minutes = divmod(int(time_in_a_day * 60), 60)
                            print_text = "rientro a casa dopo aver lavorato: " + str(hours) + " ore e " + str(minutes) + " minuti!"
                            print(print_text)
                            st.info(print_text)
                else:
                    print("hai esaurito i punti da raggiungere")
                    hours, minutes = divmod(int(time_in_a_day * 60), 60)
                    print_text = "Finora ho lavorato " + str(hours) + " ore e " + str(minutes) + " minuti!"
                    st.info(print_text)
                    st.warning("INFO: hai completato tutte le attività in lista, rientra a casa!")
                    break
                # print(next_location)
                print("ore giornaliere: " + str(time_in_a_day))
            else:
                print("Hai raggiunto già le ore giornaliere!")
        
        for punti in punti_from_officina_single_intervento_for_day:
            day += 1
            st.header("Giorno " + str(day) + ": singola attività che sfora l'orario giornaliero")
            st.info("vai a " + str(punti['to']))



