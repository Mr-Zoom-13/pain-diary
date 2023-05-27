from PyQt5.QtCore import QModelIndex
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QAbstractItemView, QPushButton, QDialog
from PyQt5 import uic
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
import sys
import sqlite3

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main_window.ui', self)

        # CONNECTING TO THE DATABASE
        self.con = sqlite3.connect('base.db')
        self.cur = self.con.cursor()

        #connecting button
        self.btn_new_seizure.clicked.connect(self.open_dialog_new_seizure)

        # table filling
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemClicked.connect(self.on_cell_item_clicked)
        every = self.cur.execute('SELECT * FROM Seizures').fetchall()
        self.table.setRowCount(len(every))
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(['ID', 'Продолжительность(в мин)', 'Интенсивность', 'Симптомы', 'Причины', 'Дата', '-', '-'])
        for i, value in enumerate(every):
            for j, item in enumerate(value):
                self.table.setItem(i, j, QTableWidgetItem(str(item)))
            item_edit = QTableWidgetItem('Редактировать')
            item_edit.setBackground(QColor(255, 179, 0))
            item_delete = QTableWidgetItem('Удалить')
            item_delete.setBackground(QColor(255, 0, 0))
            self.table.setItem(i, len(value), item_edit)
            self.table.setItem(i, len(value) + 1, item_delete)

        # layout location
        # layout = QVBoxLayout()
        # layout.addWidget(self.btn_new_seizure)
        # layout.addWidget(self.table)
        # main_widget = QWidget()
        # main_widget.setLayout(layout)
        # self.setCentralWidget(main_widget)
        self.btn_new_seizure.setFixedWidth(100)

    def open_dialog_new_seizure(self):
        self.form_new_seizure = DialogNewSeizure()
        self.form_new_seizure.show()
        self.form_new_seizure.buttonBox.accepted.connect(self.create_new_seizure)

    def create_new_seizure(self):
        duration = self.form_new_seizure.duration.text()
        strength = self.form_new_seizure.strength.text()
        symptomatic = self.form_new_seizure.symptomatic.text()
        reason = self.form_new_seizure.reason.text()
        try:
            duration = int(duration)
            self.cur.execute('INSERT INTO Seizures(duration, strength, symptomatic, reason) VALUES(?, ?, ?, ?)', (duration, strength, symptomatic, reason))
            self.con.commit()
            cur_row = self.table.rowCount() + 1
            self.table.setRowCount(cur_row)
            cur_row -= 1
            last_id = self.cur.execute('SELECT MAX(id) FROM Seizures LIMIT 1;').fetchone()[0]
            self.table.setItem(cur_row, 0, QTableWidgetItem(str(last_id)))
            self.table.setItem(cur_row, 1, QTableWidgetItem(str(duration)))
            self.table.setItem(cur_row, 2, QTableWidgetItem(strength))
            self.table.setItem(cur_row, 3, QTableWidgetItem(symptomatic))
            self.table.setItem(cur_row, 4, QTableWidgetItem(reason))
            item_edit = QTableWidgetItem('Редактировать')
            item_edit.setBackground(QColor(255, 179, 0))
            item_delete = QTableWidgetItem('Удалить')
            item_delete.setBackground(QColor(255, 0, 0))
            self.table.setItem(cur_row, 5, item_edit)
            self.table.setItem(cur_row, 6, item_delete)
        except ValueError:
            pass

    def on_cell_item_clicked(self, item):
        self.last_id = int(self.table.item(item.row(), 0).text())
        self.row_id = item.row()
        if item.text() == 'Редактировать':
            self.form_new_seizure = DialogNewSeizure()
            self.form_new_seizure.setWindowTitle('Редактирование')
            self.form_new_seizure.duration.setText(self.table.item(item.row(), 1).text())
            self.form_new_seizure.strength.setText(self.table.item(item.row(), 2).text())
            self.form_new_seizure.symptomatic.setText(self.table.item(item.row(), 3).text())
            self.form_new_seizure.reason.setText(self.table.item(item.row(), 4).text())
            self.form_new_seizure.buttonBox.accepted.connect(self.refactor_seizure)
            self.form_new_seizure.show()
        elif item.text() == 'Удалить':
            self.form_delete_seizure = DialogDeleteSeizure()
            self.form_delete_seizure.buttonBox.accepted.connect(self.delete_seizure)
            self.form_delete_seizure.show()

    def delete_seizure(self):
        self.cur.execute('DELETE FROM Seizures WHERE id = ?', (self.last_id,))
        self.con.commit()
        self.table.removeRow(self.row_id)

    def refactor_seizure(self):
        duration = self.form_new_seizure.duration.text()
        strength = self.form_new_seizure.strength.text()
        symptomatic = self.form_new_seizure.symptomatic.text()
        reason = self.form_new_seizure.reason.text()
        try:
            duration = int(duration)
            self.cur.execute('UPDATE Seizures SET duration=?, strength=?, symptomatic=?, reason=? WHERE id=?', (duration, strength, symptomatic, reason, self.last_id))
            self.con.commit()
            self.table.item(self.row_id, 1).setText(str(duration))
            self.table.item(self.row_id, 2).setText(strength)
            self.table.item(self.row_id, 3).setText(symptomatic)
            self.table.item(self.row_id, 4).setText(reason)
        except ValueError:
            pass

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
    form.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
