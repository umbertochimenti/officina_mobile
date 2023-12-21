private function getTravelTime($address1,$address2,$address1_lat,$address1_long,$address2_lat,$address2_long,$departure_time)  
    { 
        $travel_time_application_id = 'dd2a6475'; 
        $travel_time_api_key = 'bc39c684f9235cce13804cb6f117727a'; 
 
        // CHIAMO TRAVELTIME CON LISTA COORDINATE 
        if($address2==$address1) { 
            $address2 .= ' #'; 
        } 
        $locations = array(); 
        $locations_1 = array("id" => $address1, "coords" => array("lat" => floatval($address1_lat), "lng" => floatval($address1_long))); 
        $locations_2 = array("id" => $address2, "coords" => array("lat" => floatval($address2_lat), "lng" => floatval($address2_long))); 
        $locations[] = $locations_1; 
        $locations[] = $locations_2; 
 
        // Calcolo tratta 
        $departure_searches = array(); 
        $departure_searches['id'] = 'Tratta 1'; 
        $departure_searches['departure_location_id'] = $address1; 
        $departure_searches['arrival_location_ids'] = array($address2); 
        $departure_searches['transportation'] = array("type" => "driving"); 
        $departure_searches['properties'] = array("travel_time","distance","route"); 
        $departure_searches['travel_time'] = 3600; 
        $departure_searches['departure_time'] = $departure_time; 
        
        $url = 'https://api.traveltimeapp.com/v4/time-filter'; 
        $ch = curl_init($url); 
        $payload = json_encode(array("locations" => $locations, "departure_searches" => array($departure_searches))); 
 
        $this->global->log("Input a traveltime: ".$payload); 
 
        curl_setopt($ch, CURLOPT_POSTFIELDS, $payload); 
        curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type:application/json','X-Application-Id: '.$travel_time_application_id,'X-Api-Key: '.$travel_time_api_key)); 
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true); 
        $result = curl_exec($ch); 
        curl_close($ch); 
         
        $this->global->log("Risposta da traveltime: ".$result); 
 
        return $result; 
    }
    