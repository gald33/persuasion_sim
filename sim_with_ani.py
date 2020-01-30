from pprint import pprint
from image2gif import writeGif
from PIL import Image
import os
import logging
import numpy as np
from operator import attrgetter
import sys
from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FFMpegWriter
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
        # self.change_rep_button.clicked.connect(self.changeRepButton)  TEST!!! DELETE NEXT LINE
        self.change_rep_button.clicked.connect(self.animateButton)
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
                        value = round(random.uniform(-20,20),2)
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

    def animateButton(self):
        print('animate btn')
        self.ani_fig = plt.figure()
        self.plot(animation=True)
        ani = animation.FuncAnimation(self.ani_fig, self.animate, interval=10, save_count=50)
        self.ani_fig.show()
        # ani.save('ani_test' + '.gif', writer='imagemagick')
        # Set up formatting for the movie files
        # Writer = animation.writers['ffmpeg']
        # writer = FFMpegWriter(fps=15, metadata=dict(artist='Me'), bitrate=1800)
        # ani.save('im.mp4')
        file_names = sorted(
            (fn for fn in os.listdir('/home/dev/persuasion_sim/images') if fn.endswith('.png')))
        images = [Image.open(fn) for fn in file_names]
        print('done')


    def animate(self, i):
        print('calculation loop')
        # alpha = self.outputs['alpha'].value()
        alpha = 0.05
        for j, state in enumerate(self.states_sorted):
            if j != self.num_of_sender_states:
                state.update_u(state.u * (1-alpha) +
                               self.states_sorted[self.num_of_sender_states-1].u * alpha)
                self.inputs['u'][state.name].setValue(state.u)
        self.readInputs()
        self.findRecommendation()



    def FindAlphaRepButton(self):
        # print 'test'
        pass


    def changeRepButton(self):
        for i, state in enumerate(self.states_sorted):
            if i != self.num_of_sender_states:
                state.update_u(state.u * (1-self.outputs['alpha'].value()) +
                               self.states_sorted[self.num_of_sender_states-1].u * self.outputs['alpha'].value())
                self.inputs['u'][state.name].setValue(state.u)
        self.readInputs()
        self.findRecommendation()
        self.plot()


    def randomizeButton(self):
        self.randomizeInputs()
        self.readInputs()
        self.findRecommendation()
        self.plot()


    def randomizeInputs(self):
        for player in self.inputs.keys():
            if player != 'u':
                for state_name in self.inputs[player].keys():
                    value = 0
                    while value == 0:
                        value = round(random.uniform(-20, 20), 2)
                    self.inputs[player][state_name].setValue(value)
            for state_name in self.inputs['u'].keys():
                    self.inputs['u'][state_name].setValue(self.inputs['m'][state_name].value())


    def findRecommendation(self):
        # sort states by r
        #actually the sorting needs to happen every time and not just on the first run...
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
        self.readInputs()
        self.findRecommendation()
        self.plot()


    def readInputs(self):
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




    def plot(self, animation=False):
        # random data
        # data = [random.random() for i in range(10)]

        # r = tuple(state.r for state in self.states_sorted)


        # x = [state.v for state in self.states]
        # y = [state.u for state in self.states]

        # create an axis
        # if animation:
        #     print('one frame done')
        #     ax = self.ani_fig
        #     ax.add_subplot(111)
        # else:
        ax = self.figure.add_subplot(111)
        # ax = self.figure
        pprint(ax)
        pprint(self.figure)
        pprint(plt.Figure())

        # discards the old graph
        ax.clear()
        # plot dataa
        ax.plot(self.v_sums, self.u_sums, '*-', markevery=[self.num_of_sender_states-1,self.num_of_sender_states])
        style_action1 = '-' if self.u_sum_action1 >= 0 else '--'
        style_action2 = '-' if self.u_sum_action1 <= 0 else '--'
        ax.vlines(x=self.v_sum_action1, ymin=min(self.u_sums), ymax=max(self.u_sums), linestyles=style_action1, color='green')
        ax.hlines(y=self.u_sum_action1, xmin=min(self.v_sums), xmax=max(self.v_sums), linestyles=style_action1, color='green')
        ax.vlines(x=0, ymin=min(self.u_sums), ymax=max(self.u_sums), linestyles=style_action2, color='red')
        ax.hlines(y=0, xmin=min(self.v_sums), xmax=max(self.v_sums), linestyles=style_action2, color='red')
        ax.vlines(x=self.v_sums[np.argmax(self.m_sums)], ymin=min(self.u_sums), ymax=max(self.u_sums), linestyles='dotted', color='black')

        # refresh canvas
        self.canvas.draw()
        # pprint(ax)
        self.figure.savefig('blabla.png')


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    main = Window()
    main.show()

    sys.exit(app.exec_())