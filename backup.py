import sqlite3
import sys

def backup_db(db_path, output_path):
    conn = sqlite3.connect(db_path)
    with open(output_path, 'w') as f:
        for line in conn.iterdump():
            f.write(line + '\n')
    conn.close()
    print(f"Backup saved to {output_path}")

if __name__ == '__main__':
    backup_db('instance/hospital.db', 'database_backup.sql')
