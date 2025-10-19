import socket
from threading import Thread
import time


HOST = input("Введіть HOST для сервера (натисніть Enter для '0.0.0.0'): ")
if HOST == '':
    HOST = '0.0.0.0' 


PORT = input("Введіть PORT для сервера (натисніть Enter для '8081'): ")
if PORT == '':
    PORT = 8081
else:
    PORT = int(PORT)


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.bind((HOST, PORT))
except Exception as e:
    print(f"*** Не вдалося запустити сервер. Помилка: {e}")
    print("*** Можливо, порт вже зайнятий?")
    exit()

sock.listen(5)
sock.setblocking(False) 

print(f"\n[SERVER] Сервер Agario запущено на {HOST}:{PORT}")
print("[SERVER] Очікую на гравців...")

players = {}
conn_ids = {}
id_counter = 0


def handle_data():
    """
    Головний "ігровий цикл" сервера.
    Обробляє дані, перевіряє зіткнення, розсилає стан гри.
    """
    global id_counter
    while True:
        time.sleep(0.01) 
        player_data = {}
        to_remove = []

        for conn in list(players):
            try:
                data = conn.recv(64).decode().strip()
                if ',' in data:
                    parts = data.split(',')
                    if len(parts) == 5:
                        pid, x, y, r = map(int, parts[:4])
                        name = parts[-1]
                        players[conn] = {'id': pid, 'x': x, 'y': y, 'r': r, 'name': name}
                        player_data[conn] = players[conn]
            except BlockingIOError:
                continue 
            except Exception:
                to_remove.append(conn)
                continue

        eliminated = []
        for conn1 in player_data:
            if conn1 in eliminated: continue
            p1 = player_data[conn1]
            for conn2 in player_data:
                if conn1 == conn2 or conn2 in eliminated: continue
                p2 = player_data[conn2]
                dx, dy = p1['x'] - p2['x'], p1['y'] - p2['y']
                distance = (dx**2 + dy**2)**0.5
                
                if distance < p1['r'] and p1['r'] > p2['r'] * 1.1: 
                    p1['r'] += int(p2['r'] * 0.5)
                    players[conn1] = p1 
                    eliminated.append(conn2) 
                elif distance < p2['r'] and p2['r'] > p1['r'] * 1.1: 
                    p2['r'] += int(p1['r'] * 0.5)
                    players[conn2] = p2
                    eliminated.append(conn1)

        for conn in list(players.keys()):
            if conn in eliminated:
                try:
                    conn.send("LOSE".encode()) 
                except:
                    pass
                to_remove.append(conn) 
                continue

            try:
                packet = '|'.join([f"{p['id']},{p['x']},{p['y']},{p['r']},{p['name']}"
                                   for c, p in players.items() if c != conn and c not in eliminated]) + '|'
                conn.send(packet.encode())
            except:
                to_remove.append(conn)

        for conn in to_remove:
            removed_player = players.pop(conn, None)
            conn_ids.pop(conn, None)
            if removed_player:
                print(f"[SERVER] Гравець {removed_player.get('name', 'ID:'+str(removed_player.get('id')))} від'єднався або був з'їдений.")
            try:
                conn.close() 
            except:
                pass

Thread(target=handle_data, daemon=True).start()

while True:
    try:
        conn, addr = sock.accept()
        conn.setblocking(False)
        id_counter += 1
        
        players[conn] = {'id': id_counter, 'x': 0, 'y': 0, 'r': 20, 'name': f'Player{id_counter}'} 
        conn_ids[conn] = id_counter
        
        conn.send(f"{id_counter},0,0,20".encode())
        print(f"[SERVER] Новий гравець підключився: {addr}, ID: {id_counter}")
        
    except BlockingIOError:
        time.sleep(0.1) 
    except Exception as e:
        print(f"[SERVER] Помилка прийому підключення: {e}")
        time.sleep(0.5)
