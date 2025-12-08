import requests, time, json

def start_sim():
    payload={
      "friendly_count":5,
      "enemy_count":2,
      "max_time":10,
      "max_speed":70,
      "weapon_range":150,
      "detection_range":1500,
      "swarm_algorithm":"cbba-superiority",
      "assets":[{"position":[0,0,0],"value":1}]
    }
    try:
        r = requests.post('http://127.0.0.1:5000/api/simulation/start', json=payload, timeout=10)
        print('POST status:', r.status_code)
        print('POST resp:', r.text)
        if r.ok:
            data = r.json()
            simid = data.get('simulation_id')
            print('simid:', simid)
            return simid
    except Exception as e:
        print('post error', e)
    return None

if __name__ == '__main__':
    simid = start_sim()
    if simid:
        print('waiting 6s for progress...')
        time.sleep(6)
        try:
            st = requests.get(f'http://127.0.0.1:5000/api/simulation/{simid}/status', timeout=5)
            print('status:', st.status_code, st.text)
        except Exception as e:
            print('status error', e)
        try:
            dbg = requests.get('http://127.0.0.1:5000/api/debug/supabase', timeout=5)
            print('/api/debug/supabase ->', dbg.status_code, dbg.text)
        except Exception as e:
            print('debug supabase error', e)
        try:
            dbg2 = requests.get('http://127.0.0.1:5000/api/debug/simulations', timeout=5)
            print('/api/debug/simulations ->', dbg2.status_code)
            print(dbg2.text)
        except Exception as e:
            print('debug sims error', e)
