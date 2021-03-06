from pprint import pprint
import numpy as np
from operator import attrgetter
import sys
from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.animation as animation
import random


class State:
    def __init__(self, name, u, v, m, p):
        self.name = name
        self.u = u
        self.v = v
        self.m = m
        self.p = p
        self.r = round(self.u / self.v, 2)
        if self.v > 0:
            self.opt_v = 1
        elif self.v < 0:
            self.opt_v = 0

    def update_u(self, u):
        self.u = u
        self.r = round(self.u / self.v, 2)


class Window(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        # a figure instance to plot on
        self.figure = Figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Just some button connected to `plot` method
        self.randomize_button = QtGui.QPushButton('Randomize')
        self.plot_button = QtGui.QPushButton('Plot')
        self.change_rep_button = QtGui.QPushButton('Change Rep')
        self.find_alpha_button = QtGui.QPushButton('Find alpha')
        self.randomize_button.clicked.connect(self.randomizeButton)
        self.plot_button.clicked.connect(self.plotButton)
        self.change_rep_button.clicked.connect(self.changeRepButton)
        self.find_alpha_button.clicked.connect(self.FindAlphaRepButton)

        # set the layout
        layout = QtGui.QVBoxLayout()
        inputLayout = QtGui.QGridLayout()
        outputLayout = QtGui.QGridLayout()
        self.inputs = {'m':{},'v':{},'u':{}}
        self.outputs = {'r':{}}
        for j in range(1, 9):
            field = QtGui.QLabel(str(j))
            inputLayout.addWidget(field, 1, j + 1)
        for i in range(1, 4):
            field = QtGui.QLabel(['', 'Receiver', 'Sender', 'Representative'][i])
            inputLayout.addWidget(field, i + 1, 1)
            for j in range(1, 9):
                field = QtGui.QDoubleSpinBox()
                field.setSingleStep(0.1)
                field.setMinimum(-20)
                field.setMaximum(20)
                if i != 3:
                    value = 0
                    while value == 0:
                        value = round(random.uniform(-20,20),0)
                    field.setValue(value)
                else:
                    field.setValue(self.inputs['m'][j].value())
                # field.setAlignment(QtCore.Qt.AlignRight)
                field.setFont(QtGui.QFont("Ariel", 16))
                inputLayout.addWidget(field, i + 1, j + 1)
                self.inputs[['m','v','u'][i-1]][j] = field
        # display r
        outputLayout.addWidget(QtGui.QLabel('r'), 1, 1)
        for j in range(1, 9):
            field = QtGui.QLabel()
            # field.setAlignment(QtCore.Qt.AlignRight)
            field.setFont(QtGui.QFont("Ariel", 16))
            outputLayout.addWidget(field, 1, j + 1)
            self.outputs['r'][j] = field
        # display f(w*) and alpha
        outputLayout.addWidget(QtGui.QLabel('f(w*)'), 2, 1)
        self.outputs['f(w*)'] = QtGui.QLabel()
        self.outputs['f(w*)'].setFont(QtGui.QFont("Ariel", 16))
        outputLayout.addWidget(self.outputs['f(w*)'], 2, 2)
        outputLayout.addWidget(QtGui.QLabel('alpha'), 3, 1)
        self.outputs['alpha'] = QtGui.QDoubleSpinBox()
        self.outputs['alpha'].setSingleStep(0.01)
        self.outputs['alpha'].setMinimum(0)
        self.outputs['alpha'].setMaximum(1)
        self.outputs['alpha'].setFont(QtGui.QFont("Ariel", 16))
        outputLayout.addWidget(self.outputs['alpha'], 3, 2)
        outputLayout.addWidget(self.change_rep_button, 3, 3)
        outputLayout.addWidget(self.find_alpha_button, 3, 4)
        # set layouts
        layout.addWidget(self.toolbar)
        layout.addWidget(self.randomize_button)
        layout.addLayout(inputLayout)
        layout.addLayout(outputLayout)
        layout.addWidget(self.plot_button)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.plotButton()


    def FindAlphaRepButton(self):
        print 'test'

    def changeRepButton(self):
        for i, state in enumerate(self.states_sorted):
            if i != self.num_of_sender_states:
                # iterative version
                # state.update_u(state.u * (1-self.outputs['alpha'].value()) +
                #                self.states_sorted[self.num_of_sender_states-1].u * self.outputs['alpha'].value())
                # non iterative version
                state.update_u(state.u * (1-self.outputs['alpha'].value())
                               - state.v * self.outputs['alpha'].value())
                self.inputs['u'][state.name].setValue(state.u)
        self.plotButton()


    def randomizeButton(self):
        for player in self.inputs.keys():
            if player != 'u':
                for state_name in self.inputs[player].keys():
                    value = 0
                    while value == 0:
                        value = round(random.uniform(-20, 20), 2)
                    self.inputs[player][state_name].setValue(value)
            for state_name in self.inputs['u'].keys():
                    self.inputs['u'][state_name].setValue(self.inputs['m'][state_name].value())
        self.plotButton()


    def findRecommendation(self):
        # sort states by r
        self.states_sorted = sorted(self.states, key=attrgetter('r'), reverse=True)
        # calculate payoffs for different deterministic recommendations
        self.v_sums, self.u_sums, self.m_sums = [], [], []
        self.v_sum_action1 = sum(state.v for state in self.states_sorted)
        self.u_sum_action1 = sum(state.u for state in self.states_sorted)
        self.u_ic_sum = max(self.u_sum_action1, 0)
        self.num_of_sender_states = len(self.states_sorted)
        for i in range(len(self.states_sorted) + 1):
            self.v_sums.append(0)
            self.u_sums.append(0)
            self.m_sums.append(0)
            for j, state in enumerate(self.states_sorted):
                if j < i:
                    f = state.opt_v
                else:
                    f = 1 - state.opt_v
                self.v_sums[i] += state.v * f
                self.u_sums[i] += state.u * f
                self.m_sums[i] += state.m * f
            if i>0 and self.states_sorted[i-1].r < 0 \
                    and self.u_sums[i]<self.u_ic_sum \
                    and self.num_of_sender_states==len(self.states_sorted):
                    self.num_of_sender_states = i
        # find recommendation
        self.opt_v_omega_star = min(1,(self.u_sums[self.num_of_sender_states-1]-self.u_ic_sum)/(
                self.u_sums[self.num_of_sender_states-1]-self.u_sums[self.num_of_sender_states]))
        self.f_omega_star = self.opt_v_omega_star if self.states_sorted[self.num_of_sender_states-1].v > 0 else \
            1- self.opt_v_omega_star
        # display recommendation
        self.outputs['f(w*)'].setText(str(round(self.f_omega_star, 2)))

        # self.u_sums[self.num_of_sender_states - 1] - self.u_ic_sum)
        # I'm here - the aim is to find the alpha that that zeros opt_v


    def plotButton(self):
        self.states = []
        for name in self.inputs['m'].keys():
            state = State(name=name,
                          u=self.inputs['u'][name].value(),
                          v=self.inputs['v'][name].value(),
                          m=self.inputs['m'][name].value(),
                          p=1)
            self.states.append(state)
        for state in self.states:
            self.outputs['r'][state.name].setText(str(state.r))
        self.findRecommendation()
        self.plot()



    def plot(self):
        # random data
        # data = [random.random() for i in range(10)]

        # r = tuple(state.r for state in self.states_sorted)


        # x = [state.v for state in self.states]
        # y = [state.u for state in self.states]

        # create an axis
        ax = self.figure.add_subplot(121)


        # add a 'state' by dividing the non deterministic state to two at f(w)
        r = self.u_sums[self.num_of_sender_states] - self.u_sums[self.num_of_sender_states - 1] \
            / self.v_sums[self.num_of_sender_states] - self.v_sums[self.num_of_sender_states - 1]
        if self.u_sum_action1 >= 0:
            u = self.u_sum_action1 - self.u_sums[self.num_of_sender_states - 1]
            print(self.u_sums)
            pprint(self.v_sums)
            print('self.u_sums[self.num_of_sender_states]', self.u_sums[self.num_of_sender_states])
            print('self.u_sums[self.num_of_sender_states-1]', self.u_sums[self.num_of_sender_states - 1])
            print('self.v_sums[self.num_of_sender_states]', self.v_sums[self.num_of_sender_states])
            print('self.v_sums[self.num_of_sender_states-1]', self.v_sums[self.num_of_sender_states - 1])
        else:
            u = -self.u_sums[self.num_of_sender_states - 1]
        v = u/r
        print('v',v)
        print(u)

        self.v_sums.insert(self.num_of_sender_states, self.v_sums[self.num_of_sender_states - 1]+v)
        self.u_sums.insert(self.num_of_sender_states, self.u_sums[self.num_of_sender_states - 1]+u)
        self.m_sums.insert(self.num_of_sender_states, 800)


        # discards the old graph
        ax.clear()

        # plot data
        ax.plot(self.v_sums, self.m_sums, '*-', markevery=[self.num_of_sender_states-1,self.num_of_sender_states])
        style_action1 = '-' if self.u_sum_action1 >= 0 else '--'
        style_action2 = '-' if self.u_sum_action1 <= 0 else '--'
        # ax.vlines(x=self.v_sum_action1, ymin=min(self.m_sums), ymax=max(self.m_sums), linestyles=style_action1, color='green')
        # ax.hlines(y=self.u_sum_action1, xmin=min(self.v_sums), xmax=max(self.v_sums), linestyles=style_action1, color='green')
        # ax.vlines(x=0, ymin=min(self.m_sums), ymax=max(self.m_sums), linestyles=style_action2, color='red')
        # ax.hlines(y=0, xmin=min(self.v_sums), xmax=max(self.v_sums), linestyles=style_action2, color='red')
        ax.vlines(x=self.v_sums[np.argmax(self.m_sums)], ymin=min(self.m_sums), ymax=max(self.m_sums), linestyles='dotted', color='black')

        # create an axis
        ax = self.figure.add_subplot(122)

        # discards the old graph
        ax.clear()

        # plot data
        ax.plot(self.v_sums, self.u_sums, '*-', markevery=[self.num_of_sender_states - 1, self.num_of_sender_states])
        style_action1 = '-' if self.u_sum_action1 >= 0 else '--'
        style_action2 = '-' if self.u_sum_action1 <= 0 else '--'
        # ax.vlines(x=self.v_sum_action1, ymin=min(self.u_sums), ymax=max(self.u_sums), linestyles=style_action1,
        #           color='green')
        ax.hlines(y=self.u_sum_action1, xmin=min(self.v_sums), xmax=max(self.v_sums), linestyles=style_action1,
                  color='green')
        # ax.vlines(x=0, ymin=min(self.u_sums), ymax=max(self.u_sums), linestyles=style_action2, color='red')
        ax.hlines(y=0, xmin=min(self.v_sums), xmax=max(self.v_sums), linestyles=style_action2, color='red')
        ax.vlines(x=self.v_sums[np.argmax(self.m_sums)], ymin=min(self.u_sums), ymax=max(self.u_sums),
                  linestyles='dotted', color='black')

        # refresh canvas
        self.canvas.draw()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    main = Window()
    main.show()

    sys.exit(app.exec_())