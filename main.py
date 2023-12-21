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
            # print(item)
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
        # punti_from_officina_single_intervento_for_day = []
        # points_distance_single_intervento_for_day = []
        error_line = st.error("")
        error_line.empty()
        info_line = st.info("")
        info_line.empty()
        load_err_num = 0

        locations = []
        officina = {"id":"OFFICINA", "coords": {"lat": 40.64038085651474, "lng": 14.847294381362609}}
        locations.append(officina)
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
        NUM_H_IN_A_DD = daily_time_slot
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
            if total_time_with_return_to_officina > max_daily_time_slot:
                h_travel, m_travel = divmod(int((point_max_dist_from_officina['time_B_A']) * 60), 60)
                h_total, m_total = divmod(int((total_time_with_return_to_officina) * 60), 60)
                st.success("Per ritornare in officina impieghi " + str(h_travel) + " h e " + str(m_travel) + 
                " min. Oggi hai lavorato per " + str(h_total) + " h e " + str(m_total) + " min.")
                total_time = total_time_with_return_to_officina
            else:
                while total_time <= max_daily_time_slot:
                    # ora parte il check che verifica se sommando il tempo di ritorno in officina sforo il tempo
                    # totale di lavoro quotidiano
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
                                st.info("svolgo l'intervento in: " + str(point_B_min_dist['B']))
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
                        else:
                            points_to_evaluate.remove(point_B_min_dist)
                            break
                    else:
                        break
                        

        #     
        #     print("*****")
        #     print(max_dist_from_officina)
        #     key_to_check = 'to'
        #     value_to_remove = max_dist_from_officina['to']
        #     points_distances = remove_dicts_with_value(points_distances, key_to_check, value_to_remove)
        #     punti_from_officina = remove_dicts_with_value(punti_from_officina, key_to_check, value_to_remove)
        #     print("value_to_remove from officina: " + str(value_to_remove))
        #     punto_attuale_from_officina_time_to_reach = max_dist_from_officina['time_to_reach']

            

        #     time_in_a_day = 0.0
        #     time_in_a_day += max_dist_from_officina['time_to_reach']
        #     print_text = "Dall'officina a " + str(max_dist_from_officina['to'] + " impiego " + str(time_in_a_day) + " ore!")
        #     st.info("Dall'officina a " + str(max_dist_from_officina['to']))
        #     time_in_a_day += max_dist_from_officina['work_time_to']
        #     print_text = "In " + str(max_dist_from_officina['to'] + " resto per " + str(time_in_a_day) + " ore!")
        #     # st.info(print_text)

        #     while time_in_a_day <= NUM_H_IN_A_DD:
        #         can_go_list = []
        #         if (len(points_distances) > 0):
        #             for i, point in enumerate(points_distances):
        #                 if max_dist_from_officina['to'] == point['from']:
        #                     print("posso andare a: " +str(point['to']))
        #                     can_go_list.append(point)
        #             next_location = min(can_go_list, key=lambda x: x['time_to_reach'])
        #             next_location_alternatives = []
        #             while len(can_go_list) > 0:
        #                 next_location_alternative = min(can_go_list, key=lambda x: x['time_to_reach'] + x['work_time_to'] )
        #                 next_location_alternatives.append(next_location_alternative)
        #                 if next_location_alternative in can_go_list:
        #                     can_go_list.remove(next_location_alternative)
                    
        #             time_in_a_day += next_location['time_to_reach']
        #             time_in_a_day += next_location['work_time_to']
        #             max_dist_from_officina = next_location
        #             print_text = "Per andare in " + str(next_location['to']) + " impiego " + str(next_location['time_to_reach']) + " ore!"
        #             print(print_text)
        #             st.info("Da " + str(next_location['from']) + " Vado in " + str(next_location['to']))
        #             print_text = "in " + str(next_location['to'] + " resto per " + str(next_location['work_time_to']) + " ore!")
        #             print(print_text)
        #             # st.info(print_text)

        #             punto_from_officina = extract_dict_by_key_value(punti_from_officina, 'to', next_location['to'])
        #             punti_from_officina_alternativi = []
        #             for next_location_alternative in next_location_alternatives:
        #                 punto_from_officina_alternativo = extract_dict_by_key_value(punti_from_officina, 'to', next_location_alternative['to'])
        #                 punti_from_officina_alternativi.append(punto_from_officina_alternativo)

        #             punto_attuale_from_officina = extract_dict_by_key_value(punti_from_officina, 'to', next_location['from'])
        #             print("PUNTO FROM OFFICINA")
        #             print(punto_from_officina)
        #             print("PUNTO ATTUALE FROM OFFICINA:  next_location['from']: " + str(next_location['from']))
        #             print(punto_attuale_from_officina)
        #             time_from_current_point_to_officina = punto_from_officina['time_to_reach']

        #             if (time_in_a_day+time_from_current_point_to_officina > (NUM_H_IN_A_DD + NUM_H_IN_A_DD*(percentage_of_time_overrun/100))):
        #                 danger_text = "DANGER: se faccio questo lavoro torno a casa dopo " + str(time_in_a_day+time_from_current_point_to_officina) + " ore!"
        #                 print(danger_text)
        #                 # st.text(danger_text)
        #                 danger_text = "DANGER: dato che supera l'orario di lavoro del 15% rientro a casa!"
        #                 print(danger_text)
        #                 # st.text(danger_text)
        #                 hours, minutes = divmod(int((time_in_a_day+time_from_current_point_to_officina) * 60), 60)
        #                 st.error("ATTENTO: se fai l'intervento in " + str(next_location['to']) + " torneresti a casa dopo " + str(hours) + " ore e " + str(minutes) + " minuti! Questo sfora del "+str(percentage_of_time_overrun)+"% l'orario giornaliero!")
        #                 total_time_for_day = time_in_a_day-next_location['time_to_reach']-next_location['work_time_to']
        #                 # total_time_for_day -= punto_attuale_from_officina['time_to_reach']
        #                 total_time_for_day -= punto_attuale_from_officina_time_to_reach
        #                 hours, minutes = divmod(int((total_time_for_day) * 60), 60)
        #                 st.warning("Quindi, lo farai in un altro momento!")
        #                 print("Quindi, lo farai in un altro momento, così torni a casa dopo " + str(hours) + " ore e " + str(minutes) + " minuti!")
                        
        #                 # ritorno al punto precedente in termini di tempo e valuto un'alternativa
        #                 while len(next_location_alternatives) > 0:
        #                     total_alternative = time_in_a_day - next_location['time_to_reach']
        #                     total_alternative -= next_location['work_time_to']
        #                     t1 = next_location_alternatives[0]['time_to_reach']
        #                     t2 = next_location_alternatives[0]['work_time_to']
        #                     total_alternative = total_alternative + t1 + t2 + punti_from_officina_alternativi[0]['time_to_reach']
        #                     if total_alternative < (NUM_H_IN_A_DD + NUM_H_IN_A_DD*(percentage_of_time_overrun/100)):
        #                         hours, minutes = divmod(int(total_alternative * 60), 60)
        #                         st.info("ALTERNATIVA: Vado in " + str(next_location_alternatives[0]['to'] + " e torno a casa dopo: " + str(hours)) + " ore e " + str(minutes) + " minuti. Questo non sfora del "+str(percentage_of_time_overrun)+"% l'orario giornaliero!")
        #                         print("Vado in " + str(next_location_alternatives[0]['to']) + " e torno a casa dopo: " + str(hours) + " ore e " + str(minutes) + " minuti. Questo non sfora del "+str(percentage_of_time_overrun)+"% l'orario giornaliero!")
        #                         time_in_a_day = total_alternative
        #                         next_location = next_location_alternatives[0]
        #                         max_dist_from_officina = next_location
        #                         # st.success(next_location)
        #                         points_distances = remove_dicts_with_value(points_distances, 'to', next_location_alternatives[0]['to'])
        #                         break
        #                     else:
        #                         st.info("Non ci sono alternative sul percorso per oggi! Torna in officina!")
        #                         # st.info("Da " + str(next_location['from']) + " ritorno in officina!")
        #                         break
        #                     next_location_alternatives.pop(0)
        #                     punti_from_officina_alternativi.pop(0)
        #             else:
        #                 key_to_check = 'to'
        #                 value_to_remove = max_dist_from_officina['to']
        #                 points_distances = remove_dicts_with_value(points_distances, key_to_check, value_to_remove)
                        
        #                 if time_in_a_day + time_from_current_point_to_officina <= NUM_H_IN_A_DD:
        #                     hours, minutes = divmod(int(time_in_a_day * 60), 60)
        #                     print_text = "finora ho lavorato " + str(hours) + " ore e " + str(minutes) + " minuti!"
        #                     # st.info(print_text)
        #                     time_if_return =time_in_a_day+time_from_current_point_to_officina
        #                     print_text = "se rientro impiego in totale " + str(time_if_return) + " ore"
        #                     # st.success(print_text)
        #                     print_text = "dato che sono sotto " + str(NUM_H_IN_A_DD) + " ore, continuo a lavorare"
        #                     # st.success(print_text)
        #                 else:
        #                     time_in_a_day += time_from_current_point_to_officina
        #                     hours, minutes = divmod(int(time_in_a_day * 60), 60)
        #                     print_text = "rientro a casa dopo aver lavorato: " + str(hours) + " ore e " + str(minutes) + " minuti!"
        #                     print(print_text)
        #                     st.info(print_text)
        #         else:
        #             print("hai esaurito i punti da raggiungere")
        #             hours, minutes = divmod(int(time_in_a_day * 60), 60)
        #             print_text = "Finora ho lavorato " + str(hours) + " ore e " + str(minutes) + " minuti!"
        #             st.info(print_text)
        #             st.warning("INFO: hai completato tutte le attività in lista, rientra a casa!")
        #             break
        #         # print(next_location)
        #         print("ore giornaliere: " + str(time_in_a_day))
        #     else:
        #         print("Hai raggiunto già le ore giornaliere!")
        
        # for punti in punti_from_officina_single_intervento_for_day:
        #     day += 1
        #     st.header("Giorno " + str(day) + ": singola attività che sfora l'orario giornaliero")
        #     st.info("vai a " + str(punti['to']))



