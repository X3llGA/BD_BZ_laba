import sqlite3
from sqlite3 import Error
import os
from pathlib import Path

# Ініціалізація морфологічного аналізатора pymorphy3
try:
    import pymorphy3

    morph = pymorphy3.MorphAnalyzer(lang='uk')
    USE_PYMORPHY = True
    print("✓ Морфологічний аналізатор pymorphy3 ініціалізовано")
except ImportError:
    print("⚠ pymorphy3 не встановлено")
    print("→ Встановіть: pip install pymorphy3 pymorphy3-dicts-uk")
    USE_PYMORPHY = False
except Exception as e:
    print(f"⚠ Помилка ініціалізації pymorphy3: {e}")
    USE_PYMORPHY = False

# Ініціалізація токенізатора
try:
    import tokenize_uk as tok

    USE_TOKENIZER = True
    print("✓ Токенізатор tokenize_uk ініціалізовано")
except ImportError:
    print("⚠ tokenize_uk не встановлено")
    print("→ Встановіть: pip install tokenize-uk")
    USE_TOKENIZER = False


class Word:
    def __init__(self, form, lemma, pos, freq):
        self._form = form
        self._lemma = lemma
        self._pos = pos
        self._freq = freq

    @staticmethod
    def from_token(token, freq):
        if USE_PYMORPHY:
            try:
                parsed = morph.parse(token)[0]
                pos = parsed.tag.POS if parsed.tag.POS else 'UNKN'
                return Word(token, parsed.normal_form, pos, freq)
            except Exception as e:
                return Word(token, token, 'ERROR', freq)
        else:
            # Спрощений режим без морфологічного аналізу
            return Word(token, token, 'WORD', freq)

    def show(self):
        print(f"Словоформа: {self._form:20} | Лема: {self._lemma:20} | ЧМ: {self._pos:10} | Частота: {self._freq}")

    def to_tuple(self):
        return (self._form, self._lemma, self._pos, self._freq)


class Sample:
    def __init__(self, text):
        self._text = text
        if USE_TOKENIZER:
            self._tokens = tok.tokenize_words(self._text)
        else:
            # Спрощена токенізація
            import re
            self._tokens = re.findall(r'\b[а-яА-ЯіІїЇєЄґҐa-zA-Z]+\b', self._text)
        self._words_list = [s.lower() for s in self._tokens if s and s[0].isalpha()]

    def get_words(self):
        words_set = set()
        words = []
        for word_str in self._words_list:
            if word_str in words_set:
                continue
            words_set.add(word_str)
            freq = self._words_list.count(word_str)
            words.append(Word.from_token(word_str, freq))
        return words

    def show(self, words):
        for word in words:
            word.show()


class SQL:
    def __init__(self, db_file):
        self._db_file = db_file
        self._connection = None
        self._cursor = None
        self._connect()

    def _connect(self):
        """Підключення до БД з перевіркою"""
        try:
            # Створити директорію, якщо не існує
            db_path = Path(self._db_file)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            self._connection = sqlite3.connect(self._db_file)
            self._cursor = self._connection.cursor()
            print(f"✓ Підключено до БД: {self._db_file}")
        except Error as e:
            print(f"✗ Помилка підключення: {e}")
            raise

    def create_word_freq_table(self):
        """Створення таблиці WordFreq"""
        create_word_freq = '''
        CREATE TABLE IF NOT EXISTS WordFreq (
            word_id INTEGER PRIMARY KEY AUTOINCREMENT,
            form TEXT NOT NULL,
            lemma TEXT NOT NULL,
            pos TEXT,
            freq INTEGER DEFAULT 1
        );
        '''
        try:
            self._cursor.execute(create_word_freq)
            self._connection.commit()
            print("✓ Таблиця WordFreq створена/існує")
        except Error as e:
            print(f"✗ Помилка створення таблиці: {e}")

    def clear_table(self):
        """Очистити таблицю"""
        try:
            self._cursor.execute("DELETE FROM WordFreq")
            self._connection.commit()
            print("✓ Таблиця очищена")
        except Error as e:
            print(f"✗ Помилка очищення: {e}")

    def insert_into_freq_table(self, word):
        """Вставка одного слова"""
        data_tuple = word.to_tuple()
        query = '''
        INSERT INTO WordFreq (form, lemma, pos, freq)
        VALUES(?, ?, ?, ?);
        '''
        try:
            self._cursor.execute(query, data_tuple)
            self._connection.commit()
        except Error as e:
            print(f"✗ Помилка вставки: {e}")

    def generate_word_freq_table(self, words):
        """Створення таблиці та наповнення даними"""
        self.create_word_freq_table()
        print(f"→ Вставка {len(words)} записів...")
        for word in words:
            self.insert_into_freq_table(word)
        print(f"✓ Вставлено {len(words)} записів")

    def select_all(self):
        """SELECT всіх записів"""
        print("\n" + "=" * 80)
        print("ЗАПИТ 1: Всі записи з таблиці")
        print("=" * 80)
        query = "SELECT * FROM WordFreq LIMIT 10;"
        try:
            rows = self._cursor.execute(query).fetchall()
            print(f"{'ID':<5} {'Форма':<20} {'Лема':<20} {'ЧМ':<10} {'Частота':<10}")
            print("-" * 80)
            for row in rows:
                print(f"{row[0]:<5} {row[1]:<20} {row[2]:<20} {row[3] or 'N/A':<10} {row[4]:<10}")

            # Отримати загальну кількість
            total = self._cursor.execute("SELECT COUNT(*) FROM WordFreq").fetchone()[0]
            print(f"→ Показано перші 10 з {total} записів")
        except Error as e:
            print(f"✗ Помилка запиту: {e}")

    def select_pos_freq(self):
        """SELECT кількості слів по частинам мови"""
        print("\n" + "=" * 80)
        print("ЗАПИТ 2: Кількість слів за частинами мови")
        print("=" * 80)
        query = '''
        SELECT
            pos,
            COUNT(word_id) as count
        FROM
            WordFreq
        GROUP BY
            pos
        ORDER BY
            count DESC;
        '''
        try:
            rows = self._cursor.execute(query).fetchall()
            print(f"{'Частина мови':<20} {'Кількість':<10}")
            print("-" * 40)

            # Додати розшифровку частин мови
            pos_names = {
                'NOUN': 'Іменник',
                'VERB': 'Дієслово',
                'ADJF': 'Прикметник',
                'ADJS': 'Прикметник (короткий)',
                'ADVB': 'Прислівник',
                'PREP': 'Прийменник',
                'CONJ': 'Сполучник',
                'PRCL': 'Частка',
                'NPRO': 'Займенник-іменник',
                'PRED': 'Предикатив',
                'INFN': 'Інфінітив',
                'WORD': 'Слово (без аналізу)'
            }

            for row in rows:
                pos_code = row[0] or 'Невідомо'
                pos_name = pos_names.get(pos_code, pos_code)
                print(f"{pos_name:<20} {row[1]:<10}")
        except Error as e:
            print(f"✗ Помилка запиту: {e}")

    def select_top_frequent(self, limit=10):
        """SELECT найчастотніших слів"""
        print("\n" + "=" * 80)
        print(f"ЗАПИТ 3: Топ-{limit} найчастотніших слів")
        print("=" * 80)
        query = f'''
        SELECT
            lemma,
            pos,
            SUM(freq) as total_freq
        FROM
            WordFreq
        GROUP BY
            lemma, pos
        ORDER BY
            total_freq DESC
        LIMIT {limit};
        '''
        try:
            rows = self._cursor.execute(query).fetchall()
            print(f"{'Лема':<25} {'ЧМ':<15} {'Частота':<10}")
            print("-" * 60)
            for row in rows:
                print(f"{row[0]:<25} {row[1] or 'N/A':<15} {row[2]:<10}")
        except Error as e:
            print(f"✗ Помилка запиту: {e}")

    def select_by_pos(self, pos_type):
        """SELECT слів конкретної частини мови"""
        print("\n" + "=" * 80)
        print(f"ЗАПИТ 4: Слова з частиною мови '{pos_type}'")
        print("=" * 80)
        query = '''
        SELECT
            lemma,
            SUM(freq) as total_freq
        FROM
            WordFreq
        WHERE
            pos = ?
        GROUP BY
            lemma
        ORDER BY
            total_freq DESC
        LIMIT 15;
        '''
        try:
            rows = self._cursor.execute(query, (pos_type,)).fetchall()
            if rows:
                print(f"{'Лема':<30} {'Частота':<10}")
                print("-" * 50)
                for row in rows:
                    print(f"{row[0]:<30} {row[1]:<10}")
                print(f"→ Знайдено {len(rows)} записів")
            else:
                print(f"→ Не знайдено слів з частиною мови '{pos_type}'")
        except Error as e:
            print(f"✗ Помилка запиту: {e}")

    def update_freq_multiply(self, multiplier=2):
        """UPDATE: Помножити частоту всіх слів на коефіцієнт"""
        print("\n" + "=" * 80)
        print(f"UPDATE 1: Множення частоти на {multiplier}")
        print("=" * 80)
        query = '''
        UPDATE WordFreq
        SET freq = freq * ?;
        '''
        try:
            self._cursor.execute(query, (multiplier,))
            self._connection.commit()
            print(f"✓ Оновлено {self._cursor.rowcount} записів")
        except Error as e:
            print(f"✗ Помилка оновлення: {e}")

    def update_freq_for_pos(self, pos_type, new_freq):
        """UPDATE: Встановити нову частоту для конкретної частини мови"""
        print("\n" + "=" * 80)
        print(f"UPDATE 2: Встановлення freq={new_freq} для pos='{pos_type}'")
        print("=" * 80)
        query = '''
        UPDATE WordFreq
        SET freq = ?
        WHERE pos = ?;
        '''
        try:
            self._cursor.execute(query, (new_freq, pos_type))
            self._connection.commit()
            print(f"✓ Оновлено {self._cursor.rowcount} записів")
        except Error as e:
            print(f"✗ Помилка оновлення: {e}")

    def update_specific_word(self, lemma, new_freq):
        """UPDATE: Оновити частоту конкретного слова"""
        print("\n" + "=" * 80)
        print(f"UPDATE 3: Встановлення freq={new_freq} для леми '{lemma}'")
        print("=" * 80)
        query = '''
        UPDATE WordFreq
        SET freq = ?
        WHERE lemma = ?;
        '''
        try:
            self._cursor.execute(query, (new_freq, lemma))
            self._connection.commit()
            print(f"✓ Оновлено {self._cursor.rowcount} записів")
        except Error as e:
            print(f"✗ Помилка оновлення: {e}")

    def close(self):
        """Закрити з'єднання"""
        if self._connection:
            self._connection.close()
            print("\n✓ З'єднання з БД закрито")


# ============================================================================
# ГОЛОВНА ПРОГРАМА
# ============================================================================

def main():
    print("\n" + "=" * 80)
    print("СИСТЕМА АНАЛІЗУ ЧАСТОТНОСТІ СЛІВ")
    print("=" * 80)

    # Перевірка наявності файлу з текстом
    text_file = "data/text.txt"
    if not os.path.exists(text_file):
        print(f"\n⚠ Файл '{text_file}' не знайдено!")
        print("→ Створюю тестовий файл з прикладом тексту...")

        # Створити директорію та тестовий файл
        os.makedirs("data", exist_ok=True)
        with open(text_file, "w", encoding="utf-8") as f:
            sample_text = """
            Програмування - це мистецтво створювати програми. 
            Програми допомагають автоматизувати роботу. 
            Розробка програм вимагає знань алгоритмів та структур даних.
            База даних зберігає інформацію. Інформація повинна бути структурованою.
            SQL - мова запитів до бази даних. Запити дозволяють отримати дані.
            Python - популярна мова програмування. Програмування на Python просте та зрозуміле.
            Аналіз тексту допомагає зрозуміти структуру. Структура тексту важлива для обробки.
            Обробка природної мови використовує алгоритми машинного навчання.
            Машинне навчання допомагає вирішувати складні задачі.
            Студенти вивчають програмування в університеті.
            """
            f.write(sample_text)
        print(f"✓ Створено файл '{text_file}' з тестовим текстом\n")

    # Ініціалізація БД
    try:
        sql = SQL('data/freq.db')
    except Exception as e:
        print(f"✗ Критична помилка: {e}")
        return

    # Крок 1: Створення та наповнення БД
    print("\n▶ Крок 1: Створення та наповнення бази даних")
    try:
        with open(text_file, encoding="utf-8", mode="r") as f:
            text = f.read()
            smpl = Sample(text)
            words = smpl.get_words()
            sql.clear_table()
            sql.generate_word_freq_table(words)
    except FileNotFoundError:
        print(f"✗ Помилка: файл '{text_file}' не знайдено")
        sql.close()
        return
    except Exception as e:
        print(f"✗ Помилка обробки тексту: {e}")
        sql.close()
        return

    # Крок 2: SELECT запити (до оновлення)
    print("\n▶ Крок 2-3: Виконання SELECT запитів (ДО оновлення)")
    sql.select_all()
    sql.select_pos_freq()
    sql.select_top_frequent(10)

    # Спробувати знайти іменники (якщо є морфологічний аналіз)
    if USE_PYMORPHY:
        sql.select_by_pos('NOUN')  # Іменники
    else:
        sql.select_by_pos('WORD')

    # Крок 4: UPDATE запити
    print("\n▶ Крок 4: Виконання UPDATE запитів")
    sql.update_freq_multiply(2)  # Помножити всі частоти на 2

    # Крок 5: SELECT запити (після оновлення)
    print("\n▶ Крок 5: Виконання SELECT запитів (ПІСЛЯ оновлення)")
    sql.select_top_frequent(10)
    sql.select_pos_freq()

    # Додаткові UPDATE операції
    if USE_PYMORPHY:
        sql.update_freq_for_pos('VERB', 100)  # Встановити 100 для дієслів
        sql.select_by_pos('VERB')

        # Оновити конкретне слово
        sql.update_specific_word('програмування', 500)
        sql.select_top_frequent(5)
    else:
        # В спрощеному режимі оновимо всі слова
        sql.update_freq_for_pos('WORD', 50)
        sql.select_top_frequent(5)

    # Закриття з'єднання
    sql.close()

    print("\n" + "=" * 80)
    print("ЗАВЕРШЕНО")
    print("=" * 80)

    if not USE_PYMORPHY:
        print("\n💡 ПОРАДА: Для повної функціональності встановіть:")
        print("   pip install pymorphy3 pymorphy3-dicts-uk")


if __name__ == "__main__":
    main()