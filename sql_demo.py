import sqlite3
from datetime import datetime

# Підключення до бази даних (в пам'яті)
conn = sqlite3.connect(':memory:')
c = conn.cursor()

# 1) СТВОРЕННЯ БАЗИ ДАНИХ
print("=" * 80)
print("1) СТВОРЕННЯ ТАБЛИЦІ")
print("=" * 80)

c.execute("""CREATE TABLE participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            full_name TEXT,
            status TEXT,
            specialty TEXT,
            gender TEXT,
            birth_year INTEGER,
            participation_form TEXT,
            result_minutes REAL
            )""")

print("✓ Таблиця 'participants' успішно створена\n")

# 2) НАПОВНЕННЯ БАЗИ ДАНИМИ
print("=" * 80)
print("2) ВСТАВКА ДАНИХ (INSERT)")
print("=" * 80)

participants_data = [
    ('08:12:50', 'Іваненко Сергій Павлович', 'Любитель', 'Спортивна медицина', 'Чол.', 1995, 'індивідуальна', 182.5),
    ('08:17:33', 'Марченко Ольга Ігорівна', 'Професіонал', 'Легка атлетика', 'Жін.', 1998, 'командна', 168.3),
    ('08:20:15', 'Петренко Андрій Васильович', 'Любитель', 'Фізична культура', 'Чол.', 1992, 'індивідуальна', 195.7),
    ('08:25:42', 'Коваленко Марина Олексіївна', 'Професіонал', 'Легка атлетика', 'Жін.', 1996, 'командна', 165.2),
    ('08:30:10', 'Шевченко Дмитро Іванович', 'Любитель', 'Спортивна медицина', 'Чол.', 1999, 'індивідуальна', 188.4)
]

c.executemany("""INSERT INTO participants 
                 (time, full_name, status, specialty, gender, birth_year, participation_form, result_minutes)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", participants_data)

conn.commit()
print(f"✓ Додано {len(participants_data)} записів\n")

# 3) ВИКОНАННЯ SELECT ЗАПИТІВ
print("=" * 80)
print("3) SELECT ЗАПИТИ")
print("=" * 80)

# 3.1) Вибрати всіх учасників
print("\n3.1) Всі учасники:")
print("-" * 80)
c.execute("SELECT * FROM participants")
all_participants = c.fetchall()
for row in all_participants:
    print(row)

# 3.2) Вибрати тільки професіоналів
print("\n3.2) Тільки професіонали:")
print("-" * 80)
c.execute("SELECT full_name, status, result_minutes FROM participants WHERE status = 'Професіонал'")
professionals = c.fetchall()
for row in professionals:
    print(f"Ім'я: {row[0]}, Статус: {row[1]}, Результат: {row[2]} хв")

# 3.3) Вибрати учасників, які фінішували швидше за 180 хвилин
print("\n3.3) Учасники з результатом < 180 хвилин:")
print("-" * 80)
c.execute("SELECT full_name, result_minutes FROM participants WHERE result_minutes < 180 ORDER BY result_minutes")
fast_participants = c.fetchall()
for row in fast_participants:
    print(f"Ім'я: {row[0]}, Результат: {row[1]} хв")

# 3.4) Середній результат по статусу
print("\n3.4) Середній результат по статусу:")
print("-" * 80)
c.execute("""SELECT status, AVG(result_minutes) as avg_result, COUNT(*) as count
             FROM participants 
             GROUP BY status""")
avg_by_status = c.fetchall()
for row in avg_by_status:
    print(f"Статус: {row[0]}, Середній час: {row[1]:.2f} хв, Кількість: {row[2]}")

# 3.5) Вибрати учасників жіночої статі
print("\n3.5) Учасниці жіночої статі:")
print("-" * 80)
c.execute("SELECT full_name, specialty, result_minutes FROM participants WHERE gender = 'Жін.'")
females = c.fetchall()
for row in females:
    print(f"Ім'я: {row[0]}, Спеціальність: {row[1]}, Результат: {row[2]} хв")

# 4) ОНОВЛЕННЯ ЗАПИСІВ (UPDATE)
print("\n" + "=" * 80)
print("4) ОНОВЛЕННЯ ДАНИХ (UPDATE)")
print("=" * 80)

# Покращуємо результат Іваненка Сергія
print("\n4.1) Оновлюємо результат Іваненка Сергія з 182.5 на 175.0 хв:")
c.execute("""UPDATE participants 
             SET result_minutes = 175.0 
             WHERE full_name = 'Іваненко Сергій Павлович'""")
conn.commit()
print("✓ Запис оновлено")

# Змінюємо статус Петренка на Професіонал
print("\n4.2) Змінюємо статус Петренка Андрія з 'Любитель' на 'Професіонал':")
c.execute("""UPDATE participants 
             SET status = 'Професіонал' 
             WHERE full_name = 'Петренко Андрій Васильович'""")
conn.commit()
print("✓ Запис оновлено")

# 5) ПЕРЕВІРКА ЗМІН
print("\n" + "=" * 80)
print("5) ПЕРЕВІРКА ЗМІН (повторні SELECT)")
print("=" * 80)

# 5.1) Перевіряємо оновлений результат Іваненка
print("\n5.1) Результат Іваненка Сергія після оновлення:")
print("-" * 80)
c.execute("SELECT full_name, result_minutes FROM participants WHERE full_name = 'Іваненко Сергій Павлович'")
result = c.fetchone()
print(f"Ім'я: {result[0]}, Новий результат: {result[1]} хв")

# 5.2) Перевіряємо кількість професіоналів (має збільшитись)
print("\n5.2) Професіонали після оновлення (тепер їх має бути 3):")
print("-" * 80)
c.execute("SELECT full_name, status FROM participants WHERE status = 'Професіонал'")
professionals_updated = c.fetchall()
for row in professionals_updated:
    print(f"Ім'я: {row[0]}, Статус: {row[1]}")

# 5.3) Оновлена статистика по статусу
print("\n5.3) Оновлена статистика по статусу:")
print("-" * 80)
c.execute("""SELECT status, AVG(result_minutes) as avg_result, COUNT(*) as count
             FROM participants 
             GROUP BY status""")
updated_avg_by_status = c.fetchall()
for row in updated_avg_by_status:
    print(f"Статус: {row[0]}, Середній час: {row[1]:.2f} хв, Кількість: {row[2]}")

# 5.4) Оновлений список швидких учасників
print("\n5.4) Оновлений список учасників з результатом < 180 хв:")
print("-" * 80)
c.execute("SELECT full_name, result_minutes FROM participants WHERE result_minutes < 180 ORDER BY result_minutes")
fast_participants_updated = c.fetchall()
for row in fast_participants_updated:
    print(f"Ім'я: {row[0]}, Результат: {row[1]} хв")

# Закриття з'єднання
conn.close()
print("\n" + "=" * 80)
print("✓ База даних закрита успішно")
print("=" * 80)