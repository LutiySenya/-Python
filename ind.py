import os
import hashlib
import sqlite3
from pathlib import Path
def init_db():
    conn = sqlite3.connect('index.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            size INTEGER,
            hash TEXT,
            modified REAL
        )
    ''')
    conn.commit()
    return conn
def get_file_hash(filepath):
    try:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None
def scan_folder(folder):
    results = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)
            try:
                stat = os.stat(path)
                results.append({
                    'path': path,
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                    'hash': get_file_hash(path)
                })
            except:
                continue
    return results
def update_index(conn, folder):
    c = conn.cursor()
    files = scan_folder(folder)
    for f in files:
        c.execute('''
            INSERT OR REPLACE INTO files (path, size, hash, modified)
            VALUES (?, ?, ?, ?)
        ''', (f['path'], f['size'], f['hash'], f['modified']))
    conn.commit()
    print(f"✅ Индекс обновлён: {len(files)} файлов")
def find_duplicates(conn):
    c = conn.cursor()
    c.execute('''
        SELECT hash, COUNT(*), GROUP_CONCAT(path)
        FROM files
        WHERE hash IS NOT NULL
        GROUP BY hash
        HAVING COUNT(*) > 1
    ''')
    duplicates = c.fetchall()
    if not duplicates:
        print("❌ Дубликатов не найдено")
        return

    print("\n🔍 Найдены дубликаты:")
    for hash_val, count, paths in duplicates:
        print(f"\n📁 Хеш: {hash_val[:8]}... ({count} копий)")
        for p in paths.split(','):
            print(f"   - {p}")
def check_backup(conn, backup_folder):
    c = conn.cursor()
    c.execute('SELECT path FROM files')
    indexed = {row[0] for row in c.fetchall()}
    backup_files = set()
    for root, dirs, files in os.walk(backup_folder):
        for file in files:
            backup_files.add(os.path.join(root, file))
    missing = indexed - backup_files
    extra = backup_files - indexed
    print(f"\n💾 Проверка бэкапа в: {backup_folder}")
    print(f"📊 В индексе: {len(indexed)} файлов, в бэкапе: {len(backup_files)}")
    if missing:
        print(f"\n⚠️ Отсутствуют в бэкапе ({len(missing)}):")
        for f in list(missing)[:5]:
            print(f"   - {f}")
        if len(missing) > 5:
            print(f"   ... и ещё {len(missing) - 5}")
    if extra:
        print(f"\n📦 Лишние в бэкапе ({len(extra)}):")
        for f in list(extra)[:5]:
            print(f"   - {f}")
        if len(extra) > 5:
            print(f"   ... и ещё {len(extra) - 5}")
def main():
    conn = init_db()
    while True:
        print("\n" + "=" * 50)
        print("📁 ИНДЕКСАТОР ПАПОК")
        print("1 - Сканировать папку и обновить индекс")
        print("2 - Найти дубликаты")
        print("3 - Проверить резервную копию")
        print("4 - Выход")
        choice = input("Выберите действие: ")
        if choice == '1':
            folder = input("Путь к папке: ")
            if os.path.exists(folder):
                update_index(conn, folder)
            else:
                print("❌ Папка не найдена")
        elif choice == '2':
            find_duplicates(conn)
        elif choice == '3':
            backup = input("Путь к папке с бэкапом: ")
            if os.path.exists(backup):
                check_backup(conn, backup)
            else:
                print("❌ Папка не найдена")
        elif choice == '4':
            conn.close()
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор")
if __name__ == "__main__":
    main()