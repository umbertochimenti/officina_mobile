import pandas as pd
import json
import datetime
import math
import numpy as np
import streamlit as st
import os
import subprocess
import geoloc
import asyncio

def remove_dicts_with_value(input_list, key_to_check, value_to_remove):
    return [item for item in input_list if item.get(key_to_check) != value_to_remove]

def extract_dict_by_key_value(input_list, key_to_check, value_to_find):
    for item in input_list:
        if item.get(key_to_check) == value_to_find:
            return item
    return None

def conta_ripetizioni(stringa_da_contare, array_di_stringhe):
    conteggio = 0
    for stringa in array_di_stringhe:
        if stringa == stringa_da_contare:
            conteggio += 1
    return conteggio

if __name__ == "__main__":
    st.title("mobile_workshop_231221_v_0.2")
    st.header("Test allocazioni: Dati Di Input")
    address_numbers = st.number_input("Inserisci il numero di indirizzi da esaminare", min_value=2, max_value=200, value=10, step=1)
    daily_time_slot = st.number_input("Inserisci la fascia oraria di lavoro in ore", min_value=4.0, max_value=12.0, value=8.0, step=0.5)
    percentage_of_time_overrun = st.number_input("Inserisci la % massima di sforamento sull'orario giornaliero", min_value=0, max_value=30, value=15, step=1)
    max_daily_time_slot = (daily_time_slot + daily_time_slot*(percentage_of_time_overrun/100))
    uploaded_file = st.file_uploader("Seleziona il file .csv di partenza (Verifica che gli indirizzi inseriti siano corretti)", type=["csv"])

    if uploaded_file is not None:    
        geoloc.init_geolocalize()
        input_df = pd.read_csv(uploaded_file)
        input_df_used = input_df.iloc[:address_numbers, [6, 7, 8, 10]] #'Indirizzo', 'CAP', 'Città', 'Ore Intervento'
        df_with_coordinates = pd.DataFrame(columns=['Indirizzo', 'CAP', 'Città', 'Ore Intervento'])

        latitude = []
        longitude = []
        addresses = []
        time_in_addresses = []
        punti = []
        punti_from_officina = []
        error_line = st.error("")
        error_line.empty()
        info_line = st.info("")
        info_line.empty()
        load_err_num = 0
        id_point = 0

        for i, row in input_df_used.iterrows():
            address = str(row['Indirizzo'])+', ' +str(row['Città']) + ', ' + 'ITALIA'
            time = str(row['Ore Intervento'])
            geocode_object = geoloc.get_geocode_object(address)
            
            if geocode_object is None:
                info_line.empty()
                error_line.error("error on line " + str(i+1) + " for address: " + str(address))
                load_err_num +=1
            else:
                error_line.empty()
                info_line.info("ok, add line " + str(i+1) + " for address: " + str(address))
                lat_lon = geoloc.get_lat_lon(geocode_object)
                punti.append(lat_lon)
                latitude.append(lat_lon[0])
                longitude.append(lat_lon[1])
                if address in addresses:
                    c = conta_ripetizioni(address, addresses)
                    address += " (" + str(c) + ")"
                addresses.append(address)

                time_float = float(time.replace(',', '.'))
                time_in_addresses.append(time_float)
                df_with_coordinates = pd.concat([df_with_coordinates, row.to_frame().T], ignore_index=True)
        if load_err_num > 0:
            st.warning("[WARNING] TravelTime Library non ha individuato " + str(load_err_num) + " indirizzi!")
        df_with_coordinates[['lat', 'lon']] = pd.DataFrame(list(zip(latitude, longitude)))
        st.table(df_with_coordinates)

        points_to_evaluate = []
        
        for i, punto in enumerate(punti):
            dist = geoloc.get_linear_distance_in_km(geoloc.car_workshop_coords, punto)
            time_to_reach = (dist * 2)/60 # 0.5 km al minuto
            point_from_officina = {
                                "A":"OFFICINA",
                                "B": addresses[i],
                                "time_A_B": round(time_to_reach,2),
                                "time_B_A": round(time_to_reach,2),
                                "work_time_A": -1,
                                "work_time_B":  round(time_in_addresses[i],2),
                                "id_A": -1,
                                "id_B": id_point
                            }
            id_point += 1
            points_to_evaluate.append(point_from_officina)
            punti_from_officina.append(point_from_officina)
        
        for i in range(len(punti)):
            for j in range(len(punti)):
                if i != j:
                    dist = geoloc.get_linear_distance_in_km(punti[i], punti[j])
                    time_to_reach = (dist * 2)/60 # 0.5 km al minuto
                    A = extract_dict_by_key_value(punti_from_officina, "B", addresses[i])
                    B = extract_dict_by_key_value(punti_from_officina, "B", addresses[j])
                    id_A = A['id_B'] 
                    id_B = B['id_B']
                    point_to_evaluate = {
                                "A": addresses[i],
                                "B": addresses[j],
                                "time_A_B": round(time_to_reach,2),
                                "time_B_A": round(time_to_reach,2),
                                "work_time_A": round(time_in_addresses[i],2),
                                "work_time_B": round(time_in_addresses[j],2),
                                "id_A": id_A,
                                "id_B": id_B
                            }
                    points_to_evaluate.append(point_to_evaluate)
        
        # st.table(points_to_evaluate)
        
        day = 0
        officina_points = [point for point in points_to_evaluate if point['A'] == "OFFICINA"]
        # st.info(officina_points)
        
        while len(points_to_evaluate) > 0:
            # si parte dal giorno 1, con orario giornaliero pari a 0 e la lista dei punti percorsi in giornata è vuota
            day +=1
            total_time = 0.0
            day_points = []
            daily_point_yet_examinate = []
            st.header("Programmazione attività giorno " + str(day))
            print("PARTE LA PROGRAMMAZIONE GIORNALIERA DEL GIORNO: " + str(day))
            # primo passaggio: calcolo i tempi da officina a max_dist (perchè si suppone di partire dal punto più distante)
            officina_points = [point for point in points_to_evaluate if point['A'] == "OFFICINA"]
            point_max_dist_from_officina = max(officina_points, key=lambda x: x['time_A_B'])
            # sommo a tempo totale il tempo necessario per raggiungere il punto più distante e il tempo dell'intervento
            h_travel, m_travel = divmod(int((point_max_dist_from_officina['time_A_B']) * 60), 60)
            h_work, m_work = divmod(int((point_max_dist_from_officina['work_time_B']) * 60), 60)
            total_time += point_max_dist_from_officina['time_A_B']
            total_time += point_max_dist_from_officina['work_time_B']
            h_total, m_total = divmod(int((total_time) * 60), 60)
            st.info("Dall'officina, vado in " + str(point_max_dist_from_officina['B']) + " impiegando " + 
                    str(h_travel) + " h e " + str(m_travel) + " min. Qui lavoro per " + str(h_work) + 
                    " h e " + str(m_work) + " min. Finora ho lavorato per " + str(h_total) + " ore e " + 
                    str(m_total) + " min.")
                
            # rimuovo dalla lista dei punti da valutare e dalla lista dei punti rispetto all'officina
            # il punto già percorso e lo aggiungo nella lista dei punti giornalieri
            points_to_evaluate.remove(point_max_dist_from_officina)
            points_that_end_with_point_max_dist_from_officina = [point for point in points_to_evaluate if point['B'] == point_max_dist_from_officina['B']]
            
            # rimuovo tutti i punti che terminano con il punto appena inserito in lista
            # perchè ho già svolto qui l'intervento
            for point_to_remove in points_that_end_with_point_max_dist_from_officina:
                if point_to_remove in points_to_evaluate:
                    points_to_evaluate.remove(point_to_remove)

            officina_points.remove(point_max_dist_from_officina)
            day_points.append(point_max_dist_from_officina)

            total_time_with_return_to_officina = total_time + point_max_dist_from_officina['time_B_A']
            h_total_p, m_total_p = divmod(int((total_time_with_return_to_officina) * 60), 60)
            st.success("Con il rientro in officina sarei fuori da " + str(h_total_p) + " h e " + str(m_total_p) + " min!")
            if total_time_with_return_to_officina > max_daily_time_slot:
                h_travel, m_travel = divmod(int((point_max_dist_from_officina['time_B_A']) * 60), 60)
                h_total, m_total = divmod(int((total_time_with_return_to_officina) * 60), 60)
                st.success("Per ritornare in officina impieghi " + str(h_travel) + " h e " + str(m_travel) + 
                " min. Oggi hai lavorato per " + str(h_total) + " h e " + str(m_total) + " min.")
                total_time = total_time_with_return_to_officina
            else:
                while total_time <= max_daily_time_slot:
                    # ora parte il check che verifica se sommando il tempo di ritorno 
                    # in officina sforo il tempo totale di lavoro quotidiano
                    # prendo il punto che minimizza la distanza rispetto al punto attuale
                    # sarà il punto in cui effettuerò il prossimo lavoro
                    points_linked_to_A = [point for point in points_to_evaluate if point['A'] == day_points[-1]['B'] and point not in daily_point_yet_examinate]
                    if len(points_linked_to_A) > 0:
                        point_B_min_dist = min(points_linked_to_A, key=lambda x: x['time_A_B'])
                        # st.text(point_B_min_dist)

                        # sommo a tempo totale possibile il tempo necessario per raggiungere il punto e 
                        # il tempo dell'intervento. Non confermo in questa fase il punto, perchè potrei sforare l'orario
                        # massimo.
                        h_travel, m_travel = divmod(int((point_B_min_dist['time_A_B']) * 60), 60)
                        h_work, m_work = divmod(int((point_B_min_dist['work_time_B']) * 60), 60)
                        possible_total_time = total_time
                        possible_total_time += point_B_min_dist['time_A_B']
                        possible_total_time += point_B_min_dist['work_time_B']
                        h_total, m_total = divmod(int((possible_total_time) * 60), 60)
                        # st.warning("Da " + str(point_B_min_dist['A']) + " potrei andare in " + 
                        #         str(point_B_min_dist['B']) + " impiegando " + 
                        #         str(h_travel) + " h e " + str(m_travel) + " min. Qui lavoro per " + str(h_work) + 
                        #         " h e " + str(m_work) + " min. Facendo così lavorerei per " + str(h_total) + " ore e " + 
                        #         str(m_total) + " min.")
                        
                        # st.text(officina_points)
                        # st.text(point_B_min_dist['B'])
                        point_B_min_dist_from_officina = extract_dict_by_key_value(officina_points,'B',point_B_min_dist['B'])
                        if point_B_min_dist_from_officina != None:
                            # st.info(point_B_min_dist_from_officina)
                            possible_total_time += point_B_min_dist_from_officina['time_B_A']

                            if possible_total_time > max_daily_time_slot:
                                # st.error("Il tempo è eccessivo. Valuto un'alternativa!")
                                daily_point_yet_examinate.append(point_B_min_dist)
                            else:
                                st.info("intervento di " + str(point_B_min_dist['work_time_B']) + " ore in: " + str(point_B_min_dist['B']))
                                points_to_evaluate.remove(point_B_min_dist)
                                day_points.append(point_B_min_dist)

                                # rimuovo da points_to_evaluate tutti i nodi che partono dal punto corrente
                                for point_to_remove in points_linked_to_A:
                                    if point_to_remove in points_to_evaluate:
                                        points_to_evaluate.remove(point_to_remove)
                                
                                # rimuovo da points_to_evaluate tutti i nodi dei lavori già svolti oggi
                                for point_to_remove in day_points:
                                    if point_to_remove in points_to_evaluate:
                                        points_to_evaluate.remove(point_to_remove)
                                
                                # rimuovo da points_to_evaluate tutti i nodi che finiscono nel punto corrente
                                points_linked_to_B = [point for point in points_to_evaluate if point['B'] == point_B_min_dist['B']]

                                for point_to_remove in points_linked_to_B:
                                    if point_to_remove in points_to_evaluate:
                                        points_to_evaluate.remove(point_to_remove)
                                
                                # st.text(points_to_evaluate)
                                
                                # aggiorno il tempo totale del giorno
                                total_time += point_B_min_dist['time_A_B']
                                total_time += point_B_min_dist['work_time_B']
                                h_total, m_total = divmod(int((total_time) * 60), 60)
                                st.success("Finora ho lavorato " + str(h_total) + " h e " + str(m_total) + " min!")
                                tot_time_with_return_in_officina = total_time + point_B_min_dist_from_officina['time_B_A'] 
                                h_total_p, m_total_p = divmod(int((tot_time_with_return_in_officina) * 60), 60)
                                st.success("Con il rientro in officina sarei fuori da " + str(h_total_p) + " h e " + str(m_total_p) + " min!")
                        else:
                            points_to_evaluate.remove(point_B_min_dist)
                            break
                    else:
                        break
