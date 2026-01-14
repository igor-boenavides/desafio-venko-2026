#!/usr/bin/env python3

# Função: Script Python que coleta métricas do sistema e salva no banco.

import psycopg2
import time
import os
import subprocess
import socket
from datetime import datetime

"""Monitoramento de banco de dados com failover e coleta de métricas do host"""
class DatabaseMonitor:
    def __init__(self):
        self.db_primary_host = os.getenv('DB_PRIMARY_HOST', 'db-primary')
        self.db_standby_host = os.getenv('DB_STANDBY_HOST', 'db-standby')
        self.db_user = os.getenv('DB_USER', 'admin')
        self.db_password = os.getenv('DB_PASSWORD', 'admin123')
        self.db_name = os.getenv('DB_NAME', 'monitoring')
        self.active_db = None
        
    def get_connection(self):
        """Tenta conectar ao banco primário, se falhar, conecta ao standby"""
        try:
            conn = psycopg2.connect(
                host=self.db_primary_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                connect_timeout=3
            )
            self.active_db = 'primary'
            return conn
        except Exception as e:
            print(f"Primary DB unavailable: {e}. Trying standby...")
            try:
                conn = psycopg2.connect(
                    host=self.db_standby_host,
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_password,
                    connect_timeout=3
                )
                self.active_db = 'standby'
                return conn
            except Exception as e2:
                print(f"Standby DB also unavailable: {e2}")
                return None

    def get_cpu_usage(self):
        """Coleta uso de CPU do host"""
        try:
            with open('/host/proc/stat', 'r') as f:
                cpu_line = f.readline()
            cpu_values = [float(x) for x in cpu_line.split()[1:]]
            
            total1 = sum(cpu_values)
            idle1 = cpu_values[3]
            
            time.sleep(1)
            
            with open('/host/proc/stat', 'r') as f:
                cpu_line = f.readline()
            cpu_values = [float(x) for x in cpu_line.split()[1:]]
            
            total2 = sum(cpu_values)
            idle2 = cpu_values[3]
            
            total_diff = total2 - total1
            idle_diff = idle2 - idle1
            
            cpu_usage = 100 * (1 - idle_diff / total_diff) if total_diff > 0 else 0
            return round(cpu_usage, 2)
        except Exception as e:
            print(f"Error reading CPU: {e}")
            return 0.0

    def get_memory_usage(self):
        """Coleta uso de memória do host"""
        try:
            with open('/host/proc/meminfo', 'r') as f:
                lines = f.readlines()
            
            mem_info = {}
            for line in lines:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = int(parts[1].strip().split()[0])
                    mem_info[key] = value
            
            total = mem_info.get('MemTotal', 0) * 1024
            available = mem_info.get('MemAvailable', 0) * 1024
            used = total - available
            
            usage_percent = (used / total * 100) if total > 0 else 0
            
            return round(usage_percent, 2), total, used
        except Exception as e:
            print(f"Error reading memory: {e}")
            return 0.0, 0, 0

    def get_host_ip(self):
        """Obtém IP do host"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            print(f"Error getting IP: {e}")
            return "Unknown"

    def get_ping_latency(self):
        """Mede latência de ping para google.com"""
        try:
            result = subprocess.run(
                ['ping', '-c', '3', '-W', '2', 'google.com'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout
                for line in output.split('\n'):
                    if 'avg' in line or 'rtt' in line:
                        parts = line.split('=')
                        if len(parts) > 1:
                            times = parts[1].split('/')
                            if len(times) >= 2:
                                avg_time = float(times[1].strip().split()[0])
                                return round(avg_time, 2)
            return 0.0
        except Exception as e:
            print(f"Error measuring ping: {e}")
            return 0.0

    def store_metrics(self):
        """Coleta e armazena métricas no banco de dados"""
        conn = self.get_connection()
        if not conn:
            print("No database connection available")
            return
        
        try:
            cpu_usage = self.get_cpu_usage()
            mem_usage, mem_total, mem_used = self.get_memory_usage()
            host_ip = self.get_host_ip()
            ping_latency = self.get_ping_latency()
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO host_metrics 
                (cpu_usage, memory_usage, memory_total, memory_used, host_ip, ping_latency)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (cpu_usage, mem_usage, mem_total, mem_used, host_ip, ping_latency))
            
            cursor.execute("""
                DELETE FROM host_metrics 
                WHERE id NOT IN (
                    SELECT id FROM host_metrics 
                    ORDER BY timestamp DESC 
                    LIMIT 100
                )
            """)
            
            conn.commit()
            cursor.close()
            
            print(f"[{datetime.now()}] Metrics stored in {self.active_db} DB - "
                  f"CPU: {cpu_usage}%, MEM: {mem_usage}%, IP: {host_ip}, Ping: {ping_latency}ms")
            
        except Exception as e:
            print(f"Error storing metrics: {e}")
        finally:
            conn.close()

    def run(self):
        """Loop principal de monitoramento"""
        print("Starting monitoring system...")
        time.sleep(10)
        
        while True:
            try:
                self.store_metrics()
                time.sleep(60)
            except KeyboardInterrupt:
                print("\nMonitoring stopped")
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    monitor = DatabaseMonitor()
    monitor.run()