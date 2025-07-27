import requests
import json
import random
import sqlite3
import logging
import html
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime

logging.basicConfig(filename='quiz_app.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

DB_NAME = 'leaderboard.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard (
                    username TEXT,
                    score INTEGER,
                    timestamp TEXT
                )''')
    conn.commit()
    conn.close()


def save_score(username, score):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO leaderboard (username, score, timestamp) VALUES (?, ?, ?)",
              (username, score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def get_top_scores():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT username, score, timestamp FROM leaderboard ORDER BY score DESC LIMIT 5")
    rows = c.fetchall()
    conn.close()
    return rows


def fetch_questions(amount=15, category=10, difficulty='hard', qtype='multiple'):
    url = f"https://opentdb.com/api.php?amount={amount}&category={category}&difficulty={difficulty}&type={qtype}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data['response_code'] != 0:
            raise Exception("API returned invalid response")
        questions = data['results']
        for q in questions:
            q['question'] = html.unescape(q['question'])
            q['correct_answer'] = html.unescape(q['correct_answer'])
            q['incorrect_answers'] = [html.unescape(ans) for ans in q['incorrect_answers']]
        logging.info("Fetched questions successfully")
        return questions
    except Exception as e:
        logging.error(f"Error fetching questions: {e}")
        messagebox.showerror("Error", f"Failed to fetch questions: {e}")
        return []

class QuizApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Trivia Quiz App")
        self.score = 0
        self.q_index = 0
        self.questions = []
        self.username = simpledialog.askstring("Username", "Enter your name:")
        self.start_quiz()

    def start_quiz(self):
        
        self.questions = fetch_questions(amount=15)
        if not self.questions:
            self.master.destroy()
            return

        self.score = 0
        self.q_index = 0

        self.label_question = tk.Label(self.master, wraplength=400, justify="left")
        self.label_question.pack(pady=20)

        self.buttons = []
        for _ in range(4):
            btn = tk.Button(self.master, width=50, command=lambda b=_: self.check_answer(b))
            btn.pack(pady=5)
            self.buttons.append(btn)

        self.load_question()

    def load_question(self):
        q = self.questions[self.q_index]
        self.label_question.config(text=f"Q{self.q_index + 1}: {q['question']}")

        options = q['incorrect_answers'] + [q['correct_answer']]
        random.shuffle(options)

        for i, opt in enumerate(options):
            self.buttons[i].config(text=opt)
        self.correct_answer = q['correct_answer']

    def check_answer(self, idx):
        selected = self.buttons[idx].cget('text')
        if selected == self.correct_answer:
            self.score += 1
            messagebox.showinfo("Correct", "That's correct!")
        else:
            messagebox.showinfo("Incorrect", f"Wrong! Correct answer: {self.correct_answer}")

        self.q_index += 1
        if self.q_index < len(self.questions):
            self.load_question()
        else:
            self.show_result()

    def show_result(self):
        save_score(self.username, self.score)
        msg = f"Quiz completed!\nYour score: {self.score}/15\n\nTop 5 Scores:\n"
        for rank, (uname, scr, ts) in enumerate(get_top_scores(), 1):
            msg += f"{rank}. {uname} - {scr} ({ts})\n"
        messagebox.showinfo("Result", msg)
        self.master.destroy()

if __name__ == '__main__':
    init_db()
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()
0
