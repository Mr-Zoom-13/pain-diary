from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidget, QTableWidgetItem, \
    QVBoxLayout, QWidget, QAbstractItemView, QPushButton, QDialog
from PyQt5 import uic
from PyQt5.QtGui import QColor, QPixmap
import sys
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main_window.ui', self)

        # CONNECTING TO THE DATABASE
        self.con = sqlite3.connect('base.db')
        self.cur = self.con.cursor()

        # connecting button
        self.btn_new_seizure.clicked.connect(self.open_dialog_new_seizure)

        # settings for table and button
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemClicked.connect(self.on_cell_item_clicked)
        self.btn_new_seizure.setFixedWidth(100)

        # filling table
        self.fill_table()

        # Connecting combobox
        self.table_filter.currentTextChanged.connect(self.fill_table)

        # Connecting saving graphs
        self.create_graph.clicked.connect(self.save_graphs)

        # Filling graphs
        self.save_graphs()

    def fill_table(self):
        self.table.clearContents()
        if self.table_filter.currentText() == '-':
            every = self.cur.execute('SELECT * FROM Seizures').fetchall()
        elif self.table_filter.currentText() == 'Дате':
            every = self.cur.execute('SELECT * FROM Seizures ORDER BY date').fetchall()
        elif self.table_filter.currentText() == 'Продолжительности':
            every = self.cur.execute('SELECT * FROM Seizures ORDER BY duration').fetchall()
        elif self.table_filter.currentText() == 'Интенсивности':
            every = self.cur.execute('SELECT * FROM Seizures ORDER BY strength').fetchall()
        self.table.setRowCount(len(every))
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ['ID', 'Продолжительность(в мин)', 'Интенсивность', 'Симптомы', 'Причины', 'Дата',
             '-', '-'])
        for i, value in enumerate(every):
            for j, item in enumerate(value):
                self.table.setItem(i, j, QTableWidgetItem(str(item)))
            item_edit = QTableWidgetItem('Редактировать')
            item_edit.setBackground(QColor(255, 179, 0))
            item_delete = QTableWidgetItem('Удалить')
            item_delete.setBackground(QColor(255, 0, 0))
            self.table.setItem(i, len(value), item_edit)
            self.table.setItem(i, len(value) + 1, item_delete)
        self.table.resizeColumnsToContents()

    def open_dialog_new_seizure(self):
        self.form_new_seizure = DialogNewSeizure()
        self.form_new_seizure.date_time.setDateTime(datetime.now())
        self.form_new_seizure.show()
        self.form_new_seizure.buttonBox.accepted.connect(self.create_new_seizure)

    def create_new_seizure(self):
        duration = self.form_new_seizure.duration.text()
        strength = self.form_new_seizure.strength.text()
        symptomatic = self.form_new_seizure.symptomatic.text()
        reason = self.form_new_seizure.reason.text()
        date = self.form_new_seizure.date_time.dateTime().toPyDateTime()
        new_date = f'{date.year}-{date.month}-{date.day} {date.hour}:{date.minute}'
        try:
            duration = int(duration)
            self.cur.execute(
                'INSERT INTO Seizures(duration, strength, symptomatic, reason, date) VALUES(?, ?, ?, ?, ?)',
                (duration, strength, symptomatic, reason, new_date))
            self.con.commit()
            self.fill_table()
        except ValueError:
            pass

    def on_cell_item_clicked(self, item):
        self.last_id = int(self.table.item(item.row(), 0).text())
        if item.text() == 'Редактировать':
            self.form_new_seizure = DialogNewSeizure()
            self.form_new_seizure.setWindowTitle('Редактирование')
            self.form_new_seizure.duration.setText(self.table.item(item.row(), 1).text())
            self.form_new_seizure.strength.setText(self.table.item(item.row(), 2).text())
            self.form_new_seizure.symptomatic.setText(self.table.item(item.row(), 3).text())
            self.form_new_seizure.reason.setText(self.table.item(item.row(), 4).text())
            self.form_new_seizure.date_time.setDateTime(
                datetime.strptime(self.table.item(item.row(), 5).text(), '%Y-%m-%d %H:%M'))
            self.form_new_seizure.buttonBox.accepted.connect(self.refactor_seizure)
            self.form_new_seizure.show()
        elif item.text() == 'Удалить':
            self.form_delete_seizure = DialogDeleteSeizure()
            self.form_delete_seizure.buttonBox.accepted.connect(self.delete_seizure)
            self.form_delete_seizure.show()

    def delete_seizure(self):
        self.cur.execute('DELETE FROM Seizures WHERE id = ?', (self.last_id,))
        self.con.commit()
        self.fill_table()

    def refactor_seizure(self):
        duration = self.form_new_seizure.duration.text()
        strength = self.form_new_seizure.strength.text()
        symptomatic = self.form_new_seizure.symptomatic.text()
        reason = self.form_new_seizure.reason.text()
        date = self.form_new_seizure.date_time.dateTime().toPyDateTime()
        new_date = f'{date.year}-{date.month}-{date.day} {date.hour}:{date.minute}'
        try:
            duration = int(duration)
            self.cur.execute(
                'UPDATE Seizures SET duration=?, strength=?, symptomatic=?, reason=?, date=? WHERE id=?',
                (duration, strength, symptomatic, reason, new_date, self.last_id))
            self.con.commit()
            self.fill_table()
        except ValueError:
            pass

    def save_graphs(self):
        every = self.cur.execute('SELECT * FROM Seizures ORDER BY date').fetchall()
        if len(every):
            dates = [every[-1][5].split(' ')[0]]
            values_frequency = [1]
            values_duration = []
            cur = every[-1][1]
            length = 1
            itog = 7
            i = len(every) - 2
            while itog:
                if every[i][5].split(' ')[0] == dates[-1]:
                    values_frequency[-1] += 1
                    cur += every[i][1]
                    length += 1
                else:
                    dates.append(every[i][5].split(' ')[0])
                    values_frequency.append(1)
                    values_duration.append(round(cur / length, 1))
                    cur = every[i][1]
                    length = 1
                    itog -= 1
                i -= 1
                if i < 0:
                    break
            values_duration.append(round(cur / length, 1))
            dates = dates[::-1]
            values_frequency = values_frequency[::-1]
            values_duration = values_duration[::-1]
            plt.clf()
            plt.plot(dates, values_frequency)
            plt.title('Частота')
            plt.savefig('saved_figure_frequency.png')
            plt.clf()
            plt.plot(dates, values_duration)
            plt.title('Продолжительность(в мин)')
            plt.savefig('saved_figure_duration.png')
            pix_frequency = QPixmap('saved_figure_frequency.png')
            self.graph_frequency.setPixmap(pix_frequency)
            self.graph_frequency.setScaledContents(True)
            pix_duration = QPixmap('saved_figure_duration.png')
            self.graph_duration.setPixmap(pix_duration)
            self.graph_duration.setScaledContents(True)


class DialogNewSeizure(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('dialog_new_seizure.ui', self)


class DialogDeleteSeizure(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('dialog_delete_seizure.ui', self)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = MainWindow()
    form.setFixedSize(721, 600)
    form.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
